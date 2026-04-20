# CLAUDE.md

Guidance for Claude Code working in this Django rewrite of StudyGuild.

## Stack

- Python 3.12, Django 5.1, Django REST Framework 3.15
- PostgreSQL (prod) / SQLite (dev)
- `dj-rest-auth` + `django-allauth` + SimpleJWT for auth
- `drf-spectacular` for OpenAPI
- Celery + Redis for background jobs
- `django-storages` (S3) for file uploads
- pytest + pytest-django + factory_boy for tests
- ruff for lint + format

## Shape

DRF API at `/api/*`, Django Admin at `/admin/`. Apps under `apps/` with explicit `label` in `apps.py` so `apps.users` registers as `users`.

## Domain

Mirrors Rails `../backend/`:

- `users.User` — custom AbstractUser, email login, `role` choice (student/admin), optional `institution` FK
- `institutions.Institution`
- `academics.Subject`, `academics.SubjectGroup`
- `groups.StudentGroup`, `groups.StudentGroupInvitation`
- `reunions.Reunion`, `reunions.ReunionMessage`
- `community.NewsletterEntry`, `community.IssueReport`

## Conventions

**Follow The Django Way.** Mirror Rails intent but use Django idioms:

- DRF `ModelViewSet` + `DefaultRouter` — no function-based endpoints for CRUD.
- Validation at model (`clean()`) AND serializer (`validate()`); rely on `UniqueConstraint` for DB-level guarantees.
- Business rules in models / serializer `validate_*` methods. No service-object sprawl.
- Migrations for schema — never edit DB manually.
- Signals only when no alternative (prefer `save()` override or serializer hooks).
- Keep response keys matching Rails output (see `../backend/AI_GUIDANCE.md` §4). Critical for frontend compat.

## Error contract (matches Rails)

Custom handler at `config/exceptions.py`:

- 404 → `{"error": "..."}`
- Validation → `{"errors": [...]}` status **422** (not 400)

## Commands

```bash
source .venv/bin/activate
python manage.py runserver              # :8000
python manage.py makemigrations <app>
python manage.py migrate
python manage.py shell
pytest                                  # full suite
pytest -k test_name                     # single test
ruff check . && ruff format --check .
```

## Settings split

- `config/settings/base.py` — shared
- `config/settings/dev.py` — `DJANGO_SETTINGS_MODULE=config.settings.dev` (default via `manage.py`)
- `config/settings/prod.py` — WSGI/ASGI default

## Testing

- Request specs under `tests/api/`.
- Fixtures via `factory_boy` under `tests/factories/`.
- Cover happy path + validation/error path (check 422 + `{"errors": [...]}`).
- Contract tests: diff response JSON against Rails to catch drift.

## Adding a new resource (checklist)

1. Model with `db_table`, `Meta.ordering`, constraints.
2. Migration (`makemigrations`).
3. Serializer — match Rails response keys.
4. ViewSet (`ModelViewSet`) + router registration in `config/urls.py`.
5. Admin registration.
6. Factory + request tests.

## When in doubt

Pick the idiom a seasoned Django dev would reach for first. Don't port Rails quirks literally when a Django equivalent is cleaner (e.g. HABTM → `ManyToManyField`, callbacks → serializer `validate`, Devise → allauth).

## Migration Plan

See `../backend/DJANGO_MIGRATION_PLAN.md` for full phased migration plan and current status.
