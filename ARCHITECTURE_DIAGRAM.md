# FocusGuard Diagram Set

Below is a senior-style diagram pack in proper system-analysis formats.

## 1. System Workflow Diagram

```mermaid
flowchart LR
    U["User / Child"] --> O["Onboarding & Consent"]
    O --> P{"Permission granted?"}
    P -->|Yes| D["Device Behavior Collector"]
    P -->|No| M["Manual Behavior Input"]
    D --> E["Personalization Engine"]
    M --> E
    E --> F["Focus Plan Generator"]
    E --> I["Insight Engine"]
    F --> UD["User Dashboard"]
    I --> UD
    UD --> S["Focus Sessions / Habit Actions / Attention Games"]
    S --> E
    E --> G["Guardian Monitoring Service"]
    G --> PD["Parent Dashboard"]
    E --> N["Notification & Intervention Service"]
    N --> U
```

## 2. Use Case Diagram

```mermaid
flowchart LR
    user(("User"))
    parent(("Parent"))
    admin(("Admin"))

    subgraph System["FocusGuard System"]
        uc1["Register and sign in"]
        uc2["Grant or deny device permissions"]
        uc3["Track distraction and focus"]
        uc4["Start focus session"]
        uc5["Play attention game"]
        uc6["View personalized insights"]
        uc7["Manage habits and streaks"]
        uc8["Monitor child dashboard"]
        uc9["Receive guardian guidance"]
        uc10["Manage bilingual content and policy rules"]
    end

    user --> uc1
    user --> uc2
    user --> uc3
    user --> uc4
    user --> uc5
    user --> uc6
    user --> uc7
    parent --> uc8
    parent --> uc9
    admin --> uc10
```

## 3. Data Flow Diagram

```mermaid
flowchart LR
    ext1["User"] --> p1["P1 Onboarding & Consent"]
    ext2["Guardian"] --> p4["P4 Guardian Monitoring"]

    p1 --> d1[("D1 User Profile Store")]
    p1 --> p2["P2 Behavior Collection"]
    p2 --> d2[("D2 Behavior Summary Store")]
    p2 --> p3["P3 Personalization & Scoring"]
    d1 --> p3
    d2 --> p3
    p3 --> d3[("D3 Focus Plan Store")]
    p3 --> d4[("D4 Insight Store")]
    p3 --> p5["P5 Intervention Engine"]
    d3 --> p6["P6 User Dashboard"]
    d4 --> p6
    p6 --> ext1
    p4 --> d1
    d3 --> p4
    d4 --> p4
    p4 --> ext2
    p5 --> ext1
```

## 4. Activity Diagram

```mermaid
flowchart TD
    A["User opens app"] --> B["Select language"]
    B --> C["Sign in or create account"]
    C --> D["Choose permission-based tracking or manual input"]
    D --> E["Collect behavior summary"]
    E --> F["Calculate focus score"]
    F --> G{"Is distraction risk high?"}
    G -->|Yes| H["Activate intervention and recommend short focus block"]
    G -->|No| I["Recommend standard daily plan"]
    H --> J["User starts session or attention game"]
    I --> J
    J --> K["Update habit streak and progress"]
    K --> L["Show dashboard insights"]
    L --> M["End or continue next cycle"]
```

## 5. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Onboarding
    Onboarding --> Monitoring: Profile completed
    Monitoring --> Focused: Low distraction risk
    Monitoring --> Overloaded: High distraction risk
    Overloaded --> Intervention: Trigger focus shield
    Intervention --> Recovering: User completes session
    Recovering --> Focused: Streak improves
    Focused --> Monitoring: Normal reassessment
    Recovering --> Overloaded: Relapse detected
    Focused --> Overloaded: Notification spike
    Monitoring --> ParentReview: Child account flagged
    ParentReview --> Monitoring: Guidance acknowledged
```

## 6. Class Diagram

```mermaid
classDiagram
    class User {
      +UUID userId
      +string name
      +string preferredLanguage
      +bool permissionsGranted
      +login()
      +updatePreferences()
    }

    class ChildProfile {
      +UUID childId
      +string ageGroup
      +int notificationThreshold
      +linkGuardian()
    }

    class Guardian {
      +UUID guardianId
      +string relationshipType
      +reviewChildProgress()
    }

    class BehaviorSummary {
      +UUID summaryId
      +int notifications
      +float socialHours
      +float sleepHours
      +int planningConsistency
      +capture()
    }

    class FocusPlan {
      +UUID planId
      +int sessionMinutes
      +string focusTheme
      +generate()
    }

    class Habit {
      +UUID habitId
      +string title
      +int streakDays
      +markComplete()
    }

    class Insight {
      +UUID insightId
      +string title
      +string action
      +publish()
    }

    class Intervention {
      +UUID interventionId
      +string type
      +string triggerReason
      +activate()
    }

    User "1" --> "0..*" BehaviorSummary
    User "1" --> "0..*" FocusPlan
    User "1" --> "0..*" Habit
    User "1" --> "0..*" Insight
    User "1" --> "0..*" Intervention
    ChildProfile --|> User
    Guardian "1" --> "0..*" ChildProfile
```

## 7. ERD

```mermaid
erDiagram
    USERS {
        uuid user_id PK
        string full_name
        string email
        string preferred_language
        boolean permissions_granted
        string account_type
    }

    GUARDIANS {
        uuid guardian_id PK
        uuid user_id FK
        string relationship_type
    }

    CHILD_PROFILES {
        uuid child_id PK
        uuid user_id FK
        uuid guardian_id FK
        string age_group
    }

    BEHAVIOR_SUMMARIES {
        uuid summary_id PK
        uuid user_id FK
        int daily_notifications
        decimal social_media_hours
        decimal sleep_hours
        int planning_consistency
        datetime captured_at
    }

    FOCUS_PLANS {
        uuid plan_id PK
        uuid user_id FK
        int session_minutes
        string focus_theme
        datetime generated_at
    }

    HABITS {
        uuid habit_id PK
        uuid user_id FK
        string title
        int streak_days
        int progress_percent
    }

    INSIGHTS {
        uuid insight_id PK
        uuid user_id FK
        string title
        string action_text
        datetime generated_at
    }

    INTERVENTIONS {
        uuid intervention_id PK
        uuid user_id FK
        string intervention_type
        string trigger_reason
        datetime triggered_at
    }

    USERS ||--o| GUARDIANS : owns
    GUARDIANS ||--o{ CHILD_PROFILES : supervises
    USERS ||--o{ CHILD_PROFILES : extends
    USERS ||--o{ BEHAVIOR_SUMMARIES : produces
    USERS ||--o{ FOCUS_PLANS : receives
    USERS ||--o{ HABITS : practices
    USERS ||--o{ INSIGHTS : receives
    USERS ||--o{ INTERVENTIONS : triggers
```
