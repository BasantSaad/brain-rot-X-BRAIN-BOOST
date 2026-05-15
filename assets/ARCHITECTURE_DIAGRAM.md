# Bboo Senior Diagram Set

This file provides a cleaner, senior-level diagram pack for the current Bboo system.

Modeling note:

- the workflow, use case, DFD, activity, state, and ERD diagrams describe the intended real system architecture
- the class diagram is aligned to the current Python implementation in this repository

## 1. System Workflow Diagram

```mermaid
flowchart TD
    A["Visitor opens Bboo"] --> B["Register or sign in"]
    B --> C["Create or complete profile"]
    C --> D["Select language, audience, and role"]
    D --> E{"Permission granted?"}

    E -->|Yes| F["Collect device behavior signals"]
    E -->|No| G["Use manual profile and self-report input"]

    F --> H["Build user behavior profile"]
    G --> H

    H --> I["Generate dashboard snapshot"]
    H --> J["Generate personalized focus plan"]

    I --> K["User dashboard"]
    J --> K

    K --> L{"Parent mode?"}
    L -->|No| M["User reviews metrics, habits, insights, and charts"]
    L -->|Yes| N["Parent reviews guidance and child trends"]

    M --> O["Start focus session or attention game"]
    O --> P["Update recovery indicators"]
    P --> I
```

## 2. Use Case Diagram

```mermaid
flowchart LR
    visitor["<<Actor>> Visitor"]
    user["<<Actor>> User"]
    parent["<<Actor>> Parent"]
    admin["<<Actor>> Admin"]

    subgraph bboo["Bboo System"]
        uc1(["Register account"])
        uc2(["Sign in"])
        uc3(["Complete profile"])
        uc4(["Choose language and audience"])
        uc5(["Grant behavior-tracking permission"])
        uc6(["Provide manual behavior input"])
        uc7(["View dashboard"])
        uc8(["View personalized plan"])
        uc9(["Review charts, habits, and insights"])
        uc10(["Start focus session"])
        uc11(["Play attention game"])
        uc12(["Review child guidance dashboard"])
        uc13(["Manage localization and policy"])
    end

    visitor --> uc1
    visitor --> uc2

    user --> uc3
    user --> uc4
    user --> uc5
    user --> uc6
    user --> uc7
    user --> uc8
    user --> uc9
    user --> uc10
    user --> uc11

    parent --> uc12
    admin --> uc13

    uc7 -. includes .-> uc9
    uc7 -. includes .-> uc8
    uc10 -. extends .-> uc7
    uc11 -. extends .-> uc7
    uc6 -. alternate to .-> uc5
```

## 3. Data Flow Diagram

### Level 0

```mermaid
flowchart LR
    user["External Entity: User"] --> system["P0 Bboo Platform"]
    parent["External Entity: Parent"] --> system
    admin["External Entity: Admin"] --> system

    system --> user
    system --> parent
```

### Level 1

```mermaid
flowchart LR
    user["User"] --> p1["P1 Account and Profile Management"]
    p1 --> d1[("D1 Account Store")]
    p1 --> d2[("D2 Profile Store")]

    user --> p2["P2 Behavior Input Processing"]
    p2 --> d3[("D3 Behavior Summary Store")]

    d2 --> p3["P3 Focus Scoring and Personalization"]
    d3 --> p3
    p3 --> d4[("D4 Focus Plan Store")]
    p3 --> d5[("D5 Dashboard Snapshot Store")]
    p3 --> d6[("D6 Insight Store")]

    d4 --> p4["P4 Dashboard Delivery"]
    d5 --> p4
    d6 --> p4
    p4 --> user

    parent --> p5["P5 Parent Guidance and Monitoring"]
    d2 --> p5
    d5 --> p5
    d6 --> p5
    p5 --> parent

    admin --> p6["P6 Policy and Localization Management"]
    p6 --> d7[("D7 Policy and Locale Configuration")]
```

## 4. Activity Diagram

```mermaid
flowchart TD
    start(["Start"]) --> a1["Open application"]
    a1 --> a2["Register or sign in"]
    a2 --> a3["Enter profile data"]
    a3 --> a4["Select audience, role, and language"]
    a4 --> a5{"Permission granted?"}

    a5 -->|Yes| a6["Capture behavior signals"]
    a5 -->|No| a7["Use manual behavior input"]

    a6 --> a8["Build user profile"]
    a7 --> a8

    a8 --> a9["Calculate focus score"]
    a9 --> a10["Generate dashboard snapshot"]
    a10 --> a11["Display metrics, charts, habits, and insights"]
    a11 --> a12{"High distraction risk?"}

    a12 -->|Yes| a13["Recommend intervention or attention game"]
    a12 -->|No| a14["Continue normal recovery plan"]

    a13 --> a15["User completes focus session"]
    a14 --> a15

    a15 --> a16["Refresh indicators and trends"]
    a16 --> end(["End"])
```

## 5. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Visitor
    Visitor --> Authenticated : register or login success
    Authenticated --> ProfileIncomplete : session created
    ProfileIncomplete --> ProfileReady : profile completed
    ProfileReady --> MonitoringEnabled : permission granted
    ProfileReady --> MonitoringEstimated : manual input selected

    MonitoringEnabled --> DashboardActive : dashboard generated
    MonitoringEstimated --> DashboardActive : estimated dashboard generated

    DashboardActive --> FocusStable : score >= recovery threshold
    DashboardActive --> FocusAtRisk : score < recovery threshold

    FocusAtRisk --> InterventionSuggested : high distraction risk detected
    InterventionSuggested --> Recovering : focus session completed
    Recovering --> DashboardActive : metrics recalculated

    FocusStable --> ParentReview : parent mode opened
    FocusAtRisk --> ParentReview : parent mode opened
    ParentReview --> DashboardActive : guidance reviewed
```

## 6. Class Diagram

```mermaid
classDiagram
    class BbooRequestHandler {
        +do_GET()
        -_handle_dashboard(query)
        -_handle_plan(query)
        -_build_profile(query)
        -_send_json(payload)
    }

    class FocusCoachEngine {
        +build_dashboard(profile, language, mode) DashboardSnapshot
        +build_personalized_plan(profile, language) FocusPlan
        -_focus_score(profile) int
    }

    class BehaviorSimulator {
        +build_profile(audience, permissions_granted, first_name, last_name, email, country, preferred_language, role) UserProfile
    }

    class AccountProfile {
        +first_name: str
        +last_name: str
        +email: str
        +country: str
        +preferred_language: str
        +role: str
        +age_group: str
    }

    class UserProfile {
        +permissions_granted: bool
        +daily_notifications: int
        +social_media_hours: float
        +sleep_hours: float
        +planning_consistency: int
        +completed_focus_sessions_last_week: int
    }

    class DashboardSnapshot {
        +generated_at: str
        +app_name: str
        +language: str
        +mode: str
        +headline: str
        +focus_score: int
        +current_state: str
    }

    class FocusPlan {
        +generated_at: str
        +title: str
        +recommended_session_minutes: int
        +focus_theme: str
        +attention_game: str
    }

    class FocusMetric
    class HabitCard
    class InsightCard
    class ChartSeries
    class TrendPoint
    class ProfileField
    class ParentGuidance

    BbooRequestHandler --> FocusCoachEngine : uses
    BbooRequestHandler --> BehaviorSimulator : uses
    FocusCoachEngine --> UserProfile : reads
    BehaviorSimulator --> UserProfile : creates
    UserProfile *-- AccountProfile
    FocusCoachEngine --> DashboardSnapshot : creates
    FocusCoachEngine --> FocusPlan : creates
    DashboardSnapshot *-- FocusMetric
    DashboardSnapshot *-- HabitCard
    DashboardSnapshot *-- InsightCard
    DashboardSnapshot *-- ChartSeries
    DashboardSnapshot *-- ProfileField
    DashboardSnapshot o-- ParentGuidance
    ChartSeries *-- TrendPoint
```

## 7. ERD

```mermaid
erDiagram
    ACCOUNTS {
        uuid account_id PK
        string email
        string password_hash
        string status
        datetime created_at
        datetime updated_at
    }

    PROFILES {
        uuid profile_id PK
        uuid account_id FK
        string first_name
        string last_name
        string country
        string preferred_language
        string role
        string age_group
        boolean permissions_granted
        datetime created_at
        datetime updated_at
    }

    BEHAVIOR_SUMMARIES {
        uuid behavior_summary_id PK
        uuid profile_id FK
        int daily_notifications
        decimal social_media_hours
        decimal sleep_hours
        int planning_consistency
        int completed_focus_sessions_last_week
        string signal_source
        datetime captured_at
    }

    FOCUS_PLANS {
        uuid focus_plan_id PK
        uuid profile_id FK
        int recommended_session_minutes
        string focus_theme
        string attention_game
        datetime generated_at
    }

    DASHBOARD_SNAPSHOTS {
        uuid snapshot_id PK
        uuid profile_id FK
        string mode
        int focus_score
        string current_state
        datetime generated_at
    }

    INSIGHTS {
        uuid insight_id PK
        uuid snapshot_id FK
        string title
        string detail
        string action_text
    }

    HABITS {
        uuid habit_id PK
        uuid snapshot_id FK
        string title
        int progress
        string encouragement
    }

    CHART_SERIES {
        uuid chart_series_id PK
        uuid snapshot_id FK
        string title
        string subtitle
        string chart_type
    }

    TREND_POINTS {
        uuid trend_point_id PK
        uuid chart_series_id FK
        string label
        decimal value
        int display_order
    }

    GUARDIAN_LINKS {
        uuid guardian_link_id PK
        uuid guardian_profile_id FK
        uuid child_profile_id FK
        string relationship_type
        datetime linked_at
    }

    ACCOUNTS ||--|| PROFILES : owns
    PROFILES ||--o{ BEHAVIOR_SUMMARIES : produces
    PROFILES ||--o{ FOCUS_PLANS : receives
    PROFILES ||--o{ DASHBOARD_SNAPSHOTS : generates
    DASHBOARD_SNAPSHOTS ||--o{ INSIGHTS : contains
    DASHBOARD_SNAPSHOTS ||--o{ HABITS : contains
    DASHBOARD_SNAPSHOTS ||--o{ CHART_SERIES : contains
    CHART_SERIES ||--o{ TREND_POINTS : contains
    PROFILES ||--o{ GUARDIAN_LINKS : acts_as_guardian
    PROFILES ||--o{ GUARDIAN_LINKS : acts_as_child
```

## 8. Senior Modeling Notes

- `System Workflow` shows the end-to-end operational journey from entry to dashboard refresh.
- `Use Case Diagram` focuses on actors and business interactions, not internal processing.
- `DFD` separates external entities, processes, and data stores in proper data-flow style.
- `Activity Diagram` models the procedural path and decision points.
- `State Diagram` models how a user account/session progresses through system states.
- `Class Diagram` reflects the code currently implemented in `app.py`, `agent/focus_engine.py`, `simulator/behavior_simulator.py`, and `shared/schemas.py`.
- `ERD` reflects the production-ready persistence design the current prototype is moving toward.
