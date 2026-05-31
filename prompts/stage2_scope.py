from openai import OpenAI
import json

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your-groq-key-here",
    timeout=600.0
)

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Scope Definition engine for Agent 1, a requirement scoping pipeline.

YOUR JOB:
You receive the extracted requirements (Stage 1A) and all clarifications from HITL 1.
You organise everything into a clean, structured scope document.

YOU MUST PRODUCE FOUR BUCKETS:

BUCKET 1 — MVP SCOPE
The absolute minimum set of requirements needed for a working, shippable product.
Rules:
- Only include what is CRITICAL or HIGH priority AND clearly stated
- If removing it would make the product unusable, it belongs here
- Keep this tight — scope creep starts here

BUCKET 2 — NICE TO HAVE
Valuable features that improve the product but are not launch-blocking.
Rules:
- Medium priority items that enhance the core experience
- Features the user expressed interest in but hedged with "maybe" or "could"
- Nothing that requires the MVP to be complete first goes here

BUCKET 3 — FUTURE FEATURES
Features that are explicitly deferred — not forgotten, just not now.
Rules:
- Low priority items
- Features that depend on MVP being stable and successful first
- Complex integrations that would delay launch significantly

BUCKET 4 — EXPLICIT NON-GOALS
What this product will DELIBERATELY never do in this phase.
Rules:
- Not "we might do this later" — these are hard boundaries
- Derive from: platform decisions, data decisions, monetisation decisions made at HITL 1
- Every non-goal gets a NG-UID in format NG-YYYYMMDD-NNN
- Every non-goal must have a reason — why is this explicitly out of scope?

STRICT RULES:

1. EVERY requirement from Stage 1A must appear in exactly one bucket
   Nothing gets lost. Nothing gets duplicated.

2. USE the HITL 1 resolutions to make placement decisions
   If HITL 1 said "AI is behind paywall" — AI goes to Future, not MVP

3. NON-GOALS must be derived from actual decisions made
   BAD: "No blockchain integration" (was never discussed)
   GOOD: "No server-side health data storage" (explicitly decided at HITL 1)
   GOOD: "No web app" (platform decision made at HITL 1)
   GOOD: "No Android app in this phase" (explicitly decided at HITL 1)
   NEVER invent non-goals. Only derive from actual HITL 1 decisions.

4. Each requirement keeps its original UID from Stage 1A
   Do not rename or re-number requirements

5. New requirements surfaced during scoping get a new UID
   Format: REQ-YYYYMMDD-NNN (continuing from last Stage 1A uid)

6. Every requirement must have:
   - uid, title, description, category, priority, status, dependencies
   - scope_bucket: MVP / NICE_TO_HAVE / FUTURE / NON_GOAL
   - placement_reason: why it was placed in this bucket

OUTPUT FORMAT:
Respond ONLY with valid JSON — no preamble, no explanation:
{
  "session_id": "SES-YYYYMMDD-001",
  "mvp_scope": [
    {
      "uid": "REQ-YYYYMMDD-001",
      "title": "short title",
      "description": "clear testable description",
      "category": "Functional/Non-functional/Constraint",
      "priority": "Critical/High/Medium/Low",
      "status": "CLARIFIED",
      "dependencies": [],
      "scope_bucket": "MVP",
      "placement_reason": "why this is MVP"
    }
  ],
  "nice_to_have": [],
  "future_features": [],
  "non_goals": [
    {
      "uid": "NG-YYYYMMDD-001",
      "title": "short title",
      "description": "what is explicitly excluded",
      "reason": "why this is out of scope",
      "status": "ACTIVE",
      "source": "HITL1_decision/scope_boundary/platform_decision"
    }
  ],
  "new_requirements_surfaced": [],
  "scope_summary": "one paragraph summary of the scope decisions made"
}"""

# ── Load all previous outputs ─────────────────────────────────
stage1a_output = {
    "session_id": "SES-20231012-001",
    "requirements": [
        {"uid": "REQ-20230601-001", "title": "Habit Tracking", "category": "Functional",
         "priority": "High", "confidence": "HIGH",
         "description": "System must allow users to track their habits"},
        {"uid": "REQ-20230601-002", "title": "Social Sharing", "category": "Functional",
         "priority": "Medium", "confidence": "LOW",
         "description": "System may allow users to share their habits with friends"},
        {"uid": "REQ-20230601-003", "title": "Reminders", "category": "Functional",
         "priority": "Medium", "confidence": "HIGH",
         "description": "System must provide reminders to users"},
        {"uid": "REQ-20230601-004", "title": "Offline Functionality", "category": "Non-functional",
         "priority": "High", "confidence": "HIGH",
         "description": "System must work offline"},
        {"uid": "REQ-20230601-005", "title": "AI Suggestions", "category": "Functional",
         "priority": "Low", "confidence": "LOW",
         "description": "System may provide AI-driven suggestions to users"},
        {"uid": "REQ-20230601-006", "title": "Apple Health Integration", "category": "Functional",
         "priority": "Low", "confidence": "LOW",
         "description": "System may integrate with Apple Health"},
        {"uid": "REQ-20230601-007", "title": "Free Access", "category": "Constraint",
         "priority": "High", "confidence": "HIGH",
         "description": "System must be free to use"},
        {"uid": "REQ-20230601-008", "title": "Monetization", "category": "Constraint",
         "priority": "High", "confidence": "HIGH",
         "description": "System must generate revenue"},
    ]
}

hitl1_output = {
    "session_id": "SES-20231012-001",
    "rounds_used": 3,
    "resolutions": [
        {"ambiguity_ref": "M1", "status": "RESOLVED",
         "human_answer": "iOS first, Android later",
         "resolution_note": "App will be developed for iOS first"},
        {"ambiguity_ref": "M2", "status": "RESOLVED",
         "human_answer": "users own their data",
         "resolution_note": "Users have full ownership of their data"},
        {"ambiguity_ref": "M3", "status": "RESOLVED",
         "human_answer": "email login",
         "resolution_note": "Users will log in using email"},
        {"ambiguity_ref": "M4", "status": "RESOLVED",
         "human_answer": "freemium",
         "resolution_note": "App will use a freemium monetization model"},
        {"ambiguity_ref": "C1", "status": "RESOLVED",
         "human_answer": "free with premium features, AI and health sync behind paywall",
         "resolution_note": "AI and health sync are paid features"},
        {"ambiguity_ref": "V1", "status": "RESOLVED",
         "human_answer": "habit patterns and completion streaks",
         "resolution_note": "AI suggestions based on habit patterns and streaks"},
        {"ambiguity_ref": "V2", "status": "RESOLVED",
         "human_answer": "core habit tracking only, sync when back online",
         "resolution_note": "Offline covers core tracking only"},
        {"ambiguity_ref": "V3", "status": "RESOLVED",
         "human_answer": "read only data sync, no storage on our servers",
         "resolution_note": "Apple Health read-only, no server storage"},
        {"ambiguity_ref": "V4", "status": "RESOLVED",
         "human_answer": "in-app purchases for premium features",
         "resolution_note": "Monetization via in-app purchases"},
    ],
    "assumptions_fired": []
}

# ── Run scope definition ──────────────────────────────────────
def run_scope_definition(stage1a: dict, hitl1: dict) -> dict:
    print("\n⏳ Running Stage 2 — Scope Definition...\n")

    context = f"""
Stage 1A extracted requirements:
{json.dumps(stage1a['requirements'], indent=2)}

HITL 1 clarifications and resolutions:
{json.dumps(hitl1['resolutions'], indent=2)}

New requirements that were surfaced during clarification:
- User authentication / email login (surfaced from M3 resolution)

Using all of the above, define the full scope.
Organise into MVP, Nice-to-have, Future, and Non-goals.
Remember: AI features and Apple Health are behind the paywall — Future tier.
CRITICAL: Non-goals must ONLY come from these explicit HITL 1 decisions:
1. No Android app in this phase (M1 resolution)
2. No server-side health data storage (V3 resolution)
3. No web app — iOS only (M1 resolution)
Do NOT add any other non-goals. Blockchain was never mentioned. Do not invent it.
REMINDERS (REQ-20230601-003) must be in MVP — clearly stated in original input with no hedging.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")
        print(f"Raw output:\n{raw}")
        return {}

# ── Display results ───────────────────────────────────────────
def display_results(result: dict):
    if not result:
        return

    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()

    console.print(f"\n[bold purple]SESSION:[/bold purple] {result.get('session_id')}")

    bucket_config = [
        ("mvp_scope",       "MVP SCOPE",        "bold green",   "green"),
        ("nice_to_have",    "NICE TO HAVE",     "bold yellow",  "yellow"),
        ("future_features", "FUTURE FEATURES",  "bold cyan",    "cyan"),
    ]

    for key, label, header_style, border_style in bucket_config:
        items = result.get(key, [])
        if not items:
            continue

        console.print(f"\n[{header_style}]── {label} ({len(items)} items) ──[/{header_style}]")
        t = Table(show_header=True, header_style=header_style)
        t.add_column("UID", width=20)
        t.add_column("Title", width=24)
        t.add_column("Priority", width=10)
        t.add_column("Description", width=38)
        t.add_column("Placement Reason", width=32)

        for item in items:
            p_color = {"Critical":"red","High":"orange3",
                      "Medium":"yellow","Low":"green"}.get(item.get("priority"),"white")
            t.add_row(
                item.get("uid",""),
                item.get("title",""),
                f"[{p_color}]{item.get('priority','')}[/{p_color}]",
                item.get("description","")[:80],
                item.get("placement_reason","")[:60]
            )
        console.print(t)

    # non-goals
    non_goals = result.get("non_goals", [])
    if non_goals:
        console.print(f"\n[bold red]── EXPLICIT NON-GOALS ({len(non_goals)} items) ──[/bold red]")
        t = Table(show_header=True, header_style="bold red")
        t.add_column("NG-UID", width=20)
        t.add_column("Title", width=24)
        t.add_column("Description", width=35)
        t.add_column("Reason", width=38)
        for ng in non_goals:
            t.add_row(
                ng.get("uid",""),
                ng.get("title",""),
                ng.get("description","")[:60],
                ng.get("reason","")[:60]
            )
        console.print(t)

    # new requirements surfaced
    new_reqs = result.get("new_requirements_surfaced", [])
    if new_reqs:
        console.print(f"\n[bold cyan]── NEW REQUIREMENTS SURFACED ({len(new_reqs)}) ──[/bold cyan]")
        for r in new_reqs:
            console.print(f"  [cyan]{r.get('uid')}[/cyan] — {r.get('title')}: {r.get('description')}")

    # scope summary
    if result.get("scope_summary"):
        console.print(Panel(
            result["scope_summary"],
            title="[bold]Scope Summary[/bold]",
            border_style="purple"
        ))

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_scope_definition(stage1a_output, hitl1_output)
    display_results(result)

    with open("stage2_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full output saved to stage2_output.json")
