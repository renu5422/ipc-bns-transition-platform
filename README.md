# IPC-BNS Legal Intelligence Platform

AI-assisted legal migration and validation platform for translating legal references from the Indian Penal Code (IPC) to the Bharatiya Nyaya Sanhita (BNS) with traceable, engineering-grade validation.

## Problem Statement

The IPC-to-BNS transition introduces operational risk for legal teams, investigators, and compliance workflows:
- legacy case records and legal templates still reference IPC sections,
- migrated sections may not be one-to-one and can require contextual interpretation,
- manual migration is time-consuming and inconsistent across teams,
- poor migration quality can produce downstream drafting and review errors.

This project addresses those risks through a structured migration pipeline that combines deterministic rules, AI-assisted analysis, and measurable validation.

## Architecture Overview

The platform follows a modular full-stack architecture:

- **Frontend (Next.js + TypeScript):** analyst-facing interface for input, review, conflict visibility, and migration reports.
- **Backend API (FastAPI + Python):** orchestration layer for migration, validation, scoring, and audit trace generation.
- **Mapping/Data Layer:** canonical IPC↔BNS mapping assets and rule metadata.
- **Reasoning & Validation Layer:** deterministic rule engine plus model-assisted interpretation for ambiguous cases.
- **Audit/Trace Layer:** stores reasoning steps, contradictions, and confidence metrics for reviewability.

## Workflow Pipeline

1. **Input Ingestion**
   - Accept legal text, section references, or structured case metadata.

2. **Reference Extraction**
   - Detect and normalize IPC references.

3. **Candidate Mapping Generation**
   - Produce one or more BNS candidates from canonical mapping data and transformation rules.

4. **Deterministic Rule Pass**
   - Apply explicit legal mapping constraints and precedence rules.

5. **AI-Assisted Reasoning Pass**
   - Evaluate contextual signals where deterministic mapping is insufficient.

6. **Validation & Scoring**
   - Compute consistency, coverage, and confidence scores.

7. **Contradiction Detection**
   - Flag conflicting mappings, incompatible assumptions, and low-agreement outcomes.

8. **Human Review Output**
   - Return ranked suggestions with rationale, score breakdown, and audit trail.

## Deterministic Reasoning System

The deterministic layer is designed to maximize repeatability and legal traceability:
- rule-based mapping with explicit precedence,
- schema-level checks for reference format and section integrity,
- versioned rule sets for reproducible outcomes,
- deterministic fallback behavior before any model-assisted step.

This ensures core migration behavior is explainable and testable independent of model variability.

## Validation and Scoring

Validation is first-class and not treated as an afterthought. The system evaluates:
- **Mapping Validity:** whether output sections conform to known legal mapping constraints,
- **Contextual Fit:** whether candidate mappings align with extracted legal context,
- **Coverage:** proportion of input references confidently migrated,
- **Confidence Composition:** combined score from deterministic certainty and AI-assisted assessment.

Scores are exposed with component-level transparency so reviewers can understand why a mapping was accepted or flagged.

## Contradiction Detection

The contradiction module identifies and isolates problematic outcomes such as:
- multiple high-confidence but mutually exclusive mappings,
- context-rule disagreements,
- section-level inconsistencies across the same document,
- rule-pass vs model-pass divergence.

Detected contradictions are surfaced as structured review tasks rather than silently resolved, supporting legal quality control.

## Future Chatbot Layer

A future conversational interface is planned as a thin layer on top of the existing reasoning and validation engine. The chatbot will:
- answer migration questions using the same validated pipeline,
- provide citation-aware explanations from platform outputs,
- remain bounded by deterministic and scoring constraints.

This keeps conversational UX aligned with the platform’s engineering and compliance guarantees.

## Tech Stack

- **Backend:** FastAPI, Python
- **Frontend:** Next.js, TypeScript
- **Data/Rules:** JSON-based mapping assets and rule metadata

## Repository Structure

```text
ipc-bns-app/
├── frontend/   # Next.js + TypeScript UI
├── backend/    # FastAPI services in Python
├── data/       # IPC-BNS mapping and rule data
└── docs/       # Architecture, API, security, and design docs
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Documentation

- [Architecture](docs/architecture.md)
- [MVP Scope](docs/mvp_scope.md)
- [API Design](docs/api_design.md)
- [Security Plan](docs/security_plan.md)
- [Data Model](docs/data_model.md)
