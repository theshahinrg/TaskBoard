# TaskBoard (Django)

Created by **TheShahinRG** — https://shahindev.com

Lightweight team task board for tracking projects, assigning tasks, and moving work across a simple status board.

## Tech stack
- Python 3.12+ (3.11+ works)
- Django 4.2
- SQLite (default; adjust in `TaskBoard/settings.py` if needed)

## Getting started
1. (Optional) Create and activate a virtualenv:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate migration files (whenever you change your models):
   ```bash
   python manage.py makemigrations
   ```
4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
5. Create an admin user:
   ```bash
   python manage.py createsuperuser
   ```
6. Start the dev server:
   ```bash
   python manage.py runserver
   ```
7. Log in at `/accounts/login/` (Django admin at `/admin/`), create a project, and add members to share access.

## Running tests
```bash
python manage.py test
```

## Features
- Auth-protected projects; only owners and members can view or edit, and owners are auto-added as members.
- Project board groups tasks by status (To Do, Doing, Done) with quick edit/status/delete actions.
- Tasks track priority (Low/Medium/High), assignee, deadline, and show an overdue badge when past due.
- Owner-only project CRUD; task create/update/delete available to project members for collaborative work.
- Django admin configured with search, filters, and autocomplete for projects, tasks, and comments.
- Starter UI with Django templates and a lightweight CSS theme in `static/style.css`.

## Screenshots
Add your own captures to `screenshots/` and list them here, for example:
- `screenshots/project-board.png`
- `screenshots/task-form.png`
