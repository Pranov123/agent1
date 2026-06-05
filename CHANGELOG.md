# Changelog

All notable changes to Agent 1 are documented here.

---

## [3.0.0] — 2026-06-05

### Added

* **ETHOS Governance Pipeline (Stage 0)** — introduced a dedicated governance and risk assessment layer that executes before requirement extraction and scope generation
* **Semantic Domain Inference Engine** — classifies projects into domain categories such as consumer applications, SaaS, healthcare, fintech, HR/workforce, hardware/IoT, education, legal/compliance, social platforms, ecommerce, and productivity tools
* **Risk Pattern Detection Engine** — independently identifies governance-relevant patterns including employee monitoring, covert surveillance, algorithmic decision-making, regulated health data, financial data, behavioural profiling, location tracking, third-party data sharing, child-related risks, and data retention concerns
* **Dual-Model Validation Architecture** — separated domain classification and risk pattern analysis into independent LLM validation stages to reduce single-model bias
* **Confidence Band Framework** — introduced HIGH, UNCERTAIN, and LOW confidence bands to distinguish certainty of classification from actual risk severity
* **Risk Tier Framework** — introduced LOW, MEDIUM, and HIGH governance risk tiers based on detected evidence rather than confidence scores
* **Governance Decision Engine** — automatically determines required review level, audit requirements, escalation path, and governance controls
* **Pattern Severity Scoring System** — weighted severity model that evaluates risk signals using configurable pattern weights and confidence scores
* **Risk Category Classification** — classifies governance concerns into Privacy, Surveillance, Regulatory, Safety, Employment Decision, and Algorithmic Decision categories
* **Auto-Escalation Engine** — immediate escalation path for clinical healthcare systems, financial systems, legal/compliance platforms, covert surveillance systems, and other explicitly regulated domains
* **Governance Traceability Layer** — every governance decision now records escalation source, severity score, confidence score, risk category, and review rationale
* **Ambiguity-Aware Governance** — low-confidence classifications now automatically trigger human review requirements and clarification workflows
* **Governance Metadata Export** — ETHOS outputs are now included in the final session artefact and available for downstream agents and reviewers

### Changed

* **Risk assessment now occurs before scope generation** — governance evaluation is performed on raw user intent before requirements are extracted
* **Confidence and risk are now independent concepts** — a system may be confidently classified as low risk or uncertainly classified as high risk without conflating the two
* **Evidence-based governance decisions** — risk tiers are determined from detected evidence rather than solely from domain classification
* **HR/workforce classification redesigned** — workforce management systems are now treated as neutral domains and no longer automatically escalate to high-risk status
* **Healthcare classification narrowed** — healthcare domain now only applies to clinical, diagnostic, treatment, patient-record, or regulated medical systems; wellness and fitness applications remain consumer applications
* **Child-related risk detection refined** — separated legitimate educational systems from child exploitation and sensitive child-data processing risks
* **Employee monitoring detection hardened** — monitoring patterns now require explicit evidence of surveillance, productivity tracking, communication recording, keystroke logging, or similar behaviour-monitoring activities
* **Confidence calculation redesigned** — confidence now combines domain certainty, pattern certainty, disagreement penalties, and input quality scoring
* **Governance controls decoupled from risk tier** — review requirements can be elevated due to uncertainty without artificially inflating risk classification
* **Pattern severity thresholds recalibrated** — medium and high-risk escalation thresholds updated to reduce false positives while preserving safety coverage
* **Input quality assessment introduced** — vague project descriptions now reduce classification confidence while detailed specifications increase confidence
* **School administration systems reclassified** — attendance tracking, grades, parent notifications, and learning management functions are no longer automatically treated as privacy risks
* **Risk category naming standardised** — governance outputs now use consistent category labels across all pipeline stages and artefacts

### Fixed

* HR leave-management systems incorrectly escalating to HIGH risk despite containing no monitoring behaviour
* Ambiguous manager-assistance tools being incorrectly classified as surveillance systems
* School attendance systems triggering child-related privacy flags without evidence of sensitive data processing
* Educational software being flagged as child exploitation risk solely because children were mentioned
* Attendance tracking triggering PII-handling risk patterns despite no explicit personal-data processing being described
* Workforce scheduling and leave-management systems being confused with employee-monitoring systems
* Confidence score flattening issue causing nearly all projects to receive similar confidence values
* Excessive risk inflation caused by domain classification overriding pattern evidence
* Surveillance category being assigned to legitimate HR administration tools
* Healthcare detection incorrectly classifying wellness, hydration, and fitness applications as regulated medical systems
* False-positive behavioural profiling flags triggered by generic application analytics
* Generic productivity and SaaS platforms being unnecessarily escalated for governance review
* Pattern severity calculations producing inconsistent escalation outcomes across equivalent inputs
* Governance review recommendations not accurately reflecting confidence uncertainty levels
* Risk classification traceability gaps preventing reviewers from understanding escalation rationale

### Internal Architecture

* Added `ETHOSEngine` as a dedicated governance orchestration component
* Added semantic domain classification subsystem
* Added independent risk-pattern detection subsystem
* Added severity-weighted aggregation engine
* Added confidence-band evaluator
* Added governance decision builder
* Added risk-category classifier
* Added auto-escalation framework
* Added ambiguity review workflow
* Added governance traceability reporting
* Added input-quality scoring module
* Added pattern severity weighting configuration
* Added governance metadata export layer

### Governance Outcomes

The ETHOS pipeline now produces:

* Risk Tier (`LOW`, `MEDIUM`, `HIGH`)
* Risk Category (`NONE`, `PRIVACY`, `SURVEILLANCE`, `REGULATORY`, `SAFETY`, `EMPLOYMENT_DECISION`, `ALGORITHMIC_DECISION`)
* Confidence Score
* Confidence Band (`HIGH`, `UNCERTAIN`, `LOW`)
* Governance Requirements
* Recommended Review Level
* Escalation Reason
* Auto-Escalation Status
* Pattern Severity Score
* Human Review Requirements
* Domain Classification Metadata
* Pattern Detection Metadata
* Full Governance Audit Trail

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
