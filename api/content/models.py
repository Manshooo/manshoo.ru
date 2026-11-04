from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Profile(models.Model):
    """Singleton (pk=1): блок «обо мне» на главной."""

    name = models.CharField("имя", max_length=120)
    headline = models.CharField("кто я одной строкой", max_length=200)
    bio_md = models.TextField("о себе (Markdown)", blank=True)
    photo = models.ImageField("фото", upload_to="profile/", blank=True, null=True)
    location = models.CharField("город / часовой пояс", max_length=120, blank=True)
    skills = models.JSONField("навыки (список строк)", default=list, blank=True)
    socials = models.JSONField("контакты {github, telegram, email…}", default=dict, blank=True)
    meta_description = models.CharField("SEO-описание главной", max_length=160, blank=True)

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профиль"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "Profile":
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name": "…", "headline": "…"})
        return obj


class Project(models.Model):
    """Проект портфолио. Заменяет «опыт работы» в резюме — поэтому есть
    и резюмные поля (роль, организация, период), и витринные (фишки, обложка)."""

    class Type(models.TextChoices):
        WORK = "work", "работа"
        PET = "pet", "пет-проект"
        OSS = "oss", "open source"
        FREELANCE = "freelance", "фриланс"

    class Status(models.TextChoices):
        ACTIVE = "active", "живой"
        WIP = "wip", "в разработке"
        ARCHIVED = "archived", "архив"

    slug = models.SlugField("slug (URL)", unique=True)
    title = models.CharField("название", max_length=120)
    tagline = models.CharField("одной строкой", max_length=200)
    description_md = models.TextField("описание (Markdown)", blank=True)
    role = models.CharField("роль", max_length=120, blank=True)
    org = models.CharField("компания / контекст", max_length=120, blank=True)
    project_type = models.CharField("тип", max_length=20, choices=Type.choices, default=Type.PET)
    period_start = models.DateField("начало")
    period_end = models.DateField("конец (пусто = по настоящее время)", null=True, blank=True)
    stack = models.JSONField("стек (список строк)", default=list, blank=True)
    highlights = models.JSONField("ключевые фишки (список строк)", default=list, blank=True)
    links = models.JSONField("ссылки {live, repo, case}", default=dict, blank=True)
    cover = models.ImageField("обложка", upload_to="covers/", blank=True, null=True)
    status = models.CharField(
        "статус", max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    is_published = models.BooleanField("опубликован", default=False)
    is_featured = models.BooleanField("закреплён вверху", default=False)
    sort_order = models.IntegerField("порядок", default=0)
    uptime_monitor_slug = models.CharField(
        "slug монитора uptime",
        max_length=50,
        blank=True,
        help_text="Связь с uptime-чекером для живого статус-бейджа (Phase 4)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "проект"
        verbose_name_plural = "проекты"
        ordering = ["-is_featured", "sort_order", "-period_start"]
        indexes = [models.Index(fields=["is_published", "sort_order"])]

    def __str__(self) -> str:
        return self.title


class ProjectImage(models.Model):
    """Кадр галереи проекта: скриншот, фото, схема. Хранится в двух размерах —
    превью для сетки на странице и полный кадр для просмотра по клику."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="images", verbose_name="проект"
    )
    image = models.ImageField(
        "изображение", upload_to="gallery/", width_field="width", height_field="height"
    )
    thumb = models.ImageField("превью", upload_to="gallery/thumbs/")
    width = models.PositiveIntegerField("ширина", default=0, editable=False)
    height = models.PositiveIntegerField("высота", default=0, editable=False)
    caption = models.CharField("подпись", max_length=200, blank=True)
    sort_order = models.IntegerField("порядок", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "кадр галереи"
        verbose_name_plural = "галерея"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.caption or self.image.name


# Файлы убираем сигналом, а не в эндпоинтах: post_delete срабатывает и при
# каскадном удалении проекта, так что загрузки не остаются мусором в media.
@receiver(post_delete, sender=Project)
def delete_cover_file(sender, instance: Project, **kwargs) -> None:
    instance.cover.delete(save=False)


@receiver(post_delete, sender=ProjectImage)
def delete_gallery_files(sender, instance: ProjectImage, **kwargs) -> None:
    instance.image.delete(save=False)
    instance.thumb.delete(save=False)


class Course(models.Model):
    """Курс лекций. Лектор, язык и лицензия курса — значения по умолчанию
    для его лекций (в файле лекции их можно не повторять)."""

    class License(models.TextChoices):
        CC_BY = "CC-BY-4.0", "CC BY 4.0"
        CC_BY_SA = "CC-BY-SA-4.0", "CC BY-SA 4.0"
        CC_BY_NC = "CC-BY-NC-4.0", "CC BY-NC 4.0"
        CC0 = "CC0-1.0", "CC0 1.0"

    slug = models.SlugField("slug (URL)", unique=True)
    title = models.CharField("название", max_length=200)
    description = models.CharField("одной строкой", max_length=300)
    body_md = models.TextField("о курсе (Markdown)", blank=True)
    lecturer = models.CharField("лектор", max_length=200)
    institution = models.CharField("вуз / площадка", max_length=200, blank=True)
    year = models.CharField("год", max_length=20, blank=True)
    language = models.CharField("язык", max_length=10, default="ru")
    license = models.CharField(
        "лицензия", max_length=20, choices=License.choices, default=License.CC_BY
    )
    is_published = models.BooleanField("опубликован", default=False)
    sort_order = models.IntegerField("порядок", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"
        ordering = ["sort_order", "title"]

    def __str__(self) -> str:
        return self.title


class Lecture(models.Model):
    """Транскрипция или конспект одной лекции — загруженный .md-файл.

    raw хранит файл как есть (его отдаёт /lectures/…/<slug>.md), остальные
    поля — разобранная шапка (content/lectures.py) для списков и разметки.
    """

    class Kind(models.TextChoices):
        TRANSCRIPT = "transcript", "транскрипция"
        NOTES = "notes", "конспект"

    class Quality(models.TextChoices):
        ASR = "asr", "распознано автоматически"
        EDITED = "edited", "отредактировано"
        VERIFIED = "verified", "сверено с видео"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lectures", verbose_name="курс"
    )
    slug = models.SlugField("slug (имя файла)")
    title = models.CharField("название", max_length=300)
    number = models.PositiveIntegerField("номер", null=True, blank=True)
    kind = models.CharField("вид", max_length=20, choices=Kind.choices)
    lecturer = models.CharField("лектор (пусто — как у курса)", max_length=200, blank=True)
    author = models.CharField("составитель", max_length=200, blank=True)
    date = models.DateField("дата лекции")
    updated = models.DateField("правка текста", null=True, blank=True)
    language = models.CharField("язык (пусто — как у курса)", max_length=10, blank=True)
    license = models.CharField(
        "лицензия (пусто — как у курса)", max_length=20, choices=Course.License.choices, blank=True
    )
    permission = models.TextField("разрешение автора", blank=True)
    quality = models.CharField("качество текста", max_length=20, choices=Quality.choices)
    source_url = models.URLField("видео", max_length=500, blank=True)
    source_title = models.CharField("название видео", max_length=300, blank=True)
    source_duration = models.CharField("длительность", max_length=20, blank=True)
    topics = models.JSONField("темы (список строк)", default=list, blank=True)
    summary = models.TextField("кратко")
    body_md = models.TextField("текст (Markdown)")
    raw = models.TextField("исходный файл")
    is_published = models.BooleanField("опубликована", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "лекция"
        verbose_name_plural = "лекции"
        ordering = [models.F("number").asc(nulls_last=True), "date", "slug"]
        constraints = [
            models.UniqueConstraint(fields=["course", "slug"], name="lecture_unique_slug")
        ]

    def __str__(self) -> str:
        return self.title

    # Пустые поля наследуются от курса: поменял лицензию курса — поменялась у всех лекций.
    @property
    def effective_lecturer(self) -> str:
        return self.lecturer or self.course.lecturer

    @property
    def effective_author(self) -> str:
        return self.author or self.effective_lecturer

    @property
    def effective_language(self) -> str:
        return self.language or self.course.language

    @property
    def effective_license(self) -> str:
        return self.license or self.course.license

    @property
    def effective_updated(self):
        return self.updated or self.date
