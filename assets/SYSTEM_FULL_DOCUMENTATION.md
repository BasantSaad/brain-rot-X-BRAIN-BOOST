# Bboo System Documentation

## 1. System brief

Bboo is a web-based anti-distraction and focus-recovery system.

Its job is to:

- create and manage user accounts
- store profile and behavior data in MySQL
- generate focus dashboards and plans
- track check-ins, timers, app usage, summaries, and guardian links
- provide an assistant layer that can update the system through natural-language commands

The project currently contains two backend entry styles:

- a working lightweight HTTP server in `app.py`
- a newer architecture entrypoint in `api_fastapi.py`

The live user-facing site uses static HTML/CSS/JS pages and talks to backend API endpoints with a bearer-token session.

---

## 2. High-level architecture

The system now follows the layered design below.

```text
User
  ->
Frontend Pages (HTML/CSS/JS)
  ->
API Layer (app.py or api_fastapi.py)
  ->
Service Layer (services/app_service.py)
  ->
Agent Layer (agent/langgraph_runtime.py)
  ->
Tool Layer (agent/tools.py)
  ->
Repository Layer (storage/mysql_repository.py)
  ->
MySQL

Also alongside the agent:
Embedding Layer (agent/embeddings.py)
  ->
Retrieval Store / RAG Layer (agent/rag_store.py)
  ->
Ollama / Qwen Planner (agent/ollama_client.py)
```

---

## 3. Architecture by layer

### 3.1 Frontend layer

This is the user interface layer.

Main responsibilities:

- show login and dashboard pages
- let the user edit settings and plans
- let the user track app usage, check-ins, and timers
- provide the floating assistant on all pages
- send authenticated API requests using the saved bearer token

Main files:

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

### 3.2 API layer

This is the entrypoint layer for requests.

There are two versions:

- `app.py`
  - current lightweight server using Python `http.server`
  - handles all working routes for the live project
- `api_fastapi.py`
  - newer architecture version using FastAPI
  - currently demonstrates the cleaner target architecture

Main responsibilities:

- receive HTTP requests
- validate basic request structure
- require session authentication
- call service or agent logic
- return JSON responses or static files

### 3.3 Service layer

This layer centralizes business operations that should not live inside route handlers.

Main file:

- `services/app_service.py`

Main responsibilities:

- build dashboard payloads
- build plan payloads
- update settings fields
- build user profiles from stored data or simulated fallback
- apply reactive behavior signals from real tracked data

### 3.4 Agent layer

This is the decision layer for assistant behavior.

Main files:

- `agent/langgraph_runtime.py`
- `agent/assistant_engine.py`

Current status:

- `langgraph_runtime.py` is the active agent runtime
- `assistant_engine.py` is an older assistant implementation kept in the project as an earlier step

Main responsibilities of `langgraph_runtime.py`:

- receive the user message
- retrieve context from the RAG layer
- plan the action
- choose the correct tool
- execute the tool
- compose the final assistant reply

Important behavior:

- direct command rules run first for safety
- Ollama/Qwen is used as planner when configured
- if the model fails, the local rule planner is used as fallback

### 3.5 Tool layer

This layer exposes safe actions the agent is allowed to run.

Main file:

- `agent/tools.py`

Current tools:

- `get_dashboard_summary`
- `get_weekly_summary`
- `get_suggestions`
- `get_app_usage_summary`
- `update_session_minutes`
- `update_app_name`
- `update_bedtime_target`
- `update_sleep_target_hours`
- `start_focus_timer`
- `stop_focus_timer`

Why this layer matters:

- the agent never writes SQL directly
- the agent only calls approved tool functions
- tools call repository/service methods safely

### 3.6 Embedding and retrieval layer

This layer plays the role of the “Embedding model + Chroma / RAG” part of your architecture.

Main files:

- `agent/embeddings.py`
- `agent/rag_store.py`

Current implementation:

- `embeddings.py`
  - provides a small local text-vector style embedding utility
- `rag_store.py`
  - stores knowledge documents and retrieves the most relevant ones

Current note:

- this is a local lightweight version, not a real external Chroma server yet
- functionally, it already acts like a retrieval layer in the architecture

### 3.7 LLM layer

This is the model-planning layer.

Main file:

- `agent/ollama_client.py`

Current model flow:

- Ollama runs locally on `http://127.0.0.1:11434`
- model configured in `.env`
- current target model: `qwen2.5:7b-instruct`

Main responsibilities:

- send a planning prompt to Ollama
- ask the model to return strict JSON
- let the model choose the intent, tool name, and tool arguments

### 3.8 Repository and database layer

This is the persistence layer.

Main files:

- `storage/mysql_repository.py`
- `storage/schema.sql`

Main responsibilities:

- create tables
- authenticate users
- manage sessions
- read and write settings
- save plans and plan history
- manage check-ins and timers
- save app usage
- generate weekly summaries and suggestions
- save dashboard snapshots
- store agent conversations, messages, and action logs

### 3.9 Domain model layer

This layer contains structured data contracts.

Main file:

- `shared/schemas.py`

Main objects:

- `AccountProfile`
- `UserProfile`
- `FocusMetric`
- `HabitCard`
- `InsightCard`
- `ParentGuidance`
- `ProfileField`
- `TrendPoint`
- `ChartSeries`
- `DashboardSnapshot`
- `FocusPlan`

### 3.10 Simulator layer

This layer creates fallback/generated profile data when needed.

Main file:

- `simulator/behavior_simulator.py`

Main responsibilities:

- create user behavior baselines
- generate values like notifications, social media hours, sleep, planning consistency
- support the focus engine when real tracked data is incomplete

### 3.11 Focus engine layer

This layer builds the dashboard and plan logic.

Main file:

- `agent/focus_engine.py`

Main responsibilities:

- calculate focus score
- derive brain state
- generate dashboard cards, metrics, habits, charts, and insights
- generate personalized focus recovery plans

---

## 4. Workflow of the system

## 4.1 Authentication workflow

1. User opens `index.html`.
2. `auth.js` shows create-account or login form.
3. Frontend sends request to `/api/register` or `/api/login`.
4. Backend validates input.
5. `mysql_repository.py` creates or authenticates the user.
6. A session token is created in `user_sessions`.
7. Frontend stores the session in `localStorage` as `bboo-session`.
8. User is redirected to `dashboard.html`.

## 4.2 Dashboard workflow

1. `dashboard.js` reads `bboo-session`.
2. It calls:
   - `/api/profile`
   - `/api/dashboard`
   - `/api/plan`
   - and page-specific endpoints such as settings, summaries, timers, check-ins, app usage, suggestions
3. `app.py` or `api_fastapi.py` receives the request.
4. `BbooAppService` builds the needed payload.
5. `focus_engine.py` builds dashboard content.
6. `mysql_repository.py` reads or writes MySQL data.
7. Frontend renders the result into cards, charts, forms, and lists.

## 4.3 Assistant workflow

This is the most important workflow for the new architecture.

1. User types a message in the assistant UI.
2. Frontend sends `POST /api/agent/chat`.
3. Backend validates the session.
4. The message is stored in `agent_messages`.
5. `langgraph_runtime.py` starts the assistant workflow.
6. The runtime retrieves knowledge from `rag_store.py`.
7. The runtime decides the action:
   - direct rule first for explicit commands
   - otherwise Ollama/Qwen planner
   - otherwise local fallback planner
8. The runtime chooses a tool from `agent/tools.py`.
9. The tool executes service or repository logic.
10. The result is stored in `agent_action_logs`.
11. The assistant reply is saved in `agent_messages`.
12. Backend returns:
   - assistant reply
   - updated conversation history
   - updated settings
   - refreshed dashboard
13. Frontend updates the visible system state across pages.

## 4.4 Timer workflow

### Start timer

1. User says: `start a focus timer for 30 minutes`
2. Agent runtime forces `start_focus_timer`
3. Tool calls repository `start_focus_timer`
4. Repository inserts into `focus_timer_sessions`
5. Frontend reloads timer history

### Stop timer

1. User says: `stop it`
2. Agent runtime forces `stop_focus_timer`
3. Tool fetches active timer using `active_timer`
4. Tool calls repository `complete_focus_timer`
5. Timer becomes closed in DB
6. Frontend reloads timer history

## 4.5 App usage workflow

1. User saves app usage from `usage.html`
2. Frontend calls `POST /api/app-usage`
3. Repository upserts into `app_usage_logs`
4. Dashboard and weekly summary are refreshed
5. Charts and focus score react to the new behavior data

---

## 5. Mapping your requested architecture to this project

Your requested architecture:

```text
Embedding Model
  ->
Chroma / RAG
  ->
Retrieved Context
  ->
LangGraph Agent
  ->
Qwen 3.5
  ->
Tool / Action Selection
  ->
Action Layer
  ->
Execution Layer
  ->
FastAPI
  ->
CMS / MYSQL
```

Current Bboo mapping:

- Embedding Model
  - `agent/embeddings.py`
- Chroma / RAG
  - `agent/rag_store.py`
  - local lightweight replacement for now
- Retrieved Context
  - produced in `langgraph_runtime.py`
- LangGraph Agent
  - `agent/langgraph_runtime.py`
  - graph-style state workflow
- Qwen
  - `agent/ollama_client.py`
  - Ollama model: `qwen2.5:7b-instruct`
- Tool / Action Selection
  - `agent/tools.py`
- Action Layer
  - `agent/tools.py`
- Execution Layer
  - `services/app_service.py`
  - `storage/mysql_repository.py`
- FastAPI
  - `api_fastapi.py`
- CMS / MYSQL
  - MySQL is implemented
  - a full CMS is not implemented as a separate product yet
  - retrieval documents are currently code-defined in `rag_store.py`

---

## 6. File-by-file explanation

## 6.1 Root files

### `app.py`

Purpose:

- main working backend server using Python `http.server`

What it does:

- loads environment variables
- creates repository, service, and agent objects
- serves static frontend files
- exposes API routes for auth, dashboard, plans, settings, check-ins, timers, app usage, guardian links, and assistant chat

Important functions:

- `load_dotenv`
- `BbooRequestHandler.do_GET`
- `BbooRequestHandler.do_POST`
- `BbooRequestHandler.do_PUT`
- `_handle_dashboard`
- `_handle_plan`
- `_handle_agent_chat`
- `_require_session`

### `api_fastapi.py`

Purpose:

- newer architecture entrypoint using FastAPI

What it does:

- initializes repository, service, and agent runtime
- serves static pages
- provides `POST /api/agent/chat`
- provides `GET /api/agent/history`
- provides health endpoint

Why it exists:

- this file is the transition toward the cleaner future architecture

### `README.md`

Purpose:

- project setup guide

What it contains:

- local Python run steps
- XAMPP/MySQL setup
- Docker notes
- project overview

### `ARCHITECTURE.md`

Purpose:

- earlier architecture overview document for the app

### `requirements.txt`

Purpose:

- Python dependencies list

Current important packages:

- `mysql-connector-python`
- `fastapi`
- `uvicorn`

### `Dockerfile`

Purpose:

- builds a Docker image for the app

### `docker-compose.yml`

Purpose:

- runs the app and MySQL together in Docker

### `.env.example`

Purpose:

- example environment configuration

Important variables:

- DB connection values
- session TTL
- Ollama provider settings

---

## 6.2 `agent/` files

### `agent/focus_engine.py`

Purpose:

- business intelligence for focus scoring and dashboard generation

What it contains:

- focus score formula
- dashboard metric generation
- habits and insights generation
- plan generation

### `agent/langgraph_runtime.py`

Purpose:

- active assistant runtime

What it contains:

- `GraphState`
- retrieval step
- planning step
- direct command forcing
- Ollama planning
- fallback planning
- tool execution
- reply composition

Why it matters:

- this is the main “brain controller” of the assistant

### `agent/tools.py`

Purpose:

- safe tool registry for assistant actions

What it contains:

- tool definitions
- tool handler functions
- user-safe updates and reads

### `agent/ollama_client.py`

Purpose:

- connects Bboo to Ollama

What it does:

- sends planning prompts to your local Qwen model
- expects strict JSON response
- returns intent, tool name, tool args, and reply

### `agent/rag_store.py`

Purpose:

- retrieval store for assistant knowledge

What it contains:

- seeded knowledge documents
- query logic
- document scoring

### `agent/embeddings.py`

Purpose:

- lightweight local embedding/similarity model

What it does:

- tokenizes text
- builds simple vector-like counts
- calculates similarity scores

### `agent/assistant_engine.py`

Purpose:

- older assistant implementation kept from a previous iteration

Current status:

- not the main active runtime anymore

### `agent/__init__.py`

Purpose:

- package marker file

---

## 6.3 `services/` files

### `services/app_service.py`

Purpose:

- central service layer between routes and repository

What it does:

- builds dashboard payloads
- builds plan payloads
- updates single settings fields
- creates reactive profiles from real usage signals

### `services/__init__.py`

Purpose:

- package marker file

---

## 6.4 `storage/` files

### `storage/mysql_repository.py`

Purpose:

- full MySQL persistence layer

What it does:

- initializes database and tables
- user create/login/session handling
- profile read/update
- settings read/update
- plan save/history
- check-ins
- focus timers
- app usage
- dashboard snapshots
- guardian links
- weekly summaries
- suggestions
- agent conversations/messages/actions

Important methods:

- `initialize`
- `create_user`
- `authenticate_user`
- `load_session`
- `load_settings`
- `update_settings`
- `save_focus_plan`
- `load_plan_history`
- `record_checkin`
- `start_focus_timer`
- `complete_focus_timer`
- `active_timer`
- `recent_timers`
- `save_app_usage`
- `app_usage_summary`
- `app_usage_detail`
- `weekly_summary`
- `suggestion_engine`
- `ensure_agent_conversation`
- `record_agent_message`
- `record_agent_action`
- `agent_history`

### `storage/schema.sql`

Purpose:

- SQL schema export for manual DB creation/import

Main tables described there:

- `users`
- `behavior_profiles`
- `focus_plans`
- `user_sessions`
- `app_settings`
- `daily_checkins`
- `focus_timer_sessions`
- `app_usage_logs`
- `dashboard_snapshots`
- `guardian_links`
- `agent_conversations`
- `agent_messages`
- `agent_action_logs`

### `storage/__init__.py`

Purpose:

- package marker file

---

## 6.5 `shared/` files

### `shared/schemas.py`

Purpose:

- data model contracts

What it contains:

- account profile classes
- dashboard and chart classes
- plan classes
- shared serialization helpers

### `shared/topics.py`

Purpose:

- small helper for API route naming

### `shared/__init__.py`

Purpose:

- package marker file

---

## 6.6 `simulator/` files

### `simulator/behavior_simulator.py`

Purpose:

- creates simulated user behavior when real tracked data is not enough

What it generates:

- notifications
- social hours
- sleep hours
- planning consistency
- completed focus sessions

### `simulator/__init__.py`

Purpose:

- package marker file

---

## 6.7 `static/` files

### `static/index.html`

Purpose:

- login / register landing page

### `static/auth.js`

Purpose:

- handles authentication forms

What it does:

- create account submission
- login submission
- language switching
- stores session in `localStorage`
- redirects to dashboard

### `static/dashboard.js`

Purpose:

- shared frontend controller for all dashboard-related pages

What it does:

- loads dashboard/profile/plan/settings/check-ins/timers/usage/summaries
- renders cards and charts
- handles plan editing
- handles settings save
- handles check-ins and timers
- handles guardian linking
- handles app usage
- handles assistant page
- handles floating assistant dock across the entire site

This is one of the most important frontend files.

### `static/styles.css`

Purpose:

- global visual system

What it contains:

- page shell layout
- glassmorphism styling
- sidebar styling
- dashboard card styles
- charts and usage bars
- assistant page styles
- floating assistant dock styles

### `static/dashboard.html`

Purpose:

- main overview page after login

### `static/usage.html`

Purpose:

- app usage page

### `static/profile.html`

Purpose:

- profile and settings page

### `static/summary.html`

Purpose:

- weekly summary and suggestion page

### `static/checkins.html`

Purpose:

- check-ins and focus timer page

### `static/plan.html`

Purpose:

- plan and habits page

### `static/insights.html`

Purpose:

- insights and guardian page

### `static/assistant.html`

Purpose:

- dedicated full assistant page

### `static/icon.svg`

Purpose:

- app icon

---

## 7. Database table overview

Main system tables:

- `users`
  - account identity and auth fields
- `behavior_profiles`
  - behavior baseline
- `focus_plans`
  - current plan
- `focus_plan_history`
  - previous saved plans
- `user_sessions`
  - bearer-token login sessions
- `app_settings`
  - app name, bedtime, study time, default session time
- `daily_checkins`
  - mood and energy logs
- `focus_timer_sessions`
  - started/completed/stopped timers
- `dashboard_snapshots`
  - stored focus score history
- `app_usage_logs`
  - app usage by day
- `guardian_links`
  - parent-child links
- `agent_conversations`
  - assistant conversation groups
- `agent_messages`
  - assistant/user messages
- `agent_action_logs`
  - tool execution log

---

## 8. Tools used in each layer

### Frontend layer tools

- browser `fetch`
- `localStorage`
- shared DOM rendering functions in `dashboard.js`

### API layer tools

- Python `http.server` in `app.py`
- FastAPI in `api_fastapi.py`

### Service layer tools

- `BbooAppService`

### Agent layer tools

- `LocalLangGraphAgent`
- direct command parser
- Ollama planner
- fallback local planner

### Retrieval layer tools

- `SimpleEmbeddingModel`
- `LocalChromaStore`

### LLM layer tools

- Ollama local API
- Qwen model: `qwen2.5:7b-instruct`

### Action layer tools

- `BbooToolRegistry`
- tool handlers:
  - dashboard read
  - summary read
  - suggestions read
  - app usage read
  - settings update
  - timer start
  - timer stop

### Execution layer tools

- `BbooAppService`
- `MySQLRepository`

### Persistence layer tools

- MySQL
- SQL schema and repository methods

---

## 9. Current strengths of the system

- real MySQL-backed data flow
- session-based authentication
- separate pages with shared logic
- reactive dashboard tied to usage and timer behavior
- assistant integrated across the whole app
- action logging for assistant behavior
- Ollama/Qwen support
- future-ready FastAPI architecture path

---

## 10. Current limitations

- retrieval store is local code-based, not real external Chroma yet
- assistant still uses a hybrid rule + model system for safety
- `api_fastapi.py` is not yet a full replacement for every route in `app.py`
- a standalone CMS is not implemented yet
- some older files remain from previous iterations for continuity

---

## 11. Recommended next improvements

- migrate all routes fully from `app.py` to `api_fastapi.py`
- expand tool set:
  - check-in creation by chat
  - app usage add/edit by chat
  - plan editing by chat
- move RAG documents into MySQL or file-based content store
- add real Chroma or vector DB if needed
- add agent memory summarization
- add explicit action confirmation for sensitive commands
- add unit tests for tool selection and repository operations

---

## 12. Final summary

Bboo is now a layered web system with:

- frontend pages
- backend APIs
- service layer
- focus intelligence
- MySQL persistence
- assistant workflow
- retrieval layer
- Ollama/Qwen planning
- tool-based action execution

This means the project is no longer only a static dashboard prototype.
It is now a structured application architecture that can keep growing into a full intelligent assistant system.
