"""Стартовый контент: профиль и два проекта.

manshoo-ru — опубликованный честный кейс (этот сайт сам себе портфолио);
azzb-ru — черновик, владелец заполнит через админку.
"""

from datetime import date

from django.db import migrations


def seed(apps, schema_editor):
    Profile = apps.get_model("content", "Profile")
    Project = apps.get_model("content", "Project")

    if not Profile.objects.exists():
        Profile.objects.create(
            pk=1,
            name="Yanislav Pichugin",
            headline="Разработчик. Строю свои проекты и учусь на них.",
            bio_md=(
                "Привет! Я делаю личные проекты, чтобы разбираться в технологиях "
                "на практике: фронтенд, бэкенд, инфраструктура. "
                "Этот сайт — один из них: портфолио вместо раздела «опыт работы»."
            ),
            skills=["Python", "Django", "TypeScript", "Svelte", "Go", "PostgreSQL", "Docker"],
            socials={"github": "https://github.com/Manshooo"},
            meta_description=(
                "Личный сайт и портфолио Yanislav Pichugin: проекты, стек, контакты."
            ),
        )

    if not Project.objects.filter(slug="manshoo-ru").exists():
        Project.objects.create(
            slug="manshoo-ru",
            title="manshoo.ru",
            tagline="Этот сайт: портфолио из трёх сервисов с собственным мониторингом",
            description_md=(
                "Личный сайт-портфолио и одновременно полигон технологий.\n\n"
                "Три сервиса в Docker: фронтенд на SvelteKit (SSR ради SEO), "
                "API на Django + Ninja с PostgreSQL и собственный uptime-чекер на Go, "
                "который мониторит мои проекты и шлёт алерты в Telegram.\n\n"
                "Инфраструктура: nginx, CI/CD в GitHub Actions с self-hosted runner "
                "на VPS, образы в ghcr. Вся проектная документация и ADR — в репозитории."
            ),
            role="Автор и единственный разработчик",
            org="пет-проект",
            project_type="pet",
            period_start=date(2026, 7, 1),
            period_end=None,
            stack=[
                "SvelteKit",
                "TypeScript",
                "Django",
                "PostgreSQL",
                "Go",
                "SQLite",
                "Docker",
                "nginx",
                "GitHub Actions",
            ],
            highlights=[
                "Uptime-чекер написан с нуля на Go: state machine, SQLite, Telegram-алерты",
                "SSR-фронтенд на Svelte 5 — контент индексируется без JS",
                "CI/CD: паспорт каждого сервиса — свой workflow, деплой через self-hosted runner",
                "Прод-образ Go-сервиса — distroless, 22 МБ",
                "Решения зафиксированы в ADR — с альтернативами и трейд-оффами",
            ],
            links={
                "live": "https://manshoo.ru",
                "repo": "https://github.com/Manshooo/manshoo.ru",
            },
            status="wip",
            is_published=True,
            is_featured=True,
            uptime_monitor_slug="manshoo",
        )

    if not Project.objects.filter(slug="azzb-ru").exists():
        Project.objects.create(
            slug="azzb-ru",
            title="azzb.ru",
            tagline="Живой проект на Django",
            description_md="Черновик: заполнить описание, роль и фишки через админку.",
            role="Автор",
            org="пет-проект",
            project_type="pet",
            period_start=date(2026, 5, 1),
            period_end=None,
            stack=["Python", "Django", "nginx", "uWSGI"],
            highlights=[],
            links={"live": "https://azzb.ru"},
            status="active",
            is_published=False,  # черновик до заполнения
            uptime_monitor_slug="azzb",
        )


def unseed(apps, schema_editor):
    Profile = apps.get_model("content", "Profile")
    Project = apps.get_model("content", "Project")
    Project.objects.filter(slug__in=["manshoo-ru", "azzb-ru"]).delete()
    Profile.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [("content", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
