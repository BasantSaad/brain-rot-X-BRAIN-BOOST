# Bboo DFD and C4 Diagrams

This file contains the Data Flow Diagram views and C4 architecture views for the Bboo system.

---

## 1. DFD Level 0

```mermaid
flowchart LR
    User["User / Parent"] -->|"Register, login, requests, assistant commands"| Bboo["Bboo System"]
    Bboo -->|"Dashboard, plans, summaries, assistant replies"| User
    Bboo -->|"Read / write operational data"| MySQL["MySQL Database"]
    Bboo -->|"Planner prompts"| Ollama["Ollama + Qwen"]
    Ollama -->|"Intent + tool plan"| Bboo
    Bboo -->|"Retrieve knowledge context"| RAG["Local RAG Store"]
    RAG -->|"Relevant guidance context"| Bboo
```

### Explanation

- The external actor is the user or guardian.
- The core process is the Bboo System.
- The main data stores and integrations are MySQL, Ollama/Qwen, and the local RAG store.

---

## 2. DFD Level 1

```mermaid
flowchart TB
    User["User / Parent"]

    Auth["1.0 Authentication and Session Management"]
    Dashboard["2.0 Dashboard and Plan Generation"]
    Tracking["3.0 Tracking and Behavior Logging"]
    Assistant["4.0 Assistant and Tool Execution"]
    Repo["5.0 Repository and Persistence"]

    MySQL["D1 MySQL Database"]
    Ollama["E1 Ollama / Qwen"]
    RAG["D2 Retrieval Knowledge Store"]

    User -->|"Register / Login"| Auth
    Auth -->|"Session token"| User
    Auth -->|"Users, sessions"| Repo

    User -->|"Open dashboard / pages"| Dashboard
    Dashboard -->|"Dashboard, plans, summaries"| User
    Dashboard -->|"Load profile, settings, plans, summaries"| Repo

    User -->|"Check-ins, timers, app usage"| Tracking
    Tracking -->|"Updated records and feedback"| User
    Tracking -->|"Save timers, usage, check-ins"| Repo

    User -->|"Natural language request"| Assistant
    Assistant -->|"Assistant reply"| User
    Assistant -->|"Retrieve context"| RAG
    RAG -->|"Relevant knowledge"| Assistant
    Assistant -->|"Planning prompt"| Ollama
    Ollama -->|"Intent and tool plan"| Assistant
    Assistant -->|"Execute safe tool actions"| Repo

    Repo <--> MySQL
```

### Explanation

- `1.0 Authentication and Session Management` handles account access and tokens.
- `2.0 Dashboard and Plan Generation` builds the visible analytics and plans.
- `3.0 Tracking and Behavior Logging` stores app usage, timers, and check-ins.
- `4.0 Assistant and Tool Execution` handles the agent workflow.
- `5.0 Repository and Persistence` is the database access layer.

---

## 3. DFD Level 2 for Assistant Workflow

```mermaid
flowchart TB
    User["User"]
    API["Assistant API Endpoint"]
    History["Conversation Logging"]
    Retrieve["Retrieve Context"]
    Plan["Intent and Tool Planning"]
    Tools["Tool Selection"]
    Execute["Tool Execution"]
    Refresh["Refresh Dashboard State"]

    MySQL["MySQL"]
    RAG["Local RAG Store"]
    Ollama["Ollama / Qwen"]

    User -->|"Message"| API
    API -->|"Store user message"| History
    History --> MySQL

    API --> Retrieve
    Retrieve --> RAG
    RAG -->|"Context documents"| Retrieve

    Retrieve --> Plan
    Plan -->|"Planner request"| Ollama
    Ollama -->|"JSON plan"| Plan

    Plan --> Tools
    Tools --> Execute
    Execute --> MySQL

    Execute --> Refresh
    Refresh --> MySQL
    Refresh --> API
    API -->|"Assistant reply + refreshed state"| User
```

### Explanation

- The assistant does not write SQL directly.
- It retrieves context, asks the planner, selects a tool, runs the tool, then refreshes the returned system state.

---

## 4. C4 Context Diagram

```mermaid
flowchart LR
    User["User"]
    Parent["Parent / Guardian"]
    Bboo["Bboo Focus Recovery System"]
    MySQL["MySQL Database"]
    Ollama["Ollama with Qwen Model"]

    User -->|"Uses web app, tracks focus, talks to assistant"| Bboo
    Parent -->|"Views guidance and linked child summaries"| Bboo
    Bboo -->|"Stores users, plans, timers, usage, sessions, logs"| MySQL
    Bboo -->|"Requests tool planning and reply support"| Ollama
```

### Explanation

- This shows the system as one product and how it interacts with its external actors and systems.

---

## 5. C4 Container Diagram

```mermaid
flowchart TB
    User["User / Parent Browser"]

    Frontend["Frontend Pages\nHTML + CSS + JavaScript"]
    AppServer["Application Server\napp.py or api_fastapi.py"]
    Service["Service Layer\nservices/app_service.py"]
    Agent["Agent Runtime\nlanggraph_runtime.py"]
    ToolLayer["Tool Registry\nagent/tools.py"]
    RAG["RAG Layer\nembeddings.py + rag_store.py"]
    Planner["Model Planner\nollama_client.py -> Ollama/Qwen"]
    Repo["Repository Layer\nmysql_repository.py"]
    DB["MySQL Database"]

    User --> Frontend
    Frontend --> AppServer
    AppServer --> Service
    AppServer --> Agent
    Agent --> RAG
    Agent --> Planner
    Agent --> ToolLayer
    ToolLayer --> Service
    Service --> Repo
    Repo --> DB
```

### Explanation

- The browser talks to the frontend.
- The frontend calls the application server.
- The application server delegates to services and the assistant runtime.
- The assistant runtime uses retrieval, planner, and tools.
- Repository handles database persistence.

---

## 6. C4 Component Diagram for Agent Container

```mermaid
flowchart LR
    API["Assistant API Handler"]
    Runtime["LocalLangGraphAgent"]
    Rules["Direct Command Rules"]
    Planner["OllamaPlannerClient"]
    Retrieve["LocalChromaStore"]
    Embed["SimpleEmbeddingModel"]
    Registry["BbooToolRegistry"]
    Service["BbooAppService"]
    Repo["MySQLRepository"]

    API --> Runtime
    Runtime --> Rules
    Runtime --> Planner
    Runtime --> Retrieve
    Retrieve --> Embed
    Runtime --> Registry
    Registry --> Service
    Service --> Repo
```

### Explanation

- The agent container contains multiple internal components.
- Direct rules handle explicit commands safely.
- Ollama planner handles flexible model reasoning.
- Retrieval adds helpful context.
- Tools provide the only allowed execution path.

---

## 7. C4 Code-Level Mapping

### Frontend container

- `static/index.html`
- `static/auth.js`
- `static/dashboard.js`
- `static/styles.css`
- `static/dashboard.html`
- `static/usage.html`
- `static/profile.html`
- `static/summary.html`
- `static/checkins.html`
- `static/plan.html`
- `static/insights.html`
- `static/assistant.html`

### Application server container

- `app.py`
- `api_fastapi.py`

### Service container

- `services/app_service.py`

### Agent container

- `agent/langgraph_runtime.py`
- `agent/tools.py`
- `agent/ollama_client.py`
- `agent/rag_store.py`
- `agent/embeddings.py`

### Business intelligence container

- `agent/focus_engine.py`
- `simulator/behavior_simulator.py`

### Persistence container

- `storage/mysql_repository.py`
- `storage/schema.sql`

### Shared domain contracts

- `shared/schemas.py`

---

## 8. How to Use These Diagrams in Presentation

- Use DFD Level 0 for quick explanation of the whole system.
- Use DFD Level 1 for process breakdown.
- Use DFD Level 2 for assistant workflow.
- Use C4 Context to explain product boundaries.
- Use C4 Container to explain major technical blocks.
- Use C4 Component to explain how the assistant works internally.
