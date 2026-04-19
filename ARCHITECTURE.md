# FocusGuard Architecture

## 1. Product Vision

FocusGuard is a digital wellness platform designed to reduce distraction, repair attention, and improve productivity for people affected by digital overload.

It targets:

- students
- young adults
- children under parent supervision

Primary outcomes:

- reduce interruptions from notifications and compulsive scrolling
- improve focus and task completion
- build healthier habits through behavioral coaching
- help parents monitor children safely and supportively
- provide localized, bilingual experiences in English and Arabic

## 2. Senior-Level Architecture

### A. Client Applications

Clients include:

- mobile app for Android and iOS
- responsive web dashboard
- parent dashboard

Core responsibilities:

- collect consent and device permissions
- show focus sessions, habit streaks, and insights
- deliver intervention prompts and mini-games
- let users enter data manually if permissions are unavailable

### B. Device Intelligence Layer

This layer operates on-device when permissions are granted.

Responsibilities:

- monitor notification intensity
- monitor app switching and social media dwell time
- identify distraction spikes
- trigger focus mode automation where supported
- keep sensitive raw behavior data local when possible

If the user refuses permission:

- the application switches to guided self-reporting
- manual inputs feed the personalization engine
- the dashboard remains functional with reduced accuracy

### C. Application Services Layer

Backend services are split by responsibility.

Recommended services:

- `identity-service`
- `profile-service`
- `focus-session-service`
- `habit-service`
- `intervention-service`
- `insights-service`
- `guardian-service`
- `notification-service`
- `localization-service`

Responsibilities:

- authenticate users and guardians
- manage children and guardian relationships
- store plans, sessions, and habit progress
- generate interventions and practical advice
- expose APIs for dashboards and reports
- support multilingual content delivery

### D. AI and Personalization Layer

Use hybrid intelligence rather than only a black-box model.

Inputs:

- notification load
- screen time
- app-switch frequency
- sleep quality
- completed focus sessions
- planning consistency
- self-reported mood and fatigue

Outputs:

- focus score
- distraction risk state
- personalized daily plan
- intervention timing
- guardian guidance

Recommended methods:

- rule engine for safety and immediate triggers
- behavioral segmentation for user type classification
- recommendation model for habit and focus plan selection
- analytics jobs for long-term patterns

### E. Data Layer

Use a split data strategy.

Operational database:

- `PostgreSQL`

Analytics storage:

- `BigQuery`, `ClickHouse`, or `Snowflake`

Caching:

- `Redis`

Important data entities:

- users
- guardians
- child profiles
- focus sessions
- interventions
- habits
- insights
- app usage summaries
- notification summaries

### F. Privacy and Safety Layer

This is critical for real production.

Requirements:

- explicit consent for device-level monitoring
- child account protections
- region-aware privacy settings
- minimum-data collection defaults
- guardian access controls
- audit logging for parent actions
- encrypted data in transit and at rest

### G. Globalization Layer

The platform should scale globally.

Important design choices:

- localization-ready content system
- English and Arabic support from the first release
- timezone-aware scheduling
- configurable intervention rules by market
- feature flags for country-specific compliance needs

## 3. Key Workflows

### User Focus Recovery Workflow

1. User signs in and selects language.
2. User grants permissions or enters behavior data manually.
3. Device layer or self-report form sends behavior summary.
4. Personalization engine calculates focus score and risk state.
5. Dashboard shows plan, habits, and interventions.
6. User completes sessions and attention games.
7. Progress feeds future recommendations.

### Parent Monitoring Workflow

1. Guardian links a child account.
2. Guardian views safe summaries instead of invasive raw details.
3. System detects sustained overload or unhealthy trends.
4. Guardian receives guidance and recommended actions.
5. Guardian adjusts schedule rules and encouragement patterns.

## 4. Suggested Tech Stack

Frontend:

- `Next.js` or `React`
- `TypeScript`
- `Tailwind CSS` or custom design system

Mobile:

- `Flutter` or `React Native`

Backend:

- `FastAPI` or `NestJS`
- `PostgreSQL`
- `Redis`

Analytics:

- `dbt`
- `ClickHouse` or `BigQuery`

Notifications:

- Firebase Cloud Messaging
- APNs
- email provider for guardian summaries

## 5. Build Roadmap

### Phase 1

- authentication
- onboarding
- focus dashboard
- manual input fallback
- personalized plans
- English and Arabic UI

### Phase 2

- device-permission data collection
- intervention automation
- attention mini-games
- guardian dashboard

### Phase 3

- production analytics
- adaptive recommendation models
- localization expansion
- enterprise education partnerships

## 6. Senior Engineering Notes

- Design the product to remain useful without device permissions.
- Keep child monitoring supportive, not punitive.
- Separate raw device signals from summarized analytics.
- Make the intervention engine explainable.
- Treat bilingual support as a first-class system concern, not a UI afterthought.
- Add observability, audit trails, and privacy controls early.
