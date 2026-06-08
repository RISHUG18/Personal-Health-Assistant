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

## Milestone Schedule

### Weeks 1–2: Release 1 – Core MVP Foundation

Focus on architecture finalization, schema design, metadata definitions, API contracts, prompt drafting, and UI wireframes. During this phase, database schemas, alert object formats, RAG metadata specifications, and frontend contracts will be frozen. Parallel efforts will establish OCR inspection, text cleaning, chunking strategies, embedding experiments, retrieval stubs, and dummy UI components. By the end of Week 2, the core data flow pipelines (extraction, ingestion, retrieval skeleton, and static dashboards) will be implemented in draft-complete form.

### Weeks 3–4: Release 1 – Core System Implementation

Transition from drafts to working components. This includes implementing the rules engine, structured data normalization, vector ingestion into the production database, top-k similarity search, contextual prompt integration, and explainable alert generation. The frontend will integrate APIs, display alerts with severity indicators, and provide explainability drawers. AI responses will be grounded using RAG with real Gemini calls, and environment APIs (weather and AQI) will be integrated into the reasoning pipeline. By the end of Week 4, the system will be feature-complete for the MVP and ready for integration testing.

### Weeks 5–6: Release 1 – Core MVP Delivery

Focus on refinement, stability, and end-to-end validation. Trend-based rules, reminder logic, environment-aware severity modifiers, explainable chat UI, citation highlighting, and improved retrieval filters will be finalized. Performance optimization, metadata validation, logging, and guardrail UX will also be implemented. Cross-component integration, debugging, and demo preparation will be completed. At the end of Week 6, Release 1 (Core MVP) will be tagged and delivered, demonstrating upload-to-alert-to-AI explanation with environmental context in a fully integrated, explainable system.

### Weeks 7–8: Release 2 – Context-Aware Doctor-Ready System

Expand the system with patient-level aggregation, doctor dashboards, summary prompts, audit views, trend visualization, improved retrieval filtering, hallucination guardrails, and evaluation documentation. Security hardening, observability, error handling, and explainability enhancements will be completed. Evaluation benchmarks for retrieval quality and rule validation will be documented. By the end of Week 8, Release 2 will be delivered, showcasing a context-aware, doctor-ready, evaluated RAG system with refined UI and stable performance.

### Week 9: Final Submission Milestone – No New Release

Reserved strictly for final polishing, documentation cleanup, minor fixes, commit stabilization, submission checklist verification, and demo rehearsal. No new features will be added during this phase to minimize risk. This milestone ensures a smooth and professionally prepared final project submission.

## Milestone Timeline

| Milestone | Due Date | Release | Deliverable? |
|-----------|----------|---------|--------------|
| Data Architecture & DB Schemas | 31 Jan | R1 Prep | Yes |
| Context Object, Prompts & Contracts | 31 Jan | R1 Prep | Yes |
| Structured Extraction & DB Integration | 7 Feb | R1 Build | Yes |
| RAG Ingestion (Cleaning, Chunking, Vectors) | 7 Feb | R1 Build | Yes |
| Rules Engine & Alert Generation | 14 Feb | R1 Build | Yes |
| Retrieval Logic & Gemini Integration | 21 Feb | R1 Build | Yes |
| Environmental Context Integration | 28 Feb | R1 | Yes |
| Explainable Alerts UI & MVP Demo | 7 March | R1 | Yes |
| Trend Analysis, Reminders & Prompt Refinement | 14 March | R2 Build | Yes |
| Explainable Chat UI | 14 March | R2 Build | Yes |
| Doctor Dashboard & Aggregation Logic | 21 March | R2 Build | Yes |
| Explainability Backend, Logs & Guardrails | 28 March | R2 Build | Yes |
| Evaluation, Hardening & System Freeze | 4 April | R2 | Yes |
| Final Polish, QA & Submission | 11 April | R2 | No |
