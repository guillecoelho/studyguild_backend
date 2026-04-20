# StudyGuild Backend (Django)

Django 5 + DRF rewrite of the Rails `backend/`. JSON API under `/api/*`, Django Admin under `/admin`.

## Requirements

- Python 3.12+
- (Optional) PostgreSQL 15+, Redis 7+ for production
- SQLite works for local dev out of the box

## Setup

```bash
cd studyguild-django
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## URLs

- `/admin/` — Django Admin (replaces Rails `Admin::*`)
- `/up` — health check
- `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/registration/`, `/api/auth/user/` — auth (dj-rest-auth + JWT)
- `/api/schema/` — OpenAPI YAML
- `/api/docs/` — Swagger UI

## Layout

```
studyguild-django/
├── config/              # project: settings, urls, wsgi, asgi, exceptions
│   └── settings/        # base.py, dev.py, prod.py
├── apps/
│   ├── users/           # custom User model (email login, role)
│   ├── institutions/
│   ├── academics/       # subjects, subject_groups
│   ├── groups/          # student_groups, invitations
│   ├── reunions/        # reunions, reunion_messages
│   └── community/       # newsletter_entries, issue_reports
├── tests/               # pytest-django request tests
├── manage.py
├── pytest.ini
├── pyproject.toml       # ruff config
├── requirements.txt
└── requirements-dev.txt
```

## Commands

```bash
python manage.py runserver              # dev server :8000
python manage.py makemigrations         # create migrations
python manage.py migrate                # apply migrations
python manage.py createsuperuser        # create admin user
pytest                                  # full test suite
pytest tests/api/test_students.py       # single file
ruff check .                            # lint
ruff format .                           # auto-format
```

## Env Vars

See `.env.example`. Key settings:

- `DEBUG` — truthy in dev, false in prod
- `SECRET_KEY` — set a real value in prod
- `ALLOWED_HOSTS` — comma-separated
- `DATABASE_URL` — e.g. `postgres://user:pass@host:5432/dbname`
- `REDIS_URL` — Celery broker
- `CORS_ALLOWED_ORIGINS` — comma-separated frontend origins

## API Contract

Endpoints mirror the Rails API (see `../backend/AI_GUIDANCE.md` §4). Custom exception handler in `config/exceptions.py` preserves Rails-compatible error shapes:

- 404 → `{"error": "..."}`
- Validation → `{"errors": [...]}` with **status 422**

## Migration Status

- [x] Phase 0 — project scaffold, deps, settings split
- [x] Phase 1 — custom User model, auth endpoints (dj-rest-auth + JWT)
- [x] Phase 2a — `Institution` model + admin
- [ ] Phase 2b — remaining models (Subject, Reunion, groups, newsletter, issues)
- [ ] Phase 3 — ViewSets + serializers for all resources
- [ ] Phase 4 — business rule validations
- [ ] Phase 5 — Celery + storage
- [ ] Phase 6 — test suite port
- [ ] Phase 7 — admin polish
- [ ] Phase 8 — Dockerfile + deploy
- [ ] Phase 9 — cutover

Full plan: `../backend/DJANGO_MIGRATION_PLAN.md`.
