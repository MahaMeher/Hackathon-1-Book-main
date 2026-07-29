---

description: "Task list for Frontend & Backend Integration feature"

---

# Tasks: Frontend & Backend Integration

**Input**: Design documents from `/specs/008-frontend-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add backend dependencies and create the FastAPI server skeleton.

- [X] T001 Add fastapi[standard] and uvicorn[standard] to dependencies in backend/pyproject.toml
- [X] T002 Create backend/api.py with FastAPI app instance, CORS middleware (allow localhost:3000), and a health-check GET /api/health endpoint

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core frontend infrastructure that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Create Frontend_book/src/components/ChatBot/ directory with empty index.jsx, ChatBot.css, and ChatBotAPI.js files
- [X] T004 [P] Create ChatBotAPI.js fetch helper in Frontend_book/src/components/ChatBot/ChatBotAPI.js with sendQuery() function that POSTs to /api/chat and returns parsed JSON

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Ask a Question via Chatbot (Priority: P1) 🎯 MVP

**Goal**: A reader can type a question into the chatbot and receive a grounded answer from the book content.

**Independent Test**: Start the backend (`uvicorn api:app --port 8000`) and frontend (`npm start`). Navigate to any book page. Type "What is ROS 2?" in the chatbot. Verify a response appears within 5 seconds with source citations referencing specific book content.

### Implementation for User Story 1

- [X] T005 [US1] Implement POST /api/chat endpoint in backend/api.py that instantiates RAGChatbot, calls ask(query), and returns the ChatResponse as JSON (status 200) or an error response (status 500)
- [X] T006 [US1] Create ChatBot main React component in Frontend_book/src/components/ChatBot/index.js with a text input, submit button, and message list that displays user queries and assistant responses
- [X] T007 [US1] Embed the ChatBot component on Docusaurus book pages by rendering it inside the Layout or via a custom Root theme component in Frontend_book/src/theme/Root.js
- [X] T008 [US1] Configure Docusaurus devServer proxy in Frontend_book/docusaurus.config.js to forward /api/* requests to http://localhost:8000
- [X] T009 [US1] End-to-end verification: start backend + frontend, submit a query via the chatbot UI, confirm response displays with source citations

**Checkpoint**: At this point, User Story 1 should be fully functional — users can ask questions and get grounded answers with source citations.

---

## Phase 4: User Story 2 — Ask About Selected Text (Priority: P1)

**Goal**: A reader can select text on a book page and use it as context for a more targeted chatbot question.

**Independent Test**: Select any paragraph on a book page. Click the "Ask about this selection" trigger that appears. The chat input opens with context. Type a question. Verify the backend response references both the selected passage and the broader book content.

### Implementation for User Story 2

- [X] T010 [P] [US2] Add optional selected_context parameter to RAGChatbot.ask() in backend/rag_chatbot.py and include it as additional context in _build_prompt()
- [X] T011 [P] [US2] Implement text selection detection using window.getSelection() on mouseup in Frontend_book/src/components/ChatBot/index.js, showing a floating "Ask about this selection" button near the selected text
- [X] T012 [US2] Wire the "Ask about this selection" button click to open the chat input with the selected text as context and call sendQuery() with selected_context in the POST body
- [X] T013 [US2] End-to-end verification: select text on a book page, trigger the action, submit a contextual question, confirm the answer references the selected passage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 — Handle Connection Errors Gracefully (Priority: P2)

**Goal**: Users see clear, friendly messages when the backend is unreachable, a query is empty, or no relevant content is found.

**Independent Test**: Stop the backend server. Open the chatbot. Verify a "Service unavailable" message displays (not a network error or blank screen). Start the backend again. Submit an empty query — verify it is prevented. Submit a valid query — verify it works again.

### Implementation for User Story 3

- [X] T014 [P] [US3] Add error handling in ChatBotAPI.js sendQuery() that catches network errors and returns a user-friendly error object instead of throwing
- [X] T015 [P] [US3] Add loading spinner state to ChatBot component in index.js that disables the submit button during query processing
- [X] T016 [US3] Add empty query validation in ChatBot component that prevents submission if the input is blank or whitespace-only
- [X] T017 [US3] Add "no results" messaging in ChatBot component that displays a helpful suggestion when the backend returns zero relevant sources
- [X] T018 [US3] Test all error scenarios: backend offline (friendly "Service unavailable"), empty query (prevented with message), no results (helpful suggestion shown)

**Checkpoint**: All user stories should now be independently functional. Error scenarios are handled gracefully without exposing raw errors.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup.

- [X] T019 Run quickstart.md validation steps to verify end-to-end workflow: backend starts, frontend starts, chatbot visible, query works, selected text works, error states handled
- [X] T020 Verify chatbot works on multiple book content pages (not just one test page) — Root.js wrapper renders ChatBot on every page by design
- [X] T021 Code review: check for hardcoded URLs, missing error boundaries, and consistent UI feedback

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US2 (selected text) depends on US1 (chat endpoint + component) for its chat infrastructure
  - US3 (error handling) can be implemented alongside US1/US2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Priority | Depends On | Independently Testable |
|-------|----------|------------|----------------------|
| US1 — Ask a question | P1 | Foundational | ✅ Yes — test with curl or browser |
| US2 — Selected text | P1 | US1 (chat infrastructure) | ✅ Yes — test with text selected |
| US3 — Error handling | P2 | US1 (chat component) | ✅ Yes — test by stopping backend |

### Within Each User Story

- Component infrastructure before endpoint integration
- Backend endpoint before frontend integration
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

| Phase | [P] Tasks | Can Run Together |
|-------|-----------|------------------|
| Foundational | T003, T004 | Create directory + API helper simultaneously |
| US2 | T010, T011 | Backend selected_context + frontend selection detection |
| US3 | T014, T015 | Error handling + loading spinner simultaneously |

## Parallel Example: User Story 2

```bash
# Backend task:
Task: T010 — Add selected_context to RAGChatbot.ask() in backend/rag_chatbot.py

# Frontend task (runs in parallel — different file, no dependency):
Task: T011 — Implement text selection detection in Frontend_book/src/components/ChatBot/index.jsx
```

## Parallel Example: User Story 3

```bash
# Both tasks are on different files with no cross-dependency:
Task: T014 — Error handling in ChatBotAPI.js
Task: T015 — Loading spinner in ChatBot/index.jsx
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add FastAPI deps + API skeleton)
2. Complete Phase 2: Foundational (directory + API helper)
3. Complete Phase 3: User Story 1 (chat endpoint + component)
4. **STOP and VALIDATE**: Test US1 independently — type a query, verify response
5. Deploy/demo if ready

### Incremental Delivery

1. **Setup + Foundational** → Backend skeleton + frontend helper ready
2. **User Story 1** → Basic chatbot works (MVP — can ask questions and get answers)
3. **User Story 2** → Selected-text context adds precision (enhanced UX)
4. **User Story 3** → Error handling makes it production-ready locally
5. Each story adds value without breaking previous stories

### Single-Developer Strategy

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009
                                                           ↓
                                              T010 → T011 → T012 → T013
                                                                    ↓
                                                        T014 → T015 → T016 → T017 → T018
                                                                                         ↓
                                                                                 T019 → T020 → T021
```

Backend tasks (T001, T002, T005, T010) and frontend tasks (T003, T004, T006-T009, T011-T021) can be interleaved.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No test tasks generated (not requested in spec — the spec does not mandate TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
