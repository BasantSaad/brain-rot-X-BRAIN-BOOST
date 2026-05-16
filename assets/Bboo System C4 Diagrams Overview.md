# Bboo System C4 Diagrams Overview

This document provides a comprehensive set of C4 model diagrams for the Bboo Focus-Recovery System, based on the provided technical documentation.

## 1. Level 1: System Context

The **System Context** diagram illustrates the Bboo system at the highest level of abstraction, positioning it within its operational environment. It defines the system's boundaries and its relationships with human users and external technical dependencies.

| Entity | Type | Description |
| :--- | :--- | :--- |
| **User** | Person | Individuals seeking to improve focus and reduce distractions through the platform. |
| **Bboo System** | Software System | The core application providing dashboards, plans, and AI assistant features. |
| **Ollama / LLM** | External System | A local service running the Qwen model for planning and natural language processing. |
| **MySQL Database** | External System | The persistent storage engine for user profiles, behavior logs, and application state. |
| **Guardian** | External Person | Parents or mentors who interact with the system via focus insight links. |

## 2. Level 2: Container

The **Container** diagram provides a more detailed view by decomposing the Bboo system into its primary technical containers. Each container represents a separately deployable unit that fulfills a specific role within the architecture.

| Container | Technology | Responsibility |
| :--- | :--- | :--- |
| **Web Application** | HTML, CSS, JavaScript | Delivers the user interface for dashboards, focus plans, and the assistant dock. |
| **API Service** | Python (FastAPI) | Orchestrates HTTP requests, handles authentication, and manages business logic. |
| **Agent Runtime** | Python (LangGraph) | Manages the assistant's state machine, including retrieval, planning, and execution. |
| **Database** | MySQL | Provides persistent storage for all structured data and historical logs. |

## 3. Level 3: Component

The **Component** diagram zooms into the backend services to reveal the internal modular structure. It shows how the logic is partitioned into distinct layers to ensure separation of concerns and maintainability.

| Component | Responsibility | Key Interactions |
| :--- | :--- | :--- |
| **API Layer** | Request routing and session validation. | Calls Service Layer and Agent Runtime. |
| **Service Layer** | Orchestrates high-level business operations. | Interacts with Focus Engine and Repository. |
| **Agent Runtime** | Controls the assistant workflow and state. | Uses RAG Layer, Ollama, and Tool Layer. |
| **Focus Engine** | Calculates focus metrics and generates plans. | Provides data to the Service Layer. |
| **Tool Layer** | Defines and executes safe agent actions. | Calls Service and Repository methods. |
| **RAG Layer** | Manages knowledge retrieval and embeddings. | Supplies context to the Agent Runtime. |
| **Repository Layer** | Abstracts MySQL database operations. | Performs SQL queries on the Database. |

## 4. Level 4: Code (Assistant Workflow)

The **Code** level is represented through a sequence diagram that details the most critical workflow in the system: the **Assistant Chat Interaction**. This diagram maps the specific logic path from the initial user input to the final response, highlighting the interplay between the agent runtime, the retrieval system, and the external LLM.

The workflow begins with a user message being passed through the API to the **LangGraph Runtime**. The system then performs a RAG retrieval to gather relevant context before consulting the **Ollama** model for a plan. Once a tool is selected and executed, the results are persisted in the repository, and a comprehensive response is returned to the frontend.
