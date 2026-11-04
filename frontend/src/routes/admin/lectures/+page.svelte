<script lang="ts">
	import { api, ApiError } from '$lib/admin/client';
	import { formatDate, kindLabels, qualityLabels } from '$lib/format';
	import type { Course, LectureCard } from '$lib/types';

	let courses = $state<Course[]>([]);
	let error = $state('');
	let loading = $state(true);

	interface UploadReport {
		file: string;
		ok: boolean;
		message: string;
	}
	// отчёт о последней загрузке — по курсу
	let reports = $state<Record<number, UploadReport[]>>({});
	let busy = $state<Record<number, boolean>>({});
	let dragOver = $state<number | null>(null);

	const fail = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback);

	async function reload() {
		try {
			courses = await api.listCourses();
		} catch (e) {
			error = fail(e, 'Не удалось загрузить');
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		reload();
	});

	async function upload(course: Course, files: FileList | File[]) {
		const list = [...files];
		if (!list.length) return;
		busy[course.id] = true;
		const report: UploadReport[] = [];
		// по одному: у каждого файла свой ответ и свой список ошибок
		for (const file of list) {
			try {
				const { created, lecture } = await api.uploadLecture(course.id, file);
				report.push({
					file: file.name,
					ok: true,
					message: `${created ? 'добавлена' : 'заменена'}: ${lecture.title}${lecture.is_published ? '' : ' (черновик)'}`
				});
			} catch (e) {
				report.push({ file: file.name, ok: false, message: fail(e, 'не удалось загрузить') });
			}
		}
		reports[course.id] = report;
		busy[course.id] = false;
		await reload();
	}

	function onPick(course: Course, event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files) upload(course, input.files).finally(() => (input.value = ''));
	}

	function onDrop(course: Course, event: DragEvent) {
		event.preventDefault();
		dragOver = null;
		if (event.dataTransfer?.files) upload(course, event.dataTransfer.files);
	}

	async function togglePublished(lecture: LectureCard) {
		try {
			await api.setLecturePublished(lecture.id, !lecture.is_published);
			await reload();
		} catch (e) {
			error = fail(e, 'Не удалось сохранить');
		}
	}

	async function remove(lecture: LectureCard) {
		if (!confirm(`Удалить «${lecture.title}»? Отменить будет нельзя.`)) return;
		try {
			await api.deleteLecture(lecture.id);
			await reload();
		} catch (e) {
			error = fail(e, 'Не удалось удалить');
		}
	}

	const viewHref = (course: Course, lecture: LectureCard) =>
		`/lectures/${course.slug}/${lecture.slug}${lecture.is_published && course.is_published ? '' : '?preview=1'}`;
</script>

<header class="head">
	<h1>Лекции</h1>
	<a class="button" href="/admin/lectures/new">Добавить курс</a>
</header>

<p class="hint">
	Лекция — это .md-файл с YAML-шапкой (схема и пример — <code>docs/09-lectures.md</code>,
	<code>tools/lectures/example-lecture.md</code>). Имя файла становится адресом:
	<code>03-gruppy.md</code> → <code>/lectures/курс/03-gruppy</code>. Файл с тем же именем заменяет
	лекцию. Новые лекции загружаются черновиками.
</p>

{#if error}
	<p class="error">{error}</p>
{/if}

{#if loading}
	<p class="muted">Загружаем…</p>
{:else if courses.length === 0}
	<p class="muted">Курсов пока нет. Начните с «Добавить курс», затем загрузите в него лекции.</p>
{:else}
	{#each courses as course (course.id)}
		<section
			id={`course-${course.id}`}
			class="course"
			class:drag={dragOver === course.id}
			ondragover={(e) => {
				e.preventDefault();
				dragOver = course.id;
			}}
			ondragleave={() => (dragOver = null)}
			ondrop={(e) => onDrop(course, e)}
			aria-label={course.title}
		>
			<div class="course-head">
				<div>
					<h2>{course.title}</h2>
					<p class="meta">
						{course.lecturer} · {course.license.name} · /lectures/{course.slug}
					</p>
				</div>
				<span class="badge" class:published={course.is_published}>
					{course.is_published ? 'опубликован' : 'черновик'}
				</span>
				<a href={`/admin/lectures/${course.id}`}>Изменить</a>
			</div>

			{#if course.lectures.length}
				<ul class="list">
					{#each course.lectures as lecture (lecture.id)}
						<li>
							<div class="main">
								<span class="title">{lecture.title}</span>
								<span class="meta">
									{lecture.slug}.md · {kindLabels[lecture.kind]} · {formatDate(lecture.date)}
								</span>
							</div>
							<div class="actions">
								<span class="badge" class:published={lecture.is_published}>
									{lecture.is_published ? 'опубликована' : 'черновик'}
								</span>
								<button type="button" onclick={() => togglePublished(lecture)}>
									{lecture.is_published ? 'Снять' : 'Опубликовать'}
								</button>
								<a href={viewHref(course, lecture)} target="_blank" rel="noopener">Смотреть ↗</a>
								<button type="button" class="danger" onclick={() => remove(lecture)}>
									Удалить
								</button>
							</div>
						</li>
					{/each}
				</ul>
			{/if}

			<label class="upload">
				<input
					type="file"
					accept=".md,text/markdown"
					multiple
					disabled={busy[course.id]}
					onchange={(e) => onPick(course, e)}
				/>
				{busy[course.id] ? 'Загружаем…' : 'Загрузить .md (можно несколько или перетащить сюда)'}
			</label>

			{#if reports[course.id]}
				<ul class="report">
					{#each reports[course.id] as r (r.file)}
						<li class:ok={r.ok}>
							<strong>{r.file}</strong>: {r.message}
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	{/each}
{/if}

<p class="hint">
	Качество текста: {Object.values(qualityLabels).join(' → ')}. Транскрипцию без поля
	<code>permission</code> (разрешение лектора) api не примет.
</p>

<style>
	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	h1 {
		margin: 0;
		font-size: 1.5rem;
	}
	.button {
		border: 1px solid var(--accent);
		background: var(--accent);
		color: #fff;
		border-radius: 6px;
		padding: 0.35rem 0.9rem;
	}
	.button:hover {
		text-decoration: none;
		opacity: 0.9;
	}
	.hint {
		color: var(--muted);
		font-size: 0.85rem;
	}
	.course {
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1rem 1.25rem;
		margin-top: 1.5rem;
	}
	.course.drag {
		border-color: var(--accent);
		border-style: dashed;
	}
	.course-head {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	.course-head > div {
		flex: 1;
	}
	h2 {
		margin: 0;
		font-size: 1.15rem;
	}
	.meta {
		color: var(--muted);
		font-size: 0.85rem;
		margin: 0.15rem 0 0;
	}
	.list {
		list-style: none;
		padding: 0;
		margin: 1rem 0 0;
		display: grid;
		gap: 0.5rem;
	}
	.list li {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1rem;
		align-items: center;
		justify-content: space-between;
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.6rem 0.9rem;
	}
	.main {
		display: flex;
		flex-direction: column;
		min-width: 14rem;
	}
	.title {
		font-weight: 600;
	}
	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.9rem;
	}
	.badge {
		border: 1px solid var(--border);
		border-radius: 999px;
		padding: 0.05rem 0.6rem;
		font-size: 0.78rem;
		color: var(--muted);
		white-space: nowrap;
	}
	.badge.published {
		color: #16a34a;
		border-color: color-mix(in srgb, #16a34a 40%, transparent);
	}
	button {
		font: inherit;
		font-size: 0.9rem;
		border: 1px solid var(--border);
		background: var(--bg);
		color: inherit;
		border-radius: 6px;
		padding: 0.2rem 0.7rem;
		cursor: pointer;
	}
	button:hover {
		border-color: var(--accent);
	}
	.danger {
		color: #dc2626;
	}
	.upload {
		display: block;
		margin-top: 1rem;
		border: 1px dashed var(--border);
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: var(--muted);
		font-size: 0.9rem;
		cursor: pointer;
	}
	.upload input {
		display: block;
		margin-bottom: 0.4rem;
		font: inherit;
	}
	.report {
		margin: 0.75rem 0 0;
		padding-left: 1.25rem;
		font-size: 0.88rem;
	}
	.report li {
		color: #dc2626;
		white-space: pre-line;
		margin: 0.3rem 0;
	}
	.report li.ok {
		color: #16a34a;
	}
	.muted {
		color: var(--muted);
	}
	.error {
		color: #dc2626;
	}
</style>
