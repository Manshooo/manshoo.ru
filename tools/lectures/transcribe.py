#!/usr/bin/env python3
"""Видео лекции → черновик .md для раздела /lectures (docs/09-lectures.md).

Что делает:
  1. скачивает видео по ссылке (yt-dlp: ВК, YouTube, RuTube…) или берёт локальный файл;
  2. распознаёт речь (faster-whisper) → segments.json и transcript.srt;
  3. вытаскивает кадры при смене сцены (новый слайд, исписанная доска) → frames/;
  4. собирает draft.md: шапка с пустыми обязательными полями + абзацы с таймкодами
     + метки кадров там, где на экране что-то поменялось.

draft.md — сырьё, а не публикация: api его не примет, пока не заполнены date,
summary и (для транскрипции) permission. Дальше черновик редактирует скилл
lecture-notes (tools/lectures/SKILL_PROMPT.md) или человек.

Кадры остаются в рабочей папке и на сайт не загружаются: слайды — тоже
произведение лектора. Они нужны, чтобы описать их словами в блоках [На слайде].

Примеры:
  python transcribe.py https://vk.com/video-123_456 --slug 03-gruppy
  python transcribe.py lecture.mp4 --model large-v3 --device cuda
  python transcribe.py lecture.mp4 --segments work/03-gruppy/segments.json  # без повторного ASR
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Frame:
    file: str
    t: float


# --- утилиты ------------------------------------------------------------------


def need(tool: str, hint: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"Не найден {tool}: {hint}")
    return path


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, check=True, text=True, encoding="utf-8", errors="replace", **kwargs
    )


def timecode(seconds: float, srt: bool = False) -> str:
    total_ms = round(seconds * 1000)
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}" if srt else f"{h:02}:{m:02}:{s:02}"


def duration_label(seconds: float) -> str:
    h, rest = divmod(round(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def slugify(text: str) -> str:
    table = str.maketrans(
        {
            **dict(zip("абвгдезийклмнопрстуфхцыэ", "abvgdeziyklmnoprstufhcye", strict=True)),
            "ё": "e", "ж": "zh", "ч": "ch", "ш": "sh", "щ": "sch", "ю": "yu", "я": "ya",
            "ъ": "", "ь": "",
        }
    )  # fmt: skip
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().translate(table)).strip("-")
    return slug or "lecture"


# --- шаги ---------------------------------------------------------------------


def download(url: str, workdir: Path) -> Path:
    need("yt-dlp", "pip install yt-dlp (или скачайте видео вручную и передайте файл)")
    # 720p хватает, чтобы читать слайды, и вдвое легче 1080p
    run(
        [
            "yt-dlp",
            "-f",
            "bv*[height<=720]+ba/b[height<=720]/b",
            "--merge-output-format",
            "mp4",
            "-o",
            str(workdir / "video.%(ext)s"),
            url,
        ]
    )
    found = sorted(workdir.glob("video.*"))
    if not found:
        sys.exit("yt-dlp ничего не скачал")
    return found[0]


def probe_duration(video: Path) -> float:
    need("ffprobe", "поставьте FFmpeg: https://ffmpeg.org/download.html")
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
    ).stdout.strip()
    return float(out or 0)


def extract_audio(video: Path, workdir: Path) -> Path:
    need("ffmpeg", "поставьте FFmpeg: https://ffmpeg.org/download.html")
    wav = workdir / "audio.wav"
    # 16 кГц моно, 16 бит — формат, на котором обучен Whisper
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
    ]
    run([*cmd, "-c:a", "pcm_s16le", str(wav)])
    return wav


def load_wav(wav: Path):
    """WAV → float32-массив. Сами, а не через faster-whisper: его decode_audio
    зовёт PyAV, а свежие версии PyAV ломают совместимость (TypeError на av.open)."""
    import wave

    import numpy as np

    with wave.open(str(wav), "rb") as f:
        frames = f.readframes(f.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def add_cuda_dlls() -> None:
    """Подключить cuBLAS/cuDNN из pip-пакетов nvidia-*-cu12 (Windows).

    pip кладёт DLL в site-packages/nvidia/<lib>/bin, а ctranslate2 ищет их только
    в PATH — без этого GPU «не находит» cublas64_12.dll, хотя пакет стоит."""
    if sys.platform != "win32":
        return
    import importlib.util
    import os

    spec = importlib.util.find_spec("nvidia")
    if not spec or not spec.submodule_search_locations:
        return
    dirs = [
        str(b)
        for root in spec.submodule_search_locations
        for b in Path(root).glob("*/bin")
        if b.is_dir()
    ]
    for d in dirs:
        os.add_dll_directory(d)
    os.environ["PATH"] = os.pathsep.join([*dirs, os.environ.get("PATH", "")])


def transcribe(wav: Path, model_name: str, language: str, device: str) -> list[Segment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Нет faster-whisper: pip install -r tools/lectures/requirements.txt")

    compute = "float16" if device == "cuda" else "int8"
    print(f"Загружаю модель {model_name} ({device}, {compute})…", file=sys.stderr)
    model = WhisperModel(model_name, device=device, compute_type=compute)
    segments, _info = model.transcribe(
        load_wav(wav),
        language=language,
        vad_filter=True,  # режет паузы и снижает «галлюцинации» Whisper на тишине
        beam_size=5,
        # без контекста предыдущего куска модель реже зацикливается на длинных записях
        condition_on_previous_text=False,
    )
    result = []
    for s in segments:
        text = s.text.strip()
        if text:
            result.append(Segment(round(s.start, 2), round(s.end, 2), text))
            print(f"[{timecode(s.start)}] {text}", file=sys.stderr)
    return result


def extract_frames(
    video: Path, workdir: Path, threshold: float, min_gap: float
) -> list[Frame]:
    """Кадр на каждую смену сцены; первый кадр — всегда (титульный слайд)."""
    frames_dir = workdir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    proc = run(
        [
            "ffmpeg",
            "-v",
            "info",
            "-i",
            str(video),
            "-vf",
            f"select='eq(n\\,0)+gt(scene\\,{threshold})',showinfo",
            "-fps_mode",
            "vfr",
            "-q:v",
            "3",
            str(frames_dir / "%04d.jpg"),
        ],
        capture_output=True,
    )
    times = [float(t) for t in re.findall(r"pts_time:\s*([\d.]+)", proc.stderr)]
    files = sorted(frames_dir.glob("*.jpg"))

    kept: list[Frame] = []
    for file, t in zip(files, times, strict=False):
        # лектор листает слайды туда-сюда или машет рукой — частые кадры выкидываем
        if kept and t - kept[-1].t < min_gap:
            file.unlink()
            continue
        kept.append(Frame(f"frames/{file.name}", round(t, 2)))
    return kept


# --- сборка черновика ---------------------------------------------------------


def paragraphs(
    segments: list[Segment], frames: list[Frame], pause: float, max_len: float
):
    """Склеивает сегменты в абзацы: разрыв на паузе, по длине и там, где сменился кадр."""
    frame_times = [f.t for f in frames]
    block: list[Segment] = []
    fi = 0
    for seg in segments:
        while fi < len(frames) and frame_times[fi] <= seg.start:
            if block:
                yield "text", block
                block = []
            yield "frame", frames[fi]
            fi += 1
        if block and (
            seg.start - block[-1].end > pause or seg.end - block[0].start > max_len
        ):
            yield "text", block
            block = []
        block.append(seg)
    if block:
        yield "text", block
    for frame in frames[fi:]:
        yield "frame", frame


def join_segments(texts: list[str]) -> str:
    """Whisper часто не ставит точку в конце сегмента: «…группы Группой называется…».
    Если следующий сегмент начинается с заглавной, а предыдущий не закончен знаком, ставим точку."""
    out = ""
    for text in texts:
        if out and text[:1].isupper() and out[-1] not in ".?!…:;":
            out += "."
        out = f"{out} {text}" if out else text
    return out


def yaml_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_draft(
    *,
    title: str,
    kind: str,
    language: str,
    source_url: str,
    duration: float,
    segments: list[Segment],
    frames: list[Frame],
    pause: float,
    max_len: float,
) -> str:
    head = [
        "---",
        "# ЧЕРНОВИК из tools/lectures/transcribe.py. Поля с пустыми значениями обязательны,",
        "# без них api файл не примет. Схема полей — docs/09-lectures.md.",
        f"title: {yaml_str(title)}",
        "number:",
        f"kind: {kind} # transcript — текст лектора; notes — свой конспект по мотивам",
        "date: # ГГГГ-ММ-ДД, когда читалась лекция",
        f"language: {language}",
        "permission: # для transcript: где и как получено согласие автора",
        "quality: asr # после редактуры — edited, после сверки с видео — verified",
    ]
    if source_url:
        head += [
            "source:",
            f"  url: {source_url}",
            f"  duration: '{duration_label(duration)}'",
        ]
    head += ["topics: []", "summary: # 1–2 предложения: о чём лекция", "---", ""]

    body = [
        "<!-- Сырое распознавание: абзацы нарезаны по паузам, таймкоды — начало абзаца.",
        "     Метки [Кадр] — смена картинки в видео: открыть файл и описать словами,",
        "     что на слайде или доске, либо удалить метку, если там ничего важного. -->",
        "",
    ]
    for kind_, item in paragraphs(segments, frames, pause, max_len):
        if kind_ == "frame":
            body += [
                f"> **[Кадр {timecode(item.t)}]** ({item.file}): описать или удалить",
                "",
            ]
        else:
            text = join_segments([s.text for s in item])
            body += [f"[{timecode(item[0].start)}] {text}", ""]
    return "\n".join(head + body)


def build_srt(segments: list[Segment]) -> str:
    blocks = [
        f"{i}\n{timecode(s.start, srt=True)} --> {timecode(s.end, srt=True)}\n{s.text}\n"
        for i, s in enumerate(segments, 1)
    ]
    return "\n".join(blocks)


# --- точка входа --------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Видео лекции → черновик .md с таймкодами и кадрами слайдов.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Примеры:", 1)[1] if __doc__ else None,
    )
    p.add_argument("input", help="ссылка на видео или путь к файлу")
    p.add_argument(
        "--slug", help="имя будущего .md (03-gruppy); по умолчанию из названия"
    )
    p.add_argument("--title", help="название лекции; по умолчанию имя файла")
    p.add_argument("--kind", choices=["transcript", "notes"], default="transcript")
    p.add_argument(
        "--source-url", help="ссылка на оригинал, если input — локальный файл"
    )
    p.add_argument(
        "--out",
        type=Path,
        help="рабочая папка; по умолчанию tools/lectures/work/<slug>",
    )
    p.add_argument("--lang", default="ru", help="язык речи (ru)")
    p.add_argument(
        "--model",
        default="large-v3-turbo",
        help="модель Whisper: tiny для проверки, large-v3-turbo — баланс, large-v3 — точнее",
    )
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument(
        "--segments", type=Path, help="готовый segments.json: пропустить распознавание"
    )
    p.add_argument("--no-frames", action="store_true", help="не вытаскивать кадры")
    p.add_argument(
        "--scene", type=float, default=0.3, help="порог смены сцены 0–1 (0.3)"
    )
    p.add_argument(
        "--min-gap", type=float, default=20, help="минимум секунд между кадрами (20)"
    )
    p.add_argument(
        "--pause", type=float, default=2.0, help="пауза, рвущая абзац, сек (2)"
    )
    p.add_argument(
        "--max-paragraph", type=float, default=90, help="макс. длина абзаца, сек (90)"
    )
    args = p.parse_args()

    is_url = re.match(r"^https?://", args.input) is not None
    title = args.title or (Path(args.input).stem if not is_url else "Лекция")
    slug = args.slug or slugify(title)
    workdir = (args.out or HERE / "work" / slug).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    video = download(args.input, workdir) if is_url else Path(args.input).resolve()
    if not video.exists():
        sys.exit(f"Нет файла {video}")
    source_url = args.source_url or (args.input if is_url else "")
    duration = probe_duration(video)

    if args.segments:
        segments = [Segment(**s) for s in json.loads(args.segments.read_text("utf-8"))]
    else:
        add_cuda_dlls()
        device = args.device
        if device == "auto":
            try:
                import ctranslate2

                device = "cuda" if ctranslate2.get_cuda_device_count() else "cpu"
            except ImportError:
                device = "cpu"
        wav = extract_audio(video, workdir)
        try:
            segments = transcribe(wav, args.model, args.lang, device)
        except RuntimeError as exc:
            # Видеокарта есть, а CUDA-библиотек нет — частый случай на Windows.
            # Явно попросили cuda — падаем; в режиме auto — считаем на CPU.
            if device != "cuda" or args.device == "cuda":
                raise
            print(
                f"\nGPU не завёлся ({exc}).\nСчитаю на CPU. Для GPU: "
                'pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"\n',
                file=sys.stderr,
            )
            segments = transcribe(wav, args.model, args.lang, "cpu")
        wav.unlink(missing_ok=True)
    (workdir / "segments.json").write_text(
        json.dumps([asdict(s) for s in segments], ensure_ascii=False, indent=1), "utf-8"
    )
    (workdir / "transcript.srt").write_text(build_srt(segments), "utf-8")

    frames = (
        []
        if args.no_frames
        else extract_frames(video, workdir, args.scene, args.min_gap)
    )
    (workdir / "frames.json").write_text(
        json.dumps([asdict(f) for f in frames], ensure_ascii=False, indent=1), "utf-8"
    )

    draft = build_draft(
        title=title,
        kind=args.kind,
        language=args.lang,
        source_url=source_url,
        duration=duration,
        segments=segments,
        frames=frames,
        pause=args.pause,
        max_len=args.max_paragraph,
    )
    (workdir / f"{slug}.draft.md").write_text(draft, "utf-8")

    print(f"\nГотово: {workdir}", file=sys.stderr)
    print(
        f"  {slug}.draft.md — черновик ({len(segments)} сегментов, {len(frames)} кадров)"
    )
    print("  transcript.srt — субтитры, можно загрузить в ВК/YouTube к видео")
    print("  segments.json, frames.json, frames/ — сырьё для редактуры")


if __name__ == "__main__":
    main()
