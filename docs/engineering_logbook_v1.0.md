# 📗 NyayaSetu Engineering Logbook v1.0

> **Document Type:** Chronological Development Diary  
> **Project:** NyayaSetu AI  
> **Version:** 1.0 | **Started:** 2026-06-30  
> **Author:** Renuka  
> **Purpose:** Document every meaningful development task — what was built, why, how, and what it means for interviews and your resume.

---

## How to Use This Logbook

1. Open a new Task entry for every meaningful coding/testing session
2. Fill in every field — especially the Resume Bullet and Interview Q/A
3. Commit the updated Logbook to GitHub along with the code changes
4. Reference these entries during interview prep — they're your evidence

**Task Entry Template:**

```markdown
### Task [N] — [YYYY-MM-DD]: [Short Title]

- **Capability:** [QA/dev skill applied]
- **Objective:** [What you were trying to achieve]
- **Files Changed:** [List of files added or modified]
- **Implementation:** [What you built/wrote/changed — 3–5 sentences]
- **Tests Added:** [What tests were written, scenarios covered]
- **CI/Deployment:** [Any CI changes, Actions triggered]
- **Resume Bullet:** "Implemented [X] using [Y], achieving [Z impact]."
- **Interview Q:** [Likely question this work prepares you to answer]
- **Model Answer:** [Your prepared answer — use STAR format if behavioral]
- **Lessons Learned:** [Anything that surprised you or tripped you up]
```

---

## Task Entries

---

### Task 1 — 2026-06-30: Project Setup & Repository Structure

- **Capability:** Git/GitHub, project organization, repository scaffolding
- **Objective:** Initialize the NyayaSetu AI repository with a clean, professional folder structure that supports future growth — backend, frontend, tests, docs, schemas, datasets.
- **Files Changed:**
  - `README.md` (created)
  - `backend/app/main.py` (created)
  - `backend/requirements.txt` (created)
  - `docs/` folder structure (created)
  - `.github/workflows/ci.yml` (created, placeholder)
  - `.gitignore` (created)
- **Implementation:** Set up a monorepo structure with `backend/`, `frontend/`, `tests/e2e/`, `datasets/`, `schemas/`, `docs/`, and `architecture/` folders. Initialized FastAPI app in `main.py` with a health-check route. Wrote a README explaining the project vision and folder layout. Added `.gitignore` for Python and Node artifacts.
- **Tests Added:** None yet — first task was scaffolding only.
- **CI/Deployment:** Created placeholder `ci.yml` — will be expanded in Week 4.
- **Resume Bullet:** "Designed and initialized a modular monorepo for NyayaSetu AI — a Python/FastAPI legal intelligence system — following professional project organization standards."
- **Interview Q:** "Walk me through how you'd set up a new Python project from scratch."
- **Model Answer:** "I start with a clear folder structure separating concerns: source code, tests, docs, and configuration. I initialize Git early, write a meaningful README, add a `.gitignore`, and set up the package structure so imports are clean. For a FastAPI project, I add a `requirements.txt`, create the app entry point with a health-check route, and ensure the project runs with a single command from day one."
- **Lessons Learned:** Setting up the folder structure thoughtfully at the start saves significant refactoring later. It's worth spending 30 minutes planning before writing any code.

---

### Task 2 — 2026-06-30: Write MappingService Unit Test Suite

- **Capability:** pytest — fixtures, parametrize, class-based test organisation, tmp_path
- **Objective:** Establish a full unit test suite for `MappingService` covering all public methods — search, contradiction detection, impact analysis, schema validation, and record validation — with proper isolation using `conftest.py` fixtures.
- **Files Changed:**
  - `tests/conftest.py` (created)
  - `tests/test_mapping_service.py` (created)
  - `pytest.ini` (created)
- **Implementation:** Created `conftest.py` with session-scoped fixtures (`mapping_service`, `client`), a `MINIMAL_RECORD` constant, and `tmp_path`-based fixtures for edge cases (duplicate IPC codes, empty critical lists). Wrote `test_mapping_service.py` with 6 test classes: `TestSearch` (13 tests), `TestDeterminism` (4), `TestContradictionDetection` (4), `TestImpactAnalysis` (4), `TestSchemaValidation` (3), `TestRecordValidation` (4), `TestEdgeCases` (3). Used `@pytest.mark.parametrize` to test 5 different search keywords in one block.
- **Tests Added:** 39 unit tests — all 39 pass. Covers happy paths, empty input, zero/negative limits, missing files, corrupt JSON, and invalid data types.
- **CI/Deployment:** `pytest.ini` configures `testpaths = tests` so CI always discovers tests correctly.
- **Resume Bullet:** "Wrote 39 parametrized pytest unit tests for a legal mapping service — covering search ranking, contradiction detection, schema validation, and edge cases — achieving full method coverage."
- **Interview Q:** "How do you structure a pytest test suite for a service class?"
- **Model Answer:** "I use class-based test organisation — one class per behaviour area (e.g. `TestSearch`, `TestDeterminism`) — with shared fixtures in `conftest.py`. Session-scoped fixtures handle expensive setup like loading a real data file, while `tmp_path` fixtures isolate tests that need custom data. I use `@pytest.mark.parametrize` to avoid repeating the same assertion pattern for multiple inputs. This keeps tests readable, fast, and independent."
- **Lessons Learned:** A `session`-scoped fixture sharing one `MappingService` instance is safe only because the service is stateless (reads data at init, never mutates it). If the service ever gains write methods, fixtures need `function` scope.

---

### Task 3 — 2026-06-30: Write Search API Contract Tests + JSON Schema

- **Capability:** API contract testing — jsonschema, FastAPI TestClient, negative testing, determinism verification
- **Objective:** Prove that `GET /search` always returns a response that matches a formal JSON Schema contract, handles invalid inputs with correct HTTP status codes (not 500s), and is deterministic across repeated calls.
- **Files Changed:**
  - `schemas/search_response_schema.json` (created)
  - `tests/test_search_api.py` (created)
- **Implementation:** Defined `schemas/search_response_schema.json` with `additionalProperties: false` — every field typed, required list enforced. Wrote `test_search_api.py` with 4 test classes: `TestSearchContract` (13 tests, validates every response against the schema), `TestSearchLimit` (6 tests for limit boundaries), `TestSearchNegative` (7 tests — missing param, empty string, XSS attempt, SQL injection, very long query), `TestSearchDeterminism` (5 tests proving same query → same result). Used `assert_valid_schema()` helper so failures print the exact offending path.
- **Tests Added:** 41 API tests — all 41 pass.
- **CI/Deployment:** These tests run in CI via the new `ci.yml` pipeline.
- **Resume Bullet:** "Implemented JSON Schema contract testing for a FastAPI search endpoint — 41 tests covering happy paths, negative inputs (XSS, SQL injection, empty strings), limit boundary validation, and determinism — integrated into GitHub Actions CI."
- **Interview Q:** "How do you ensure your API never silently breaks its contract?"
- **Model Answer:** "I define a JSON Schema for every API response with `additionalProperties: false` — this catches not just missing fields but also type changes and unexpected fields. In pytest, I validate every successful response against the schema using `jsonschema.validate()`. I also write negative tests: what happens with empty strings, missing params, injected characters. These run in CI on every push, so any change that accidentally alters the response shape fails the build immediately, before it reaches review."
- **Lessons Learned:** Setting `additionalProperties: false` in the schema is critical. Without it, a schema test can pass even if the API adds unexpected fields that could break typed clients downstream.

---

### Task 4 — 2026-06-30: Add GitHub Actions CI Pipeline

- **Capability:** CI/CD — GitHub Actions, multi-job pipeline, coverage enforcement
- **Objective:** Automate linting and testing on every push to `main` and every PR, so the main branch is always in a known-good state and coverage never silently drops.
- **Files Changed:**
  - `.github/workflows/ci.yml` (created)
- **Implementation:** Wrote a 2-job GitHub Actions workflow. Job 1 (`lint`) installs `flake8` and checks the `backend/` directory with `--max-line-length=100`. Job 2 (`test`) depends on lint passing, installs all backend + test dependencies, runs `pytest tests/ --cov=backend --cov-fail-under=70 -v`, and uploads the coverage artifact. Both jobs use `actions/setup-python@v5` with pip caching to minimise run time.
- **Tests Added:** No new tests — but all 80 existing tests now run automatically.
- **CI/Deployment:** This task IS the CI setup. Verified by running tests locally: 80 passed, 1 warning (httpx deprecation — no action needed).
- **Resume Bullet:** "Configured a 2-stage GitHub Actions CI pipeline (lint → test with 70% coverage gate) that runs on every push and PR, catching regressions before merge."
- **Interview Q:** "Walk me through a CI pipeline you've set up."
- **Model Answer:** "I set up a GitHub Actions pipeline with two jobs that run sequentially. The first job lints the code with flake8 — catching style issues early without running tests. The second job depends on the first, installs dependencies with pip caching, runs pytest with coverage, and fails if coverage drops below 70%. I also upload the coverage artifact so reviewers can see which lines aren't covered. This pattern — lint first, test second — means developers get fast feedback on obvious errors before waiting for the full test suite."
- **Lessons Learned:** The `needs: lint` dependency between jobs ensures tests don't run when the code doesn't even pass lint. This saved CI minutes and makes the failure message clearer.

---

### Task 3 — [YYYY-MM-DD]: [Fill when complete]

- **Capability:**
- **Objective:**
- **Files Changed:**
- **Implementation:**
- **Tests Added:**
- **CI/Deployment:**
- **Resume Bullet:**
- **Interview Q:**
- **Model Answer:**
- **Lessons Learned:**

---

### Task 4 — [YYYY-MM-DD]: [Fill when complete]

- **Capability:**
- **Objective:**
- **Files Changed:**
- **Implementation:**
- **Tests Added:**
- **CI/Deployment:**
- **Resume Bullet:**
- **Interview Q:**
- **Model Answer:**
- **Lessons Learned:**

---

### Task 5 — [YYYY-MM-DD]: [Fill when complete]

- **Capability:**
- **Objective:**
- **Files Changed:**
- **Implementation:**
- **Tests Added:**
- **CI/Deployment:**
- **Resume Bullet:**
- **Interview Q:**
- **Model Answer:**
- **Lessons Learned:**

---

## Sample Entries (For Reference)

The following are example entries to illustrate how to write rich, interview-ready Logbook tasks.

---

### [SAMPLE] Task S1 — 2026-07-10: Implement Schema Validation for Search API

- **Capability:** API Contract Testing / jsonschema validation
- **Objective:** Ensure the Search API always returns responses that exactly match the defined JSON schema — catching regressions automatically.
- **Files Changed:**
  - `schemas/search_response.json` (created)
  - `backend/app/services/validation_pipeline.py` (created)
  - `backend/tests/contract/test_search_contract.py` (created)
- **Implementation:** Defined a JSON schema for the Search API response including required fields (`results`, `total`, `duration_ms`), correct types, and array item structure. Built a `ValidationPipeline` class that loads schema files by name and runs `jsonschema.validate()`. Added runtime validation at the end of the Search route before returning the response — so if the service ever produces a malformed response, it fails loudly rather than silently.
- **Tests Added:** 5 pytest tests — valid payload passes, missing `results` field fails, wrong type for `total` fails, empty results array is valid, extra unknown fields are flagged.
- **CI/Deployment:** Tests run automatically in GitHub Actions CI on push.
- **Resume Bullet:** "Implemented API contract testing using JSON Schema validation in pytest, catching response-shape regressions automatically across 6 endpoints."
- **Interview Q:** "How do you ensure your API responses are always correct?"
- **Model Answer:** "I define JSON schemas for every API response and validate at two levels: at the service layer in runtime to catch bugs before they reach the client, and in the test suite using pytest contract tests. This means any refactor that accidentally changes the response shape will fail the CI pipeline immediately, not get discovered by a user. I used `jsonschema` in Python for this."
- **Lessons Learned:** Discovered that `jsonschema` by default allows extra fields — had to use `additionalProperties: false` to enforce strict schemas. This is a subtle but important difference from loose validation.

---

### [SAMPLE] Task S2 — 2026-07-22: Add GitHub Actions CI Pipeline

- **Capability:** CI/CD — GitHub Actions, automated testing pipeline
- **Objective:** Automate linting and testing on every push so the main branch is always in a known-good state.
- **Files Changed:**
  - `.github/workflows/ci.yml` (updated from placeholder to full pipeline)
- **Implementation:** Wrote a GitHub Actions workflow with two jobs: `lint` (runs flake8 on `backend/`) and `test` (sets up Python 3.11, installs dependencies, runs `pytest backend/tests/ --cov`). Configured the workflow to trigger on `push` and `pull_request` to `main`. Added a coverage threshold — fails if coverage drops below 70%.
- **Tests Added:** No new tests — but all existing tests now run automatically in CI.
- **CI/Deployment:** This task IS the CI setup. Verified by pushing a branch and observing GitHub Actions dashboard.
- **Resume Bullet:** "Set up GitHub Actions CI pipeline running lint and pytest with coverage reporting on every push, reducing manual test execution and catching regressions early."
- **Interview Q:** "Have you worked with CI/CD? Walk me through a pipeline you've set up."
- **Model Answer:** "Yes — I set up a GitHub Actions pipeline for NyayaSetu AI. It has two jobs: first, a linter (flake8) that checks code style, and second, a test runner (pytest) with coverage reporting. It triggers on every push and PR to main. If tests fail or coverage drops below threshold, the merge is blocked. This gave the team immediate feedback on whether a change broke anything."
- **Lessons Learned:** GitHub Actions runs in a clean Ubuntu environment, so any test that relies on a local file path will fail. I had to update the dataset loader to use paths relative to the project root, not the developer's machine.

---

## Logbook Index

| Task # | Date | Title | Capability | Status |
|--------|------|-------|-----------|--------|
| 1 | 2026-06-30 | Project Setup & Repository Structure | Git/GitHub, project org | Done |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| S1 | [Sample] | Schema Validation for Search API | API Contract Testing | Sample |
| S2 | [Sample] | GitHub Actions CI Pipeline | CI/CD | Sample |

---

*End of Engineering Logbook v1.0 — add a new Task entry after every meaningful coding session.*
