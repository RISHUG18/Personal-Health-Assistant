# Project Plan

## Project Information

| Field | Details |
|-------|---------|
| **Project Number** | 48 |
| **Project Title** | Gen AI driven Wellbeing Coach and Health Management Platform |
| **Document** | Project Plan |
| **Creation Date** | 11th February |
| **Created By** | Rishabh Goyal, Aditya Singh, Tanush Garg, Avnish Uba, Sashi Kumar Gudipati |
| **Client** | Teja Vardhan Podipireddy (SuryaQuantum AI) |

## Problem Statement

People struggle to understand their overall health because their fitness data (from apps and devices) and medical records (often in PDFs or paper reports) are scattered across different platforms. There is no unified system that combines these sources and analyzes them with external factors to provide clear, personalized guidance. Additionally, doctors lack an efficient way to monitor patients between visits and often face overwhelming raw data without concise summaries or priority alerts.

## Team Members and Responsibilities

- **Rishabh Goyal** — Responsible for designing and managing structured data models, implementing the rules engine, and defining metadata schemas for Retrieval-Augmented Generation (RAG).

- **Avnish Uba** — Leads the RAG ingestion pipeline, including data cleaning, document chunking strategies, embedding generation, and management of the vector database.

- **Tanush Garg** — Oversees RAG retrieval logic and context construction, integrates the Gemini large language model, and connects external environment and contextual data APIs.

- **Aditya Singh** — Develops the core user interface, handles backend API integration, implements observability and monitoring, and ensures explainable and transparent user experiences.

- **Sashi Kumar Gudipati** — Supports auxiliary and secondary user interfaces, conducts quality assurance and testing, and prepares project demonstrations and validation scenarios.

## Team Communication

Our team will meet once a week based on the project's weekly requirements to review progress and plan tasks.

## Development Environment

The project is developed using Python as the primary programming language, with FastAPI for backend API development and React for building interactive patient and doctor dashboards. Version control is managed through a Git-based workflow, and structured technical documentation supports system design and requirements tracking.

The AI pipeline incorporates:
- Google Gemini 2.5 Flash for generating explanations and summaries
- BAAI/bge-base-en-v1.5 embedding model for semantic search
- Tesseract OCR for extracting text from medical reports

A custom Retrieval-Augmented Generation (RAG) pipeline is implemented, using FAISS for development-phase vector search and pgvector (Supabase extension) in production. The system uses Supabase PostgreSQL as the primary database, with Supabase Storage for securely storing medical report PDFs.

External integrations include:
- OpenWeatherMap API and OpenWeather Air Pollution API for environmental health context
- Planned integration of Google Health Connect for wearable and mobile health data synchronization

## Milestone Schedule (Updated From Final Status Tracker)

### Week 1: Planning and Requirements — Completed

Completed MVP definition, initial client meeting, MVP refinement, and weekly team planning.

### Week 2: Core Foundation Setup — Completed

Completed database setup, PDF upload flow, prompt/context drafting, OCR implementation/testing, retrieval stubs, API contracts, and mock frontend/backend alignment tasks.

### Week 3: Initial RAG Build and Extraction Sprint — Partially Completed

Completed endpoint fixes, extraction normalization and insertion into lab_results, baseline RAG understanding, query embedding function, and Supabase OCR pipeline connection. One coordination activity remained marked ongoing, and several RAG tasks were delayed in this week and moved forward.

### Week 4: Integration Catch-up and UI/API Wiring — Completed

Completed delayed vector similarity work, Android-to-backend endpoint adapter integration, alert object additions, UI sample improvements, SRS, and meeting documentation.

### Week 5: RAG Stabilization and App Feature Expansion — Mostly Completed

Completed context builder, metadata improvements, RAG query endpoint, Gemini response integration, retrieval optimization, report-processing integration, dashboard/profile/settings expansion, endpoint integration, and voice endpoint improvements. Two testing tasks were still marked ongoing in this week.

### Week 6: Wearables, Auth, and Mobile Core Flows — Completed

Completed environment API integration, wearable backend pipeline, scheduled jobs (wearables/environment), user authentication pipeline, upload/login/register/dashboard/alerts app integrations, reports endpoint support, and end-to-end voice pipeline integration.

### Week 7: Doctor Features, Summaries, and Voice Reliability — Completed

Completed end-to-end summary generation (user/doctor), nightly alert cron, voice chat to RAG integration, FAISS fallback, doctor dashboard endpoints and UI, GDPR-related backend updates, wearable alert objects, and additional test-data standardization.

### Week 8: Final Feature Closure and Hardening — Completed

Completed UI graph improvements for wearable data, report deletion endpoint, report upload status websocket support, PDF validator, longitudinal lab search, discrete wearable ingestion, doctor dashboard AI chat updates, monthly/quarterly summarizer work, and health-connect vitals extraction/display fixes.

## Milestone Timeline (Execution Outcome)

| Milestone | Planned Window | Outcome From Tracker |
|-----------|----------------|----------------------|
| MVP definition, client alignment, team planning | Week 1 | Completed |
| Database foundation, OCR baseline, API contracts, retrieval stubs | Week 2 | Completed |
| First RAG implementation sprint | Week 3 | Partially completed; carry-over tasks shifted |
| Integration catch-up and Android/backend wiring | Week 4 | Completed |
| RAG completion, Gemini integration, app expansion | Week 5 | Mostly completed; two testing lines marked ongoing |
| Wearables + environment + auth full integration | Week 6 | Completed |
| Doctor-ready workflows and scheduled summarization | Week 7 | Completed |
| Final functional enhancements and hardening | Week 8 | Completed |
