from django.db import models


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
