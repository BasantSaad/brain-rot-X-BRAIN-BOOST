# FocusGuard

FocusGuard is a bilingual anti-distraction application concept aimed at reducing digital overload and "brain rot" for students, young adults, and children.

It includes:

- a polished English and Arabic web dashboard
- smart intervention support when device permissions are granted
- fallback manual estimation when the user does not share permissions
- habit coaching and attention-training activities
- a guardian dashboard for parents of younger users
- practical, data-driven focus insights

## Run locally

Use Python 3.11+ if possible.

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Product scope

The local demo models a production-ready product direction with:

- user dashboard
- parent dashboard
- personalized focus plans
- bilingual interface
- API-first backend shape
- architecture and UML/data-flow documentation

## Main files

- `app.py`
  - lightweight HTTP server and API endpoints
- `agent/focus_engine.py`
  - personalization, scoring, and guidance logic
- `simulator/behavior_simulator.py`
  - mock user behavior data generation
- `shared/schemas.py`
  - domain contracts for dashboard and plans
- `static/`
  - beautiful frontend UI
- `ARCHITECTURE.md`
  - senior-level system architecture
- `ARCHITECTURE_DIAGRAM.md`
  - full diagram set
