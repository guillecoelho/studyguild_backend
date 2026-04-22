# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

- Python 3.12, Django 5.1, Django REST Framework 3.15
- PostgreSQL (prod) / SQLite (dev)
- `dj-rest-auth` + `django-allauth` + SimpleJWT for auth
- `drf-spectacular` for OpenAPI
- Django Channels + Redis for WebSocket (reunions chat)
- Celery + Redis for background jobs (configured, no tasks yet)
- `django-storages` (S3) for file uploads
- pytest + pytest-django + factory_boy for tests
- ruff for lint + format

## Shape

DRF API at `/api/*`, Django Admin at `/admin/`. Apps under `apps/` with explicit `label` in `apps.py` so `apps.users` registers as `users`.

WebSocket: `ws/reunions/<reunion_id>/?token=<jwt>` — ASGI only, requires Redis running.

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
- Signals only when no alternative (prefer `save()` override or serializer hooks). Existing signals: auto-add creator to groups/reunions on creation; auto-add invitee to group on invitation accept.
- Keep response keys matching Rails output (see `../backend/AI_GUIDANCE.md` §4). Critical for frontend compat.

### Key patterns

**`BusinessRulesMixin`** (`config/serializers.py`): Mix into serializers to run model `clean()` during DRF validation. All serializers that need cross-field model validation should use this.

**Nested routing** (`rest_framework_nested`): Used for `student_groups → student_group_invitations` and `reunions → reunion_messages`. Register a `NestedSimpleRouter` against the parent router; viewset gets `<parent>_pk` in `kwargs`.

**Request payload unwrapping**: Some viewsets call `_unwrap(request.data, "key")` to strip a wrapper key (e.g. `{"reunion": {...}}` → `{...}`). Match existing apps' pattern when adding new resources.

**Access control on models**: Use model methods (`StudentGroup.manageable_by(user)`, `Reunion.join_restriction_error_for(student)`) rather than inline view logic. Raise `PermissionDenied` / return error string in those methods.

**WebSocket broadcast**: `ReunionMessage` creation triggers `channel_layer.group_send` to `reunion_<id>`. Consumer (`apps/reunions/consumers.py`) validates JWT from query param on connect (closes 4001 if invalid), then forwards `reunion.message` events as `{"event": "message_created", "message": {...}}`.

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
python manage.py import_scraped_subjects  # seed academics data
```

## Settings split

- `config/settings/base.py` — shared
- `config/settings/dev.py` — `DJANGO_SETTINGS_MODULE=config.settings.dev` (default via `manage.py`)
- `config/settings/prod.py` — WSGI/ASGI default

## Testing

- Request specs under `tests/api/`.
- Fixtures via `factory_boy` under `tests/factories/`.
- `tests/conftest.py` provides `api_client` fixture (unauthenticated `APIClient`).
- Cover happy path + validation/error path (check 422 + `{"errors": [...]}`).
- Contract tests: diff response JSON against Rails to catch drift.

## Adding a new resource (checklist)

1. Model with `db_table`, `Meta.ordering`, constraints.
2. Migration (`makemigrations`).
3. Serializer — match Rails response keys; use `BusinessRulesMixin` if model has `clean()`.
4. ViewSet (`ModelViewSet`) + router registration in `config/urls.py`.
5. Admin registration.
6. Factory + request tests.

## When in doubt

Pick the idiom a seasoned Django dev would reach for first. Don't port Rails quirks literally when a Django equivalent is cleaner (e.g. HABTM → `ManyToManyField`, callbacks → serializer `validate`, Devise → allauth).

## Migration Plan

See `../backend/DJANGO_MIGRATION_PLAN.md` for full phased migration plan and current status.
