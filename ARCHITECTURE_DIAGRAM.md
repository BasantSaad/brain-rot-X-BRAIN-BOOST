# Bboo Diagram Set

## 1. System Workflow Diagram

```mermaid
flowchart LR
    V["Visitor"] --> A["Account Registration / Sign In"]
    A --> P["Profile Creation"]
    P --> C{"Permission granted?"}
    C -->|Yes| D["Device Signal Collector"]
    C -->|No| M["Manual Behavior Input"]
    D --> E["Focus Personalization Engine"]
    M --> E
    E --> H["Habit and Plan Engine"]
    E --> I["Insight and Graph Engine"]
    H --> U["User Dashboard"]
    I --> U
    U --> G["Attention Games / Focus Sessions"]
    G --> E
    E --> R["Guardian Guidance Engine"]
    R --> PD["Parent Dashboard"]
```

## 2. Use Case Diagram

```mermaid
flowchart LR
    visitor(("Visitor"))
    user(("User"))
    parent(("Parent"))
    admin(("Admin"))

    subgraph System["Bboo System"]
        uc1["Create account"]
        uc2["Sign in"]
        uc3["Create profile"]
        uc4["Grant device permission"]
        uc5["View dashboard graphs"]
        uc6["Start focus session"]
        uc7["Play attention game"]
        uc8["Review insights and habits"]
        uc9["Monitor child account"]
        uc10["Manage platform policy and localization"]
    end

    visitor --> uc1
    visitor --> uc2
    user --> uc3
    user --> uc4
    user --> uc5
    user --> uc6
    user --> uc7
    user --> uc8
    parent --> uc9
    admin --> uc10
```

## 3. Data Flow Diagram

```mermaid
flowchart LR
    ext1["Visitor / User"] --> p1["P1 Authentication"]
    p1 --> d1[("D1 User Account Store")]
    p1 --> p2["P2 Profile Management"]
    p2 --> d2[("D2 Profile Store")]
    p2 --> p3["P3 Behavior Collection"]
    p3 --> d3[("D3 Behavior Summary Store")]
    d2 --> p4["P4 Focus Personalization"]
    d3 --> p4
    p4 --> d4[("D4 Focus Plan Store")]
    p4 --> d5[("D5 Insight and Trend Store")]
    d4 --> p5["P5 User Dashboard"]
    d5 --> p5
    p5 --> ext1
    ext2["Parent"] --> p6["P6 Guardian Monitoring"]
    d2 --> p6
    d5 --> p6
    p6 --> ext2
```

## 4. Activity Diagram

```mermaid
flowchart TD
    A["Open Bboo"] --> B["Create account or sign in"]
    B --> C["Enter important profile data"]
    C --> D["Choose permission tracking or manual input"]
    D --> E["Create behavior baseline"]
    E --> F["Generate dashboard, graphs, and plan"]
    F --> G{"High distraction risk?"}
    G -->|Yes| H["Trigger intervention and attention game"]
    G -->|No| I["Continue standard recovery plan"]
    H --> J["Complete session"]
    I --> J
    J --> K["Update habits and graphs"]
    K --> L["Review insights"]
```

## 5. State Diagram

```mermaid
stateDiagram-v2
    [*] --> Visitor
    Visitor --> Authenticated: Account created or login success
    Authenticated --> ProfilePending: Session started
    ProfilePending --> ProfileReady: Important data completed
    ProfileReady --> Monitoring: Baseline created
    Monitoring --> Focused: Low risk
    Monitoring --> Overloaded: High risk
    Overloaded --> Intervention: Shield activated
    Intervention --> Recovering: Session completed
    Recovering --> Focused: Trend improves
    Focused --> Monitoring: Recheck
    Monitoring --> ParentReview: Child account linked
    ParentReview --> Monitoring: Guidance delivered
```

## 6. Class Diagram

```mermaid
classDiagram
    class Account {
      +UUID accountId
      +string email
      +string passwordHash
      +signIn()
      +signOut()
    }

    class Profile {
      +UUID profileId
      +string firstName
      +string lastName
      +string country
      +string preferredLanguage
      +completeProfile()
    }

    class BehaviorSummary {
      +UUID summaryId
      +int dailyNotifications
      +float socialMediaHours
      +float sleepHours
      +capture()
    }

    class FocusDashboard {
      +UUID dashboardId
      +int focusScore
      +renderGraphs()
    }

    class FocusPlan {
      +UUID planId
      +int sessionMinutes
      +generate()
    }

    class Guardian {
      +UUID guardianId
      +monitorChild()
    }

    class ChildProfile {
      +UUID childId
      +linkGuardian()
    }

    Account "1" --> "1" Profile
    Profile "1" --> "0..*" BehaviorSummary
    Profile "1" --> "0..1" FocusDashboard
    Profile "1" --> "0..*" FocusPlan
    Guardian "1" --> "0..*" ChildProfile
    ChildProfile --|> Profile
```

## 7. ERD

```mermaid
erDiagram
    ACCOUNTS {
        uuid account_id PK
        string email
        string password_hash
        datetime created_at
        string account_status
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
    }

    GUARDIANS {
        uuid guardian_id PK
        uuid profile_id FK
        string relationship_type
    }

    CHILD_PROFILES {
        uuid child_profile_id PK
        uuid profile_id FK
        uuid guardian_id FK
    }

    BEHAVIOR_SUMMARIES {
        uuid summary_id PK
        uuid profile_id FK
        int daily_notifications
        decimal social_media_hours
        decimal sleep_hours
        int planning_consistency
        datetime captured_at
    }

    FOCUS_PLANS {
        uuid plan_id PK
        uuid profile_id FK
        int session_minutes
        string focus_theme
        datetime generated_at
    }

    INSIGHTS {
        uuid insight_id PK
        uuid profile_id FK
        string title
        string action_text
        datetime generated_at
    }

    INTERVENTIONS {
        uuid intervention_id PK
        uuid profile_id FK
        string intervention_type
        string trigger_reason
        datetime triggered_at
    }

    DASHBOARD_SNAPSHOTS {
        uuid snapshot_id PK
        uuid profile_id FK
        int focus_score
        string state_label
        datetime generated_at
    }

    ACCOUNTS ||--|| PROFILES : owns
    PROFILES ||--o| GUARDIANS : can_be
    GUARDIANS ||--o{ CHILD_PROFILES : supervises
    PROFILES ||--o{ CHILD_PROFILES : extends
    PROFILES ||--o{ BEHAVIOR_SUMMARIES : produces
    PROFILES ||--o{ FOCUS_PLANS : receives
    PROFILES ||--o{ INSIGHTS : receives
    PROFILES ||--o{ INTERVENTIONS : triggers
    PROFILES ||--o{ DASHBOARD_SNAPSHOTS : generates
```
