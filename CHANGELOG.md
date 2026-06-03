# Changelog

All notable changes to Agent 1 are documented here.

---

## [2.0.0] — 2026-06-03

### Added
- **Stage 1C — Requirement Enrichment** — new pipeline stage that runs after HITL 1 and before Stage 2. Enriches every requirement with clarification answers, upgrades confidence levels, fills dependencies, adds measurable acceptance criteria, and extracts key decisions
- **Decisions log** — key decisions made during clarification are now captured, named, and included in the scope document
- **Assumptions register** — stated assumptions (fired when clarification rounds exhaust) are now tracked in the session record and surfaced in the artefact
- **Full traceability chain** — every requirement in the markdown artefact now shows its complete chain: user input → ambiguity → HITL 1 answer → decision → validation flag → approval
- **Descriptive ambiguity IDs** — replaced M1/C1/V1 with descriptive slugs: `MISS-platform`, `CONF-offline-vs-sync`, `VAG-reminder-frequency`
- **Stable requirement IDs** — enforced REQ-YYYYMMDD-NNN format across all stages. Short IDs like R1, R2 are no longer generated
- **NFR extraction** — Stage 1A now explicitly extracts Non-Functional Requirements (power, storage, performance, reliability) as separate requirements
- **Rollback recovery path** — state machine now defines the full recovery path after rollback: ROLLBACK → CLARIFIED → re-validation pipeline
- **State machine transition rationale** — every state transition now records a rationale field in the version history
- **Blocking vs advisory flag separation** — the summary now clearly separates hard-block flags from soft advisory flags
- **Simultaneous JSON and markdown output** — every session now produces both a machine-readable JSON file and a human-readable markdown scope document in the output folder

### Changed
- **Validation is now evidence-based** — Stage 3 validator must cite direct evidence from the scope before flagging anything. Speculative risks and generic concerns are no longer flagged
- **Acceptance criteria require measurable thresholds** — vague criteria like "accurately tracks" are rejected in favour of "tracks within +/- 10ml"
- **Scope classification respects user intent** — explicitly requested features are never demoted to Future unless HITL 1 explicitly placed them behind a paywall or deferred them
- **Dependency inference is strict** — dependencies are only added when a requirement technically cannot function without another. Offline features no longer incorrectly depend on sync features
- **Reviewer justification enforced** — HITL 2 notes now require a minimum of 20 characters
- **Non-goal hallucination fixed** — Stage 2 now only creates non-goals from explicit HITL 1 statements. Absence of a topic in the conversation no longer creates a non-goal
- **Validation respects resolved conflicts** — Stage 3 no longer re-flags contradictions that were explicitly resolved during HITL 1
- **Confidence reassessment** — confidence is now reassessed based on answer quality, not just presence of an answer
- **Requirement text no longer truncated** — full descriptions are preserved in all display tables and artefacts
- **Domain-aware missing requirement detection** — Stage 3 checks for engineering-specific gaps based on product domain (hardware/IoT, mobile, web) rather than generic gaps
- **Artefact output changed from PDF to Markdown** — markdown is more portable and consumable by downstream agents and development teams

### Fixed
- Ethics validator hallucinating pricing concerns when no pricing model exists in scope
- Accessibility flags firing despite scope already covering multiple notification methods
- Phone sync being demoted to Nice-to-Have despite being explicitly requested by user
- REQ-003 (reminders) incorrectly depending on REQ-sync (reminders work offline)
- config.py duplicate key assignment causing 401 authentication errors
- Groq API key being committed to git history — pre-commit hook added to block future leaks

---

## [1.0.0] — 2026-05-30

### Added
- **Stage 1A — Requirement Extractor** — extracts atomic requirements from raw user input using Llama3-70b via Groq
- **Stage 1B — Ambiguity Detector** — identifies missing requirements, conflicts, and vague statements
- **HITL 1 — Intent Checkpoint** — interactive clarification loop with max 3 rounds and stated assumption fallback
- **Stage 2 — Scope Definition** — organises requirements into MVP, nice-to-have, future features, and explicit non-goals
- **Stage 3 — Validation Layer** — adversarial review including contradiction detection, scope explosion scoring, bias audit, and product ethics check
- **HITL 2 — Scope Approval** — human reviewer approves, rejects, or requests modification of the full validated scope
- **Session manager** — tracks all requirements, states, versions, flags, and produces the session record
- **State machine** — enforces valid state transitions with actor authority and hard-block flag checking
- **Scope explosion scoring** — five-factor weighted model (Requirement Impact, Architectural Expansion, Cross-Cutting Complexity, Timeline Pressure, Dependency Growth) with hard veto rules
- **Rich terminal display** — colour-coded tables showing output after every pipeline stage
- **Session persistence** — full session saved to JSON after every run
- **Groq integration** — OpenAI-compatible client using llama-3.3-70b-versatile for fast local development
- **Config-based model switching** — single config.py file controls all model and API settings

---

## Versioning

This project follows [Semantic Versioning](https://semver.org):
- **Major** — breaking changes to pipeline architecture or output format
- **Minor** — new features or stages added
- **Patch** — bug fixes and prompt improvements
