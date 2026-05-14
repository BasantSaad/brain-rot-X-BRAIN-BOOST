# Bboo

Bboo is a bilingual anti-distraction application concept built to reduce digital overload and "brain rot" through account-based onboarding, personalized focus recovery, supportive parent monitoring, and practical behavior insights.

It now includes:

- a real account and profile-first flow
- a custom Bboo icon
- Electric Fuchsia visual identity for user mode
- Transformative Teal visual identity for parent mode
- dashboard graphs for focus recovery and behavior balance
- permission-aware behavior tracking with profile-input fallback
- English and Arabic support

## Run locally

Use Python 3.11+ if possible.

```powershell
pip install -r requirements.txt
```

Create a local `.env` file in the project root or set these environment variables first:

```text
BBOO_DB_HOST=127.0.0.1
BBOO_DB_PORT=3306
BBOO_DB_USER=root
BBOO_DB_PASSWORD=your_mysql_password
BBOO_DB_NAME=bboo
```

Then start the app:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Run with Docker

You can run Bboo fully in Docker without XAMPP.

1. Install Docker Desktop and make sure it is running.
2. Open PowerShell in the project folder:

```powershell
cd "D:\college materials\4 semester 2\System Analysis\Brain rot\brain-rot-X-BRAIN-BOOST"
```

3. If you already have the local Python server running on port `8000`, stop it first.
4. Build and start the containers:

```powershell
docker compose up --build
```

5. Wait until you see the app container and MySQL container become healthy.
6. Open the app:

```text
http://127.0.0.1:8000
```

Docker notes:

- the Bboo web app runs on port `8000`
- the MySQL container is exposed on port `3307` on your machine
- inside Docker, the app connects to MySQL by service name `mysql`
- the database data is stored in the Docker volume `bboo_mysql_data`

Useful Docker commands:

```powershell
docker compose down
docker compose up
docker compose logs -f
```

If you also want to inspect the Docker MySQL database in phpMyAdmin or another client, use:

```text
Host: 127.0.0.1
Port: 3307
User: root
Password: bboo_root
Database: bboo
```

## XAMPP MySQL setup

1. Open XAMPP Control Panel.
2. Start `MySQL`.
3. Open [http://localhost/phpmyadmin](http://localhost/phpmyadmin).
4. If your MySQL `root` user has no password in XAMPP, set `BBOO_DB_PASSWORD=` as empty in `.env`.
5. If your MySQL `root` user has a password, put that password in `.env`.
6. Run the app with `python app.py`.

The app will create the `bboo` database and its tables automatically on startup.

If you prefer creating the schema manually in phpMyAdmin, import:

- `storage/schema.sql`

## Real application flow

1. User enters important data:
   first name, last name, email, country, audience, language, and permission choice.
2. Bboo creates the account profile.
3. The user enters the dashboard with personalized metrics, graphs, habits, and plans.
4. Parent mode applies a distinct guardian dashboard and guidance model.

## Main files

- `app.py`
  - lightweight API server plus MySQL-backed auth/profile endpoints
- `agent/focus_engine.py`
  - personalization, charts, and guidance logic
- `simulator/behavior_simulator.py`
  - mock account and behavior generation
- `storage/mysql_repository.py`
  - MySQL persistence, schema bootstrap, and password verification
- `storage/schema.sql`
  - optional phpMyAdmin/XAMPP import script for the MySQL schema
- `shared/schemas.py`
  - domain contracts for profile, dashboard, charts, and plans
- `static/`
  - icon, onboarding UI, and themed dashboards
- `ARCHITECTURE.md`
  - senior-level real-application architecture
- `ARCHITECTURE_DIAGRAM.md`
  - workflow, UML, DFD, and ERD diagrams
