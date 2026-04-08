# Tasks: Book Content Ingestion & Vector Indexing

**Input**: Design documents from `/specs/006-book-ingestion-vector-indexing/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Organization**: Tasks organized by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Ensure project structure and dependencies are ready

- [ ] T001 Verify backend/ directory exists with main.py, .env.example, pyproject.toml
- [ ] T002 Install dependencies: `cd backend && uv sync` (httpx, beautifulsoup4, cohere, qdrant-client, python-dotenv, tenacity)
- [ ] T003 [P] Copy .env.example to .env and document required variables (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY, BOOK_BASE_URL)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Verify main.py imports: httpx, BeautifulSoup, cohere, qdrant_client, dotenv, tenacity
- [ ] T005 [P] Verify BookIngestionPipeline.__init__() loads all env vars and initializes clients
- [ ] T006 Verify BOOK_BASE_URL environment variable (not VERCEL_BOOK_URL)
- [ ] T007 [P] Verify logging configured with format: `%(asctime)s - %(levelname)s - %(message)s`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Book Content Fetching Pipeline (Priority: P1) 🎯 MVP

**Goal**: Discover and fetch all public pages from Docusaurus book on GitHub Pages

**Independent Test**: Run pipeline with BOOK_BASE_URL and verify all pages fetched with valid HTML content

### Implementation for User Story 1

- [ ] T008 [US1] Implement `discover_book_urls()` in backend/main.py - fetch sitemap.xml, parse URLs, fallback to HTML crawling
- [ ] T009 [US1] Implement `fetch_book_content(url)` in backend/main.py - async HTTP with retry logic (tenacity), handle 404/429/500s
- [ ] T010 [US1] Implement `_extract_title(html)` in backend/main.py - extract <title> or <h1> for page title
- [ ] T011 [US1] Add URL validation and deduplication (normalize trailing slashes, lowercase)
- [ ] T012 [US1] Add statistics tracking: pages_fetched, pages_failed counters

**Checkpoint**: US1 complete - can fetch all book pages with retry logic

---

## Phase 4: User Story 2 - Text Extraction and Chunking (Priority: P1)

**Goal**: Extract clean text from HTML and chunk into embedding-ready segments

**Independent Test**: Run extraction on fetched pages, verify clean text (no HTML tags), verify chunks have proper metadata

### Implementation for User Story 2

- [ ] T013 [US2] Implement `extract_text_content(book_content)` in backend/main.py - remove nav/sidebar/footer with BeautifulSoup, target `.theme-doc-markdown` or `main` selectors
- [ ] T014 [US2] Implement `chunk_text(text, source_url, section)` in backend/main.py - 3000 char chunks with 200 char overlap, break at sentence boundaries
- [ ] T015 [US2] Implement `_extract_section_from_url(url)` in backend/main.py - parse URL path to section name (e.g., `/docs/module1/chapter1` → "Chapter1")
- [ ] T016 [US2] Add chunk metadata: source_url, section, chunk_index, word_count, char_count
- [ ] T017 [US2] Validate extracted text is non-empty and contains no HTML tags (regex: `<[^>]+>`)

**Checkpoint**: US2 complete - can extract clean text and create chunks with metadata

---

## Phase 5: User Story 3 - Embedding Generation and Storage (Priority: P1)

**Goal**: Generate Cohere embeddings and store vectors in Qdrant Cloud with metadata

**Independent Test**: Run embedding generation and verify vectors stored in Qdrant with complete metadata

### Implementation for User Story 3

- [ ] T018 [US3] Implement `generate_embeddings(chunks)` in backend/main.py - batch Cohere API calls (96 texts/batch), use embed-english-v3.0 model
- [ ] T019 [US3] Implement `store_vectors_in_qdrant(vectors)` in backend/main.py - create collection if needed, upsert with metadata payload
- [ ] T020 [US3] Add rate limiting for Cohere API: sleep 12s between batches (5 req/min free tier limit)
- [ ] T021 [US3] Add Qdrant collection verification: get_collection() after upsert, verify vector count
- [ ] T022 [US3] Add metadata payload per vector: source_url, section, chunk_index, model_used, generated_at

**Checkpoint**: US3 complete - embeddings generated and stored with metadata in Qdrant

---

## Phase 6: User Story 4 - Ingestion Verification and Inspection (Priority: P2)

**Goal**: Verify pipeline completion and inspect vector collection

**Independent Test**: Run inspection after ingestion, verify collection exists with expected vector count and metadata

### Implementation for User Story 4

- [ ] T023 [US4] Add final statistics logging in `run_ingestion_pipeline()`: pages_fetched, chunks_created, vectors_stored, duration
- [ ] T024 [US4] Add collection inspection endpoint/method: list vectors with sample metadata from Qdrant
- [ ] T025 [US4] Add error tracking: collect and report all failures (fetch errors, extraction errors, API errors)
- [ ] T026 [US4] Add pipeline return codes: 0=success, 1=failure for CLI integration

**Checkpoint**: US4 complete - full visibility into pipeline execution and results

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Add comprehensive error handling: try/except for all network calls, graceful degradation on failures
- [ ] T028 [P] Verify idempotency: re-run pipeline produces same vector count (upsert replaces existing vectors)
- [ ] T029 Update backend/README.md with usage instructions from quickstart.md
- [ ] T030 Run full pipeline end-to-end with test data, verify all success criteria met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on US1 completion (needs fetched pages)
- **User Story 3 (Phase 5)**: Depends on US2 completion (needs chunks)
- **User Story 4 (Phase 6)**: Depends on US3 completion (needs stored vectors)
- **Polish (Phase 7)**: Depends on all user stories complete

### Sequential Execution (Single Developer)

```
T001-T003 (Setup) → T004-T007 (Foundational) → T008-T012 (US1) → T013-T017 (US2) → T018-T022 (US3) → T023-T026 (US4) → T027-T030 (Polish)
```

### Parallel Opportunities

- T002, T003 can run in parallel (install deps while documenting env vars)
- T004, T005, T007 can run in parallel (verify independent components)
- T008, T009, T010 can run in parallel (independent functions in main.py)
- T013, T014, T015 can run in parallel (independent functions in main.py)
- T018, T019 can run in parallel (independent functions in main.py)
- T027, T028 can run in parallel (independent polish tasks)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test URL discovery and fetching
5. Demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1: Fetch book pages → Test → Demo
3. US2: Extract & chunk text → Test → Demo
4. US3: Generate & store embeddings → Test → Demo (Full pipeline!)
5. US4: Add verification & logging → Test → Demo
6. Polish: Error handling, idempotency, documentation

### Full Pipeline Execution

```bash
cd backend
python main.py
```

Expected output:
```
Ingestion completed!
  - Pages fetched: X/Y
  - Chunks created: Z
  - Vectors stored: Z
  - Collection: book_knowledge_base
  - Duration: Mm Ss
```

---

## Notes

- All tasks target single file: backend/main.py
- Existing main.py (916 lines) already implements most functionality - verify and update as needed
- Key change: BOOK_BASE_URL replaces VERCEL_BOOK_URL
- Each phase checkpoint should be independently testable
- Commit after each task or logical group
- Total tasks: 30
