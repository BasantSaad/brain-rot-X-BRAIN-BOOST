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
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Real application flow

1. User enters important data:
   first name, last name, email, country, audience, language, and permission choice.
2. Bboo creates the account profile.
3. The user enters the dashboard with personalized metrics, graphs, habits, and plans.
4. Parent mode applies a distinct guardian dashboard and guidance model.

## Main files

- `app.py`
  - lightweight API server and account/profile query handling
- `agent/focus_engine.py`
  - personalization, charts, and guidance logic
- `simulator/behavior_simulator.py`
  - mock account and behavior generation
- `shared/schemas.py`
  - domain contracts for profile, dashboard, charts, and plans
- `static/`
  - icon, onboarding UI, and themed dashboards
- `ARCHITECTURE.md`
  - senior-level real-application architecture
- `ARCHITECTURE_DIAGRAM.md`
  - workflow, UML, DFD, and ERD diagrams
