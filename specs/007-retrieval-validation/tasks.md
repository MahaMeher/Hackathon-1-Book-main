# Tasks: Retrieval Validation & Pipeline Testing

**Input**: Design documents from `/specs/007-retrieval-validation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/retrieval-contract.md
**Feature Branch**: `007-retrieval-validation`

**Tests**: YES - Unit tests and integration tests included for validation functionality

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source code**: `backend/retrieved.py`, `backend/tests/`
- **Single file implementation**: All retrieval logic in `backend/retrieved.py`
- **Tests**: Separate test files in `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing project structure and dependencies from Spec 1

- [X] T001 Verify backend directory structure exists from Spec 1
- [X] T002 [P] Verify pyproject.toml has required dependencies (qdrant-client, cohere, python-dotenv, requests)
- [X] T003 [P] Verify .env file exists with QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create retrieved.py file with proper imports (qdrant-client, cohere, dotenv, requests, logging, time, dataclasses)
- [X] T005 [P] Define data classes for SearchQuery, RetrievedChunk, RetrievalResult, ValidationResult, QuerySession in backend/retrieved.py per data-model.md
- [X] T006 [P] Implement configuration loading from environment variables in backend/retrieved.py
- [X] T007 Set up Qdrant client initialization and connection verification in backend/retrieved.py
- [X] T008 Set up Cohere client initialization for query embeddings in backend/retrieved.py
- [X] T009 Configure logging infrastructure with proper format and levels in backend/retrieved.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Semantic Similarity Search Validation (Priority: P1) 🎯 MVP

**Goal**: Execute test queries against Qdrant collection and retrieve semantically relevant book content with proper embeddings and similarity search

**Independent Test**: Can be fully tested by executing sample queries against the Qdrant collection and verifying that retrieved chunks are semantically relevant to the query terms

### Tests for User Story 1

- [X] T010 [P] [US1] Create test file test_retrieval.py in backend/tests/test_retrieval.py with pytest setup and fixtures
- [X] T011 [P] [US1] Create unit test for execute_query() with mocked Qdrant and Cohere clients in backend/tests/test_retrieval.py
- [X] T012 [US1] Create integration test for end-to-end query execution against real Qdrant collection in backend/tests/test_retrieval.py

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement execute_query() function signature with query_text, top_k, collection_name parameters in backend/retrieved.py
- [X] T014 [US1] Implement query embedding generation using Cohere embed-english-v3.0 with 'search_query' input type in backend/retrieved.py
- [X] T015 [US1] Implement cosine similarity search query against Qdrant collection with top-k retrieval in backend/retrieved.py
- [X] T016 [US1] Map Qdrant results to RetrievedChunk dataclass with similarity scores and metadata in backend/retrieved.py
- [X] T017 [US1] Build RetrievalResult with timing breakdown (embedding_time_ms, search_time_ms, execution_time_ms) in backend/retrieved.py
- [X] T018 [US1] Add empty query validation and QueryEmptyError exception in backend/retrieved.py
- [X] T019 [US1] Add error handling for connection failures and API errors with appropriate exceptions in backend/retrieved.py

**Checkpoint**: At this point, User Story 1 should be fully functional - can execute queries and retrieve results independently

---

## Phase 4: User Story 2 - Metadata Validation & Source Tracing (Priority: P1)

**Goal**: Validate completeness and accuracy of metadata in retrieved chunks, verify source URLs correspond to actual ingested book pages

**Independent Test**: Can be fully tested by running queries and verifying that all returned results contain complete and accurate metadata that maps to actual source URLs

### Tests for User Story 2

- [X] T020 [P] [US2] Create test file test_validation.py in backend/tests/test_validation.py with pytest setup
- [X] T021 [P] [US2] Create unit test for validate_result() with mock RetrievalResult in backend/tests/test_validation.py
- [X] T022 [US2] Create integration test for metadata validation with real Qdrant results in backend/tests/test_validation.py

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement validate_metadata() function to check completeness of all required fields (source_url, section, chunk_index, model_used) in backend/retrieved.py
- [X] T024 [US2] Implement validate_urls() function to verify source URLs are valid URL format in backend/retrieved.py
- [X] T025 [US2] Implement relevance scoring based on similarity scores and keyword overlap in backend/retrieved.py
- [X] T026 [US2] Build ValidationResult with metadata_completeness, url_valid, relevance_score, passes_criteria in backend/retrieved.py
- [X] T027 [US2] Add validation to execute_query() pipeline that calls validate_result() on each query result in backend/retrieved.py
- [X] T028 [US2] Implement URL format validation (regex or urlparse) without HTTP requests in backend/retrieved.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - queries return results with validated metadata

---

## Phase 5: User Story 3 - Retrieval Performance & Latency Validation (Priority: P2)

**Goal**: Measure and report query execution times to ensure retrieval latency is acceptable for interactive use (<2 seconds per query)

**Independent Test**: Can be fully tested by running multiple queries and measuring response times to verify they meet latency targets

### Tests for User Story 3

- [X] T029 [P] [US3] Create unit test for performance measurement functions in backend/tests/test_retrieval.py
- [X] T030 [US3] Create integration test that verifies query execution time is under 2 seconds in backend/tests/test_retrieval.py

### Implementation for User Story 3

- [X] T031 [P] [US3] Add detailed timing instrumentation to execute_query() with separate measurements for embedding and search in backend/retrieved.py
- [X] T032 [US3] Implement QuerySession tracking with avg_execution_time_ms calculation in backend/retrieved.py
- [X] T033 [US3] Add performance logging with breakdown reporting for each operation in backend/retrieved.py

**Checkpoint**: User Story 3 complete - can measure and report performance for all queries

---

## Phase 6: User Story 4 - Deterministic Pipeline Behavior (Priority: P2)

**Goal**: Verify that the retrieval pipeline behaves deterministically - same query returns same results across multiple runs

**Independent Test**: Can be fully tested by running the same query multiple times and verifying consistent results

### Tests for User Story 4

- [X] T034 [P] [US4] Create unit test for test_determinism() function with mocked Qdrant in backend/tests/test_validation.py
- [X] T035 [US4] Create integration test that runs same query 5 times and verifies identical results in backend/tests/test_validation.py

### Implementation for User Story 4

- [X] T036 [P] [US4] Implement test_determinism() function that executes same query multiple times and compares results in backend/retrieved.py
- [X] T037 [US4] Add result comparison logic checking chunk_ids, order, and similarity scores across runs in backend/retrieved.py
- [X] T038 [US4] Update run_validation_session() to support optional determinism testing flag in backend/retrieved.py

**Checkpoint**: All user stories complete - full validation pipeline with determinism verification

---

## Phase 7: CLI Interface & Main Function

**Purpose**: Provide command-line interface for running validation tests with various options

- [X] T039 Implement argument parser with --query, --queries-file, --top-k, --output, --test-determinism, --verbose options in backend/retrieved.py
- [X] T040 Implement run_validation_session() orchestrating multiple queries with results aggregation in backend/retrieved.py
- [X] T041 Implement main() function that parses args, connects to Qdrant, runs validation, and displays results in backend/retrieved.py
- [X] T042 Implement console output formatting with structured display of queries, results, and validation summary in backend/retrieved.py
- [X] T043 Implement JSON export functionality to write RetrievalResult to output file in backend/retrieved.py
- [X] T044 Implement default test queries covering all 4 book modules (ROS 2, Digital Twin, AI Brain, VLA) in backend/retrieved.py

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] Add comprehensive docstrings to all public functions in backend/retrieved.py
- [X] T046 [P] Add type hints to all function signatures and return types in backend/retrieved.py
- [X] T047 Run all unit tests and verify they pass: `cd backend && pytest tests/ -v`
- [X] T048 Create integration test script that runs complete validation session in backend/tests/test_integration.py
- [X] T049 Run end-to-end validation with real queries against Qdrant collection and verify all success criteria met
- [X] T050 Update README.md in backend/ with retrieval validation usage instructions
- [X] T051 Verify quickstart.md scenarios work correctly by running examples from the guide
- [X] T052 Performance validation - run multiple queries and verify average execution time < 2 seconds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2)
  - Or in parallel if multiple developers available
- **CLI Interface (Phase 7)**: Depends on all user story functions being implemented
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 results but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on execute_query() timing from US1
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on execute_query() determinism

### Within Each User Story

- Tests MUST be written before implementation (TDD approach)
- Models/data classes before services/functions
- Core implementation before integration
- Error handling added throughout
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks marked [P] can run in parallel (T005, T006)
- All tests for a user story marked [P] can run in parallel (T010, T011)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create test file test_retrieval.py in backend/tests/test_retrieval.py"
Task: "Create unit test for execute_query() with mocked clients"

# Once foundation is ready, these can run in parallel:
Task: "Implement execute_query() function signature"
Task: "Define SearchQuery dataclass"
Task: "Define RetrievedChunk dataclass"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Execute test query and verify relevant results returned
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Execute queries and retrieve results → Test independently
3. Add User Story 2 → Validate metadata and URLs → Test independently
4. Add User Story 3 → Measure performance → Test independently
5. Add User Story 4 → Verify determinism → Test independently
6. Add CLI Interface → Run full validation session
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (execute_query)
   - Developer B: User Story 2 (validate_result)
   - Developer C: User Story 3 + 4 (performance + determinism)
3. Stories complete and integrate independently
4. Team collaborates on CLI Interface phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Reuse existing backend infrastructure from Spec 1 (pyproject.toml, .env)
- Single file architecture keeps everything in backend/retrieved.py
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
