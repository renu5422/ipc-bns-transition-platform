# 📙 QA/SDET Learning Roadmap v1.0

> **Document Type:** Living Learning & Execution Roadmap  
> **Project Context:** NyayaSetu AI  
> **Version:** 1.0 | **Date:** 2026-06-30  
> **Author:** Renuka  
> **Purpose:** Track every QA/SDET capability learned, implemented, and interview-prepped — all through real NyayaSetu work

---

## Table of Contents

1. [Philosophy & Rules](#part-i--philosophy--rules)
2. [Weekly Framework](#part-ii--weekly-framework)
3. [Capability Tracker](#part-iii--capability-tracker)
4. [DSA Tracker](#part-iv--dsa-tracker)
5. [Week-by-Week Plan](#part-v--week-by-week-plan)
6. [Friday Consolidation Template](#part-vi--friday-consolidation-template)
7. [Weekend Sprint Framework](#part-vii--weekend-sprint-framework)
8. [Job Search Playbook](#part-viii--job-search-playbook)
9. [Progress Log](#part-ix--progress-log)

---

## Part I – Philosophy & Rules

### 1.1 Core Learning Philosophy

**"Learn through NyayaSetu — not alongside it."**

Every concept must be implemented in a real part of the project. No isolated toy examples. The full cycle for every capability:

```
Learn → Implement in NyayaSetu → Write Tests → Debug → Document → Interview Prep
```

This means: if you're learning API schema validation, you write a real jsonschema test for the NyayaSetu Search API — not a hello-world validator.

### 1.2 Permanent Roadmap Rules

| # | Rule |
|---|------|
| 1 | Track **capabilities**, not just tasks. Every entry maps to a skill. |
| 2 | **Mon–Thu:** Learn + implement one new QA/SDET capability. |
| 3 | **Friday:** Consolidation only — no new topic. Review, document, interview prep. |
| 4 | **Sat–Sun:** NyayaSetu sprint — feature work, integration, deep builds. |
| 5 | Every feature = code + tests + docs + Git commit + resume bullet + interview Q. |
| 6 | No capability is "done" until its resume bullet and interview Q/A are written. |
| 7 | DSA practice daily — 1 problem minimum on weekdays, 2 on weekends. |

---

## Part II – Weekly Framework

### Monday–Thursday: Capability Days

Each day within the week builds on the same capability:

- **Monday:** Learn the concept (read docs, watch tutorial, read one blog post)
- **Tuesday:** Implement it in NyayaSetu (write the code/test)
- **Wednesday:** Deepen it — add edge cases, negative tests, error scenarios
- **Thursday:** Polish — refactor, add to CI, update documentation

### Friday: Consolidation Day

No new learning. One structured review session:

1. Write the Friday Consolidation entry (template in Part VI)
2. Draft or update resume bullet for this week's capability
3. Prepare interview Q&A
4. Push all changes to GitHub with clean commit messages
5. DSA: 2 problems from current week's pattern

### Saturday–Sunday: NyayaSetu Sprint

- Define a mini sprint goal on Friday evening
- Build toward a complete feature or integration milestone
- Write tests as you go (TDD preferred)
- End Sunday with a Git commit and Logbook entry

---

## Part III – Capability Tracker

> Update Status column as: `Not Started` → `In Progress` → `Done`  
> Mark ✓ in Resume Bullet and Interview Q columns when written

| # | Category | Capability | NyayaSetu Module | Resume Bullet | Interview Q | Status |
|---|----------|------------|-----------------|:---:|:---:|--------|
| 1 | Python | OOP: Classes & Inheritance | All service modules | | | Not Started |
| 2 | Python | Decorators & Context Managers | Diagnostics Layer | | | Not Started |
| 3 | Python | Type Hints & Pydantic Models | FastAPI schemas | | | Not Started |
| 4 | Python | Exception Handling Patterns | All services | | | Not Started |
| 5 | Python | Async/Await (asyncio) | FastAPI async routes | | | Not Started |
| 6 | Data | NumPy arrays & operations | Retrieval scoring | | | Not Started |
| 7 | Data | Pandas DataFrames & filtering | Dataset preprocessing | | | Not Started |
| 8 | Data | Matplotlib/Seaborn charts | Results visualization | | | Not Started |
| 9 | ML | Scikit-learn pipelines | Relevance ranking model | | | Not Started |
| 10 | ML | Train/test split & evaluation | Mapping quality eval | | | Not Started |
| 11 | API | REST API design (FastAPI) | All API endpoints | | | Not Started |
| 12 | API Testing | Schema Validation (jsonschema) | Validation Pipeline | | | Not Started |
| 13 | API Testing | Negative Testing | Search API | | | Not Started |
| 14 | API Testing | Contract Testing | All endpoints | | | Not Started |
| 15 | API Testing | Postman/pytest API tests | All endpoints | | | Not Started |
| 16 | Automation | Playwright setup & config | Frontend E2E | | | Not Started |
| 17 | Automation | Locators & Selectors | Frontend UI tests | | | Not Started |
| 18 | Automation | Synchronization (waits) | Playwright tests | | | Not Started |
| 19 | Automation | Page Object Model (POM) | Playwright tests | | | Not Started |
| 20 | Backend QA | Pytest fixtures & conftest | All test suites | | | Not Started |
| 21 | Backend QA | Mocking & Patching | Service unit tests | | | Not Started |
| 22 | Backend QA | Test parametrization | Retrieval tests | | | Not Started |
| 23 | Backend QA | Coverage measurement | All modules | | | Not Started |
| 24 | Backend QA | Logging & Diagnostics | Diagnostics Layer | | | Not Started |
| 25 | CI/CD | GitHub Actions setup | Build pipeline | | | Not Started |
| 26 | CI/CD | Test automation in CI | ci.yml workflow | | | Not Started |
| 27 | CI/CD | Code linting in CI | flake8 in CI | | | Not Started |
| 28 | Agentic AI | LangChain basics | Chatbot Engine | | | Not Started |
| 29 | Agentic AI | LangGraph multi-step agents | Complex query flows | | | Not Started |
| 30 | Agentic AI | MCP (Model Context Protocol) | External tool integration | | | Not Started |
| 31 | LLM | Prompt Engineering | Summary Generator | | | Not Started |
| 32 | LLM | RAG (Retrieval-Augmented Gen) | Chatbot + Retrieval | | | Not Started |
| 33 | DB | SQL basics & queries | Dataset querying | | | Not Started |
| 34 | DB | SQLAlchemy ORM | Data layer | | | Not Started |
| 35 | Deployment | Flask/FastAPI deployment | Local + cloud deploy | | | Not Started |
| 36 | Deployment | Docker basics | Containerization | | | Not Started |
| 37 | DL | TensorFlow/PyTorch basics | Experimental ranking | | | Not Started |
| 38 | Tools | Git branching & PRs | All contributions | | | Not Started |
| 39 | Tools | VS Code debugging | Development workflow | | | Not Started |
| 40 | Tools | Postman collections | API testing | | | Not Started |

---

## Part IV – DSA Tracker

> One problem minimum per day. Document approach and time complexity.

| Week | Pattern | Topics | LeetCode Problems | Status |
|------|---------|--------|------------------|--------|
| 1 | HashMap / Counting | Frequency maps, two-sum variants | Two Sum (#1), Valid Anagram (#242), Group Anagrams (#49) | Not Started |
| 2 | Sliding Window | Fixed + variable window, substring problems | Max Subarray (#53), Longest Substring No Repeat (#3) | Not Started |
| 3 | Two Pointers | In-place ops, sorted arrays, palindromes | Container With Most Water (#11), 3Sum (#15) | Not Started |
| 4 | Binary Search | Search in sorted arrays, find boundary | Binary Search (#704), Search in Rotated Array (#33) | Not Started |
| 5 | Stack / Queue | Monotonic stack, BFS, expression eval | Valid Parentheses (#20), Daily Temperatures (#739) | Not Started |
| 6 | Trees (BFS/DFS) | Level order, path sum, traversals | Max Depth Binary Tree (#104), Level Order (#102) | Not Started |
| 7 | Graphs | DFS/BFS on grid, connected components | Number of Islands (#200), Clone Graph (#133) | Not Started |
| 8 | Dynamic Programming | Memoization, 1D/2D DP | Climbing Stairs (#70), Coin Change (#322) | Not Started |
| 9 | Sorting & Intervals | Merge intervals, custom sort | Merge Intervals (#56), Sort Colors (#75) | Not Started |
| 10 | Linked Lists | Reverse, detect cycle, merge | Reverse List (#206), Merge Two Sorted (#21) | Not Started |

---

## Part V – Week-by-Week Plan

### Week 1 (Jun 30 – Jul 6, 2026) — Python Foundations + pytest Basics

**Mon–Thu Focus:** Python OOP + pytest fixtures  
**NyayaSetu Implementation:** Refactor Retrieval Engine as a class; write first pytest suite  
**DSA Pattern:** HashMap  

| Day | Activity |
|-----|----------|
| Mon | Review Python OOP: classes, inheritance, `__init__`, `@property`. Read FastAPI source for patterns. |
| Tue | Refactor `retrieval_engine.py` into a class `RetrievalEngine` with typed methods. |
| Wed | Write `tests/unit/test_retrieval_engine.py` with pytest fixtures and parametrize. |
| Thu | Add conftest.py with shared fixtures. Run coverage. Fix gaps. Commit. |
| Fri | Friday Consolidation: OOP + pytest. Write resume bullet. Interview Q: "How do you structure Python classes for testability?" |
| Sat–Sun | Sprint: Complete Aggregation Service class + unit tests. Commit. Logbook entry. |

**Deliverables:** `retrieval_engine.py` (class-based), `test_retrieval_engine.py`, conftest.py, Logbook Task #1

---

### Week 2 (Jul 7–13) — API Design + Schema Validation

**Mon–Thu Focus:** FastAPI route design + jsonschema contract testing  
**NyayaSetu Implementation:** Define all API schemas, add Validation Pipeline  
**DSA Pattern:** Sliding Window  

| Day | Activity |
|-----|----------|
| Mon | Learn FastAPI: Pydantic models, response types, status codes. |
| Tue | Define JSON schemas for Search and Mapping API responses. |
| Wed | Implement Validation Pipeline using `jsonschema`. Write contract test suite. |
| Thu | Add negative tests — missing fields, wrong types, extra fields. Commit. |
| Fri | Consolidation: API schema validation. Resume bullet. Interview Q: "How do you ensure API response correctness?" |
| Sat–Sun | Sprint: Hook Validation Pipeline into all existing endpoints. Run full test suite. |

**Deliverables:** `schemas/*.json`, `validation_pipeline.py`, `test_contract_*.py`

---

### Week 3 (Jul 14–20) — Mapping Engine + Negative Testing

**Mon–Thu Focus:** Negative test patterns for APIs  
**NyayaSetu Implementation:** Build Mapping Engine; write negative test suite  
**DSA Pattern:** Two Pointers  

---

### Week 4 (Jul 21–27) — CI/CD + GitHub Actions

**Mon–Thu Focus:** GitHub Actions for CI  
**NyayaSetu Implementation:** Add `ci.yml` — lint + test on every push  
**DSA Pattern:** Binary Search  

---

### Week 5 (Jul 28 – Aug 3) — Playwright E2E Testing

**Mon–Thu Focus:** Playwright setup, locators, synchronization  
**NyayaSetu Implementation:** Write E2E tests for the search UI flow  
**DSA Pattern:** Stack/Queue  

---

### Week 6 (Aug 4–10) — LangChain + Chatbot Engine

**Mon–Thu Focus:** LangChain basics, chain composition, LLM integration  
**NyayaSetu Implementation:** Build first version of Chatbot Engine with LangChain  
**DSA Pattern:** Trees  

---

### Week 7 (Aug 11–17) — LangGraph + Agentic Flows

**Mon–Thu Focus:** LangGraph for multi-step agent workflows  
**NyayaSetu Implementation:** Build a multi-step "search → map → summarize" agent  
**DSA Pattern:** Graphs  

---

### Week 8 (Aug 18–24) — MCP + Tool Integration

**Mon–Thu Focus:** Model Context Protocol (MCP) for external tool use  
**NyayaSetu Implementation:** Expose NyayaSetu APIs as MCP tools  
**DSA Pattern:** Dynamic Programming  

---

### Week 9 (Aug 25–31) — ML + Scikit-learn Ranking

**Mon–Thu Focus:** Scikit-learn pipelines, TF-IDF, ranking models  
**NyayaSetu Implementation:** Replace heuristic ranking in Retrieval Engine with ML model  
**DSA Pattern:** Sorting & Intervals  

---

### Week 10 (Sep 1–7) — Deployment + Docker + FastAPI Prod

**Mon–Thu Focus:** Docker, deployment, FastAPI production patterns  
**NyayaSetu Implementation:** Containerize backend, deploy to Render or Railway  
**DSA Pattern:** Linked Lists  

---

## Part VI – Friday Consolidation Template

Copy this template each Friday. Fill every field before closing the week.

```markdown
### Friday Consolidation — Week [N] — [Date]

- **Capability Learned:** [Name of the QA/dev skill]
- **Where Implemented:** [NyayaSetu module or file(s)]
- **Implementation Summary:** [2–3 sentences: what you built, how it works]
- **Tests Written:** [Number + types of tests added]
- **Resume Bullet:** "Implemented [X] in [context], achieving [result/impact]."
- **Interview Q:** [Likely interview question on this topic]
- **Model Answer:** [3–5 sentence answer using STAR or direct explanation]
- **Mistakes / Gotchas:** [What tripped you up — this is gold for interviews]
- **DSA This Week:** [Pattern + problems solved + time complexities]
- **Next Week Preview:** [What you'll focus on Monday]
```

---

## Part VII – Weekend Sprint Framework

Use this template every Friday evening to plan the weekend sprint.

```markdown
### Weekend Sprint — [Dates]

**Sprint Goal:** [One sentence: what will exist by Sunday evening that doesn't exist now]

**Backlog Items:**
- [ ] Task A: [description] — Est: [hours]
- [ ] Task B: [description] — Est: [hours]
- [ ] Task C: [description] — Est: [hours]

**Done Criteria:**
- [ ] Feature works end-to-end in local dev
- [ ] Tests pass (unit + integration)
- [ ] Committed to GitHub with clean message
- [ ] Logbook entry written

**Sunday Review:**
- What got done: 
- What didn't: 
- Reason: 
- Carry forward to next sprint:
```

---

## Part VIII – Job Search Playbook

### 8.1 Master Research Prompt (Use on Wed/Fri)

```
I'm preparing to apply to [Company] for the [Role] position.
Help me:
1. Summarize what [Company] does and its main products
2. Identify the key technical stack from the job description
3. List the top 5 skills they're prioritizing
4. Find any recent news about [Company] that shows growth/culture
5. Suggest 3 tailored talking points linking my NyayaSetu project to their needs
```

### 8.2 Application Strategy Prompt (Use on Mon/Tue/Thu)

```
Here is the job description for [Role] at [Company]:
[PASTE JD]

Here is my current resume summary and skills:
[PASTE SUMMARY]

Help me:
1. Identify which of my NyayaSetu capabilities match their requirements
2. Rewrite my resume bullet points to align with their language
3. Write a concise, authentic cover email (not formal letter) in 3 paragraphs
4. Suggest which projects or capabilities I should mention first in screening
```

### 8.3 Application Tracker

| # | Company | Role | Applied Date | Source | Status | Notes |
|---|---------|------|:---:|--------|--------|-------|
| 1 | | | | LinkedIn | | |
| 2 | | | | Naukri | | |
| 3 | | | | Referral | | |

**Status values:** Applied → Screening → Interview 1 → Interview 2 → Offer → Rejected → Ghosted

---

## Part IX – Progress Log

> Update weekly. One row per week.

| Week | Dates | Capability | Module Built | Tests Added | DSA Pattern | Git Commits | Notes |
|------|-------|-----------|--------------|-------------|-------------|-------------|-------|
| 1 | Jun 30–Jul 6 | OOP + pytest | Retrieval Engine class | Yes | HashMap | TBD | |
| 2 | Jul 7–13 | API Schema Validation | Validation Pipeline | Yes | Sliding Window | TBD | |
| 3 | Jul 14–20 | Negative Testing | Mapping Engine | Yes | Two Pointers | TBD | |
| 4 | Jul 21–27 | GitHub Actions CI | ci.yml | Yes | Binary Search | TBD | |
| 5 | Jul 28–Aug 3 | Playwright E2E | E2E test suite | Yes | Stack/Queue | TBD | |
| 6 | Aug 4–10 | LangChain | Chatbot Engine v1 | Yes | Trees | TBD | |
| 7 | Aug 11–17 | LangGraph | Multi-step agent | Yes | Graphs | TBD | |
| 8 | Aug 18–24 | MCP | NyayaSetu as MCP tool | Yes | DP | TBD | |
| 9 | Aug 25–31 | ML + Scikit-learn | Ranking model | Yes | Sorting | TBD | |
| 10 | Sep 1–7 | Docker + Deployment | Containerized backend | Yes | Linked Lists | TBD | |

---

*End of QA/SDET Learning Roadmap v1.0 — update every Friday and after each sprint.*
