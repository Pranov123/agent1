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
│ Will the phone app be developed for iOS, Android,      │
│ or both?                                               │
╰────────────────────────────────────────────────────────╯
  Your answer: > iOS first, Android in a later phase
```

**Tips for answering:**
- Be specific — vague answers trigger another round
- You have 3 rounds maximum
- If you exhaust all 3 rounds without answering, the agent makes a conservative stated assumption and flags it clearly in the output

**Priority labels:**
- `P1` — must be answered before scoping can proceed
- `P2` — needed for specific features
- `P3` — can proceed with a stated assumption if unanswered

**Ambiguity ID format:**
- `MISS-<topic>` — missing information e.g. `MISS-platform`, `MISS-power-source`
- `CONF-<topic>` — conflict e.g. `CONF-offline-vs-sync`
- `VAG-<topic>` — vague statement e.g. `VAG-reminder-frequency`

---

### Step 5 — Requirement enrichment (Stage 1C)

After your clarification answers, the agent automatically enriches every requirement with everything learned during HITL 1:

```
── ENRICHED REQUIREMENTS (4) ──

  REQ-20260603-001
  Description: The smart water bottle shall remind the user to drink
               water at configurable intervals, default every 60 minutes
               between 8am and 10pm, using LED glow ring and vibration motor.
  Confidence:  🟢 HIGH
  Acceptance criteria:
    ✓ Reminder fires within 1 minute of scheduled time
    ✓ Reminder uses both visual and haptic alerts
    ✓ User can adjust frequency via phone app

── DECISIONS EXTRACTED (4) ──
  Use LED glow ring and vibration motor for reminders
  Use Bluetooth for syncing with phone
  ...
```

This step updates requirement descriptions, upgrades confidence levels, fills in dependencies, adds measurable acceptance criteria, and extracts key decisions. No input needed from you — it runs automatically.

---

### Step 6 — Review the scope definition

After enrichment, Stage 2 organises everything into four buckets:

```
── MVP SCOPE (6 items) ──
── NICE TO HAVE (0 items) ──
── FUTURE FEATURES (0 items) ──
── EXPLICIT NON-GOALS (2 items) ──
```

**What each bucket means:**
- **MVP** — the minimum set of features needed to ship a working product
- **Nice to have** — valuable features that are not launch-blocking
- **Future features** — explicitly deferred to a later phase
- **Non-goals** — things this product will deliberately never do in this phase, derived only from explicit HITL 1 decisions

Non-goals are never invented — they are always traceable to a specific answer you gave during HITL 1.

---

### Step 7 — Review validation findings

Stage 3 adversarially reviews the scope and shows you:

```
── MISSING REQUIREMENTS (2) ──
── SCOPE EXPLOSION ANALYSIS ──
   Weighted SSS: 38/100   Severity: Minor
── BIAS AUDIT (0) ──
── PRODUCT ETHICS (0) ──
```

The validator is evidence-based — it only flags issues that are directly supported by what is (or is not) in the scope. It will not invent risks.

**Scope Severity Score (SSS):**
- `0–35` Minor — healthy scope, safe to proceed
- `36–65` Medium — review carefully, consider splitting features
- `66–100` Major — scope is too large, must reduce before proceeding

---

### Step 8 — Approve or reject (HITL 2)

The full scope is shown with all validation flags. You make the final call:

```
REVIEWER ACTION
Options: approve / reject / modify

  Your reviewer ID: > reviewer_001
  Action (approve/reject/modify): > approve
  Notes (required — min 20 characters): > all NFRs captured, traceability complete, approved for handoff
```

- `approve` — all requirements are locked and saved to disk
- `reject` — all requirements are rejected with your reason recorded
- `modify` — requirements stay open, you can re-run with adjustments

> **Note:** Notes are required and must be at least 20 characters. This enforces meaningful reviewer justification.

---

### Step 9 — Session saved

```
✅ Session saved — output/SES-20260603-CEB396.json
📄 Markdown artefact — output/SES-20260603-CEB396_scope.md

SESSION SUMMARY
  Session ID   : SES-20260603-CEB396
  Requirements : 6
  Non-goals    : 2
  Open flags   : 0
  HITL1 rounds : 3
```

Two files are produced simultaneously — the full session JSON and the human-readable markdown scope document.

---

## Project Structure

```
agent1/
├── main.py                  # Entry point — run this
├── config.py                # All settings — API key, models, thresholds
├── core/
│   ├── __init__.py          # Client factory
│   ├── pipeline.py          # Main orchestrator — runs all 6 stages
│   ├── session_manager.py   # Tracks requirements, states, flags, versions,
│   │                        # decisions, assumptions, and produces session record
│   ├── state_machine.py     # Enforces valid state transitions, actor authority,
│   │                        # hard block flags, and rollback recovery
│   └── artefact_generator.py# Generates markdown scope document from session JSON
├── prompts/                 # Individual stage scripts for prompt testing
│   ├── stage1a_extractor.py # Requirement extraction
│   ├── stage1b_ambiguity.py # Ambiguity detection
│   ├── hitl1_checkpoint.py  # Clarification loop
│   ├── stage2_scope.py      # Scope definition
│   └── stage3_validation.py # Adversarial validation
├── output/                  # Session JSON and markdown artefacts saved here
└── logs/                    # Log files
```
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