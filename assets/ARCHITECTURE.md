# Bboo Architecture

## 1. Product Vision

Bboo is a real anti-distraction application designed to reduce digital overload, rebuild attention, and improve productivity for students, young adults, and children under guardian care.

The product begins with account creation and profile onboarding before the user enters the application dashboard.

## 2. Core Real-Application Flow

The real application should work in this order:

1. User opens Bboo.
2. User creates an account or signs in.
3. User enters important profile data.
4. User grants device permissions or chooses manual data input.
5. Bboo creates the profile and baseline behavior model.
6. User enters the dashboard.
7. Bboo continuously updates habits, graphs, interventions, and insights.

Important profile data:

- first name
- last name
- email
- country
- preferred language
- audience type
- account role
- permission consent

## 3. Senior-Level Architecture

### A. Client Experience Layer

Applications:

- mobile app
- responsive web app
- parent dashboard

Responsibilities:

- registration and login
- profile creation and profile editing
- language selection
- dashboard presentation
- graph rendering
- focus sessions and attention games
- guardian controls

### B. Identity and Profile Layer

Services:

- `auth-service`
- `profile-service`

Responsibilities:

- account creation
- login and session management
- password reset
- guardian-child linking
- role-based access
- profile completion tracking

### C. Device Intelligence Layer

This layer runs when permissions are granted.

Responsibilities:

- capture notification intensity
- capture app switching behavior
- estimate distraction load
- detect high-risk time windows
- trigger focus intervention hooks

If permissions are denied:

- Bboo collects manual profile and self-report data
- the dashboard still works
- insight confidence is marked as estimated

### D. Personalization and Intervention Layer

Services:

- `focus-engine`
- `habit-engine`
- `intervention-engine`
- `insights-engine`
- `guardian-guidance-engine`

Outputs:

- focus score
- personalized plan
- habit recommendations
- graph-ready trend summaries
- supportive parent guidance

### E. Data Layer

Operational data:

- `PostgreSQL`

Cache and sessions:

- `Redis`

Analytics and trend storage:

- `ClickHouse` or `BigQuery`

Core entities:

- users
- guardians
- child_profiles
- behavior_summaries
- focus_plans
- habits
- interventions
- insights
- dashboard_snapshots

### F. Notification and Communication Layer

Responsibilities:

- intervention prompts
- session reminders
- guardian alerts for sustained overload
- email verification
- localized notifications

### G. Globalization and Policy Layer

Requirements:

- English and Arabic from release one
- timezone-aware scheduling
- local privacy policy variations
- child-safety controls by region

## 4. Security and Privacy

Because Bboo may involve children and behavior data, the real system must include:

- consent-first monitoring
- guardian authorization checks
- encryption at rest and in transit
- profile audit trails
- minimal default data collection
- explainable parent summaries instead of raw surveillance

## 5. Visual System Direction

### User Dashboard

- primary tone: Electric Fuchsia
- emotional goal: energetic, high-saturation, motivating, attention-grabbing

### Parent Dashboard

- primary tone: Transformative Teal
- emotional goal: responsibility, guidance, calm oversight, trust

## 6. Production Build Roadmap

### Phase 1

- authentication
- profile onboarding
- bilingual dashboards
- manual-input fallback
- graphs and habits

### Phase 2

- mobile permission integration
- distraction intervention automation
- attention games
- guardian linking

### Phase 3

- analytics warehouse
- adaptive recommendations
- regional expansion
- production observability
