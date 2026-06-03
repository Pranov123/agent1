# Agent 1 — Requirement Scoping Agent

> **Transform any raw idea into a structured, validated, human-approved scope document.**

Agent 1 is an AI-powered requirement scoping pipeline. You give it a raw idea — messy, vague, unstructured — and it extracts requirements, detects ambiguities, asks you targeted clarification questions, organises everything into MVP / nice-to-have / future / non-goals, validates the scope adversarially, and produces a fully traceable output ready for downstream development.

---

## Table of Contents

- [What It Does](#what-it-does)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Agent](#running-the-agent)
- [Walkthrough — First Run](#walkthrough--first-run)
- [Understanding the Output](#understanding-the-output)
- [Project Structure](#project-structure)
- [Example Inputs](#example-inputs)
- [Troubleshooting](#troubleshooting)

---

## What It Does

You type (or paste) a raw idea like this:

```
I want to build an app where users can track their habits and maybe share them 
with friends and get reminders and it should work offline and maybe have some AI 
that gives suggestions and I want it to be free but also make money somehow
```

Agent 1 runs it through a five-stage pipeline and produces:

- A structured list of requirements — each with a unique ID, category, priority, and status
- An ambiguity report — missing information, conflicts, and vague statements
- A clarified scope split into four buckets — MVP, nice-to-have, future features, and explicit non-goals
- A validation report — contradictions, missing requirements, scope explosion score, bias audit, product ethics check
- A full session record saved to disk — versioned, traceable, auditable

---

## How It Works

```
Your input
    │
    ├─── Stage 1A: Requirement Extractor
    │         Extracts atomic requirements from raw input
    │
    ├─── Stage 1B: Ambiguity Detector
    │         Finds missing info, conflicts, vague statements
    │
    ├─── HITL 1: Intent Checkpoint
    │         YOU answer clarification questions (max 3 rounds)
    |
    ├─── Stage 1C: Requirement Enrichment
    │         Enriches each requirement with clarification answers,
    │         updates confidence levels, fills dependencies,
    │         adds acceptance criteria, extracts key decisions
    │
    ├─── Stage 2: Scope Definition
    │         Organises into MVP / nice-to-have / future / non-goals
    │
    ├─── Stage 3: Validation Layer
    │         Adversarial review — finds contradictions, gaps, risks
    │
    └─── HITL 2: Scope Approval
              YOU review the full scope and approve / reject / modify
```

HITL = Human In The Loop. The agent never approves its own output — you do.

---

## Prerequisites

- Python 3.11 or later
- A [Groq API key](https://console.groq.com) — free to sign up

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/agent1.git
cd agent1
```

### 2. Create a virtual environment

```bash
python3 -m venv env
source env/bin/activate        # Linux / Mac
# env\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install openai pydantic rich
```

### 4. Get a Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Click **API Keys** → **Create Key**
4. Copy the key — you only see it once

### 5. Add your API key

Open `config.py` and paste your key:

```python
GROQ_API_KEY = "your-groq-key-here"
```

---

## Configuration

All settings live in `config.py`. The defaults work out of the box — the only thing you need to change is your API key.

```python
# Your Groq API key — required
GROQ_API_KEY = "your-groq-key-here"

# Model used for all pipeline stages
GROQ_PRIMARY_MODEL    = "llama-3.3-70b-versatile"
GROQ_VALIDATION_MODEL = "llama-3.3-70b-versatile"

# Maximum clarification rounds before assumptions fire (default: 3)
MAX_CLARIFICATION_ROUNDS = 3

# Request timeout in seconds (default: 600)
REQUEST_TIMEOUT = 600.0
```

---

## Running the Agent

### Interactive mode (recommended)

```bash
python3 main.py
```

The agent will prompt you to enter your idea. Type or paste it and press Enter.

### Command line mode

```bash
python3 main.py "I want to build a tool that helps restaurant owners manage tables and take orders on tablets"
```

---

## Walkthrough — First Run

Here is exactly what happens when you run the agent:

### Step 1 — Enter your idea

```
Enter your idea, feature request, or requirement.
Be as raw and unfiltered as you want — Agent 1 will structure it.
──────────────────────────────────────────────────
> I want to build an app where users can track their habits...
```

Be as raw and unpolished as you want. The messier the input, the more useful the clarification process.

### Step 2 — Watch Stage 1A extract requirements

The agent immediately shows you a table of extracted requirements:

```
✓ Extracted 8 requirements
┌─────────────────────┬──────────────────┬────────────┬────────────┬──────────────────────────┐
│ UID                 │ Title            │ Priority   │ Confidence │ Description              │
├─────────────────────┼──────────────────┼────────────┼────────────┼──────────────────────────┤
│ REQ-20260530-001    │ Habit Tracking   │ Critical   │ HIGH       │ System must allow...     │
│ REQ-20260530-002    │ Social Sharing   │ Low        │ LOW        │ System may allow...      │
└─────────────────────┴──────────────────┴────────────┴────────────┴──────────────────────────┘
```

**Confidence** tells you how clearly the requirement was stated:
- `HIGH` — clearly stated in the input
- `MEDIUM` — implied but not stated
- `LOW` — user said "maybe" or "could"

### Step 3 — Review ambiguity findings

Stage 1B shows you what is missing, conflicting, or vague:

```
⚠ Found 8 ambiguities
── MISSING REQUIREMENTS (4) ──
── CONFLICTS (1) ──
── VAGUE STATEMENTS (3) ──
```

### Step 4 — Answer clarification questions (HITL 1)

The agent asks you up to 5 questions per round, highest priority first:

```
── Round 1 of 3 ──

╭─── Q1 (P1) ────────────────────────────────────────────╮
│ How does the app plan to make money while being free?  │
╰────────────────────────────────────────────────────────╯
  Your answer: > freemium — basic features free, AI behind paywall
```

**Tips for answering:**
- Be specific — vague answers trigger another round
- You have 3 rounds maximum
- If you exhaust all 3 rounds without answering, the agent makes a conservative stated assumption and flags it clearly in the output

**Priority labels:**
- `P1` — must be answered before scoping can proceed
- `P2` — needed for specific features
- `P3` — can proceed with a stated assumption if unanswered

### Step 5 — Review the scope definition

After your answers, Stage 2 organises everything into four buckets:

```
── MVP SCOPE (5 items) ──
── NICE TO HAVE (1 items) ──
── FUTURE FEATURES (2 items) ──
── EXPLICIT NON-GOALS (3 items) ──
```

**What each bucket means:**
- **MVP** — the minimum set of features needed to ship a working product
- **Nice to have** — valuable features that are not launch-blocking
- **Future features** — explicitly deferred to a later phase
- **Non-goals** — things this product will deliberately never do in this phase, derived from your HITL 1 answers

### Step 6 — Review validation findings

Stage 3 adversarially reviews the scope and shows you:

```
── CONTRADICTIONS (1) ──
── MISSING REQUIREMENTS (1) ──
── SCOPE EXPLOSION ANALYSIS ──
   Weighted SSS: 42/100   Severity: Minor
── BIAS AUDIT (1) ──
── PRODUCT ETHICS (1) ──
```

**Scope Severity Score (SSS):**
- `0–35` Minor — healthy scope, safe to proceed
- `36–65` Medium — review carefully, consider splitting features
- `66–100` Major — scope is too large, must reduce before proceeding

### Step 7 — Approve or reject (HITL 2)

The full scope is shown with all validation flags. You make the final call:

```
REVIEWER ACTION
Options: approve / reject / modify

  Your reviewer ID: > reviewer_001
  Action: > approve
  Notes: > acknowledged bias flag, auth to be added next iteration
```

- `approve` — all requirements are locked and saved to disk
- `reject` — all requirements are rejected with your reason recorded
- `modify` — requirements stay open, you can re-run with adjustments

### Step 8 — Session saved

```
✅ Session complete — saved to output/SES-20260530-ABC123.json

SESSION SUMMARY
  Session ID   : SES-20260530-ABC123
  Requirements : 8
  Non-goals    : 3
  Open flags   : 3
  HITL1 rounds : 2
```

Your full session is saved to the `output/` folder as a JSON file.

---

## Understanding the Output

Every run produces two files in the `output/` folder with the same session ID:

```
output/
├── SES-20260603-CEB396.json         ← full session data (machine readable)
└── SES-20260603-CEB396_scope.md     ← scope document (human readable)
```

The markdown file is the primary deliverable — it is the document you hand off to your development team.

---

### Scope Document (\_scope.md)

The markdown artefact contains eight sections:

| Section | Contents |
| --- | --- |
| **1. Summary** | Requirement counts, flag counts, original input |
| **2. Key Decisions** | Decisions made during clarification with rationale and affected requirements |
| **3. Scope Definition** | MVP, nice-to-have, and future features in tables |
| **4. Explicit Non-Goals** | Hard boundaries derived from HITL 1 decisions |
| **5. Requirements Detail** | Full spec per requirement — description, acceptance criteria, traceability chain, dependencies, flags |
| **6. Validation Report** | Scope explosion score, contradictions, missing requirements, bias and ethics flags |
| **7. Assumptions Register** | Any stated assumptions made when clarification rounds were exhausted |
| **8. Review Log** | Full audit trail — HITL 1 answers and HITL 2 approval |

---

### Requirement Lifecycle

Requirements move through these states during the pipeline:

```
DRAFT → EXTRACTED → CLARIFICATION_PENDING → CLARIFIED → VALIDATED → HUMAN_REVIEW → APPROVED → LOCKED
```

After HITL 2 approval all requirements are `LOCKED` — they cannot be changed without a formal change request.

---

### Flag Types

| Flag | Type | Blocks approval? |
| --- | --- | --- |
| `COMPLIANCE_HOLD` | Hard block | Yes — must be resolved |
| `LEGAL_CONFLICT` | Hard block | Yes — must be resolved |
| `NON_GOAL_CONFLICT` | Hard block | Yes — must be resolved |
| `BIAS_AUDIT` | Advisory | No — informational only |
| `ACCESSIBILITY_OMISSION` | Advisory | No — informational only |
| `PRODUCT_ETHICS` | Advisory | No — informational only |
| `CONTRADICTION` | Advisory | No — informational only |

Hard flags block the approval transition until resolved. Advisory flags are surfaced for reviewer awareness but do not block the pipeline.

---

### Traceability Chain

Every requirement in the scope document includes a full traceability chain showing exactly how it evolved:

| Stage | What it shows |
| --- | --- |
| 📝 User Input | The exact phrase from the original input that led to this requirement |
| ❓ Ambiguity | Which ambiguities were raised about this requirement |
| 💬 HITL 1 Answer | The human answers that resolved those ambiguities |
| 📌 Decision | Key decisions that shaped this requirement |
| ⚠️ / 🚫 Validation Flag | Any flags raised during Stage 3 validation |
| ✅ Approval | Who approved it and when |

## Project Structure

```
agent1/
├── main.py                  # Entry point — run this
├── config.py                # All settings — API key, models, thresholds
├── core/
│   ├── __init__.py          # Client factory
│   ├── pipeline.py          # Main orchestrator — runs all 6 stages (1A, 1B, HITL1, 1C, 2, 3)
│   ├── session_manager.py   # Tracks requirements, states, flags, versions
│   └── state_machine.py     # Enforces valid state transitions
├── prompts/                 # Individual stage scripts for testing
│   ├── stage1a_extractor.py
│   ├── stage1b_ambiguity.py
│   ├── hitl1_checkpoint.py
│   ├── stage2_scope.py
│   └── stage3_validation.py
├── output/                  # Session JSON files saved here
└── logs/                    # Log files
```

---

## Example Inputs

Agent 1 works on any domain. Here are some examples to try:

**SaaS product:**
```
I want to build a tool for freelancers to track their invoices, send payment 
reminders automatically, and see which clients pay late. Should integrate with 
Stripe somehow.
```

**Internal tool:**
```
We need a system where HR managers can track employee onboarding steps, assign 
tasks to different departments, and see which new hires are blocked on paperwork.
```

**Consumer app:**
```
An app for dog owners to track their dog's health — vet visits, vaccinations, 
medications, and share updates with a dog sitter when they travel.
```

**Hardware product:**
```
A smart water bottle that reminds you to drink water, tracks your daily intake, 
and syncs with your phone. Should work without the phone nearby.
```

**Restaurant tool:**
```
A tool for small restaurant owners to manage their tables, take orders on a 
tablet, split bills between customers, and track which dishes are selling well. 
Needs to work even when the wifi goes down.
```

---

## Troubleshooting

### JSON parse error

```
❌ JSON parse failed: Expecting value
```

The model returned malformed JSON. This happens occasionally. Just re-run — the model will produce clean output on the next attempt.

### Groq rate limit

```
Error 429: Rate limit exceeded
```

Groq free tier has rate limits. Wait 60 seconds and re-run. For heavy usage consider upgrading your Groq plan.

### Approved: 0 requirements

Requirements didn't flow through the state machine correctly. This usually means Stage 2 returned an empty scope. Re-run the pipeline — it is a model consistency issue that resolves on retry.

### API key error

```
Error 401: Invalid API key
```

Check that your API key in `config.py` is correct and has not expired. Generate a new one at [console.groq.com](https://console.groq.com) if needed.

### Timeout error

```
openai.APITimeoutError: Request timed out
```

Increase the timeout in `config.py`:

```python
REQUEST_TIMEOUT = 1200.0
```

---

## License

MIT

---

## Built with

- [Groq](https://groq.com) — fast LLM inference
- [Rich](https://github.com/Textualize/rich) — terminal formatting
- [Pydantic](https://docs.pydantic.dev) — data validation
- [OpenAI Python SDK](https://github.com/openai/openai-python) — API client