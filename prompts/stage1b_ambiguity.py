from openai import OpenAI
import json

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your-groq-key-here"
)

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Ambiguity Detector for Agent 1, a requirement scoping pipeline.

You receive raw user input. You run in PARALLEL with the Requirement Extractor.
Your job is completely different — you are NOT extracting requirements.

YOUR SOLE JOB:
Find every ambiguity, conflict, and gap in the raw user input that would prevent
a clear, unambiguous scope from being defined.

YOU MUST DETECT THREE CLASSES OF PROBLEM:

CLASS 1 — MISSING REQUIREMENTS
Things that are implied or necessary but not stated.
Ask: "What decisions would a builder have to make that the user hasn't answered?"
Examples:
- Platform not stated (iOS? Android? Web?)
- User identity model not stated (how do users log in?)
- Data ownership not stated (who owns the data?)

CLASS 2 — CONFLICTS
Requirements or statements that directly contradict each other.
Ask: "Can both of these be true at the same time?"
Examples:
- "free" AND "make money" without a model defined
- "private" AND "share with friends" without access rules defined
- "simple" AND a long list of complex features

CLASS 3 — VAGUE STATEMENTS
Statements that cannot be validated, tested, or built without further definition.
Ask: "Could two different developers build two completely different things from this?"
Examples:
- "AI that gives suggestions" — what kind? triggered how? based on what data?
- "works offline" — all features? core features only? what syncs when online?
- "make money somehow" — ads? subscription? data? freemium?

STRICT RULES:

1. NEVER suggest solutions — only identify problems
   BAD: "User should clarify platform — suggest iOS first"
   GOOD: "Platform not specified — iOS, Android, Web, or cross-platform all possible"

2. NEVER invent conflicts that aren't there
   Only flag real contradictions in the input

3. EVERY item must have a specific clarification question
   The question must be specific enough that a yes/no or single-choice answer resolves it

4. PRIORITISE your findings
   P1 = blocks all scoping until resolved
   P2 = blocks specific features until resolved
   P3 = can proceed with stated assumption if unresolved after 3 rounds

OUTPUT FORMAT:
Respond ONLY with valid JSON — no preamble, no explanation:
{
  "session_id": "<match the session id from context>",
  "ambiguity_count": <total number of items>,
  "missing_requirements": [
    {
      "id": "M1",
      "description": "what is missing",
      "affected_requirements": ["REQ-uid-here"],
      "clarification_question": "specific yes/no or choice question",
      "priority": "P1/P2/P3"
    }
  ],
  "conflicts": [
    {
      "id": "C1",
      "description": "what conflicts with what",
      "affected_requirements": ["REQ-uid-1", "REQ-uid-2"],
      "clarification_question": "specific question to resolve the conflict",
      "priority": "P1/P2/P3"
    }
  ],
  "vague_statements": [
    {
      "id": "V1",
      "description": "what is vague and why",
      "affected_requirements": ["REQ-uid-here"],
      "clarification_question": "specific question to resolve the vagueness",
      "priority": "P1/P2/P3"
    }
  ],
  "ambiguity_summary": "one paragraph summary of the overall ambiguity level and biggest blockers"
}"""

# ── Test input — same as Stage 1A ─────────────────────────────
test_input = """I want to build an app where users can track their habits 
and maybe also share them with friends and get reminders and it should 
work offline and maybe have some AI that gives suggestions and it could 
also integrate with Apple Health and I want it to be free but also 
make money somehow"""

# ── Stage 1A output — passed in as context ────────────────────
# In the real pipeline this comes from Stage 1A's output
stage1a_requirements = [
    {"uid": "REQ-20231012-001", "title": "Habit Tracking"},
    {"uid": "REQ-20231012-002", "title": "Friend Sharing"},
    {"uid": "REQ-20231012-003", "title": "Reminders"},
    {"uid": "REQ-20231012-004", "title": "Offline Functionality"},
    {"uid": "REQ-20231012-005", "title": "AI Suggestions"},
    {"uid": "REQ-20231012-006", "title": "Apple Health Integration"},
    {"uid": "REQ-20231012-007", "title": "Monetization"},
]

# ── Run detection ─────────────────────────────────────────────
def run_ambiguity_detection(user_input: str, requirements: list) -> dict:
    print("\n⏳ Running Stage 1B — Ambiguity Detection...\n")

    # build context from 1A output
    req_context = "\n".join([f"- {r['uid']}: {r['title']}" for r in requirements])

    user_message = f"""Raw user input:
\"\"\"{user_input}\"\"\"

Requirements already extracted by Stage 1A (for reference):
{req_context}

Detect all ambiguities, conflicts, and missing requirements."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1
    )

    raw_output = response.choices[0].message.content

    # strip markdown fences if present
    if "```json" in raw_output:
        raw_output = raw_output.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_output:
        raw_output = raw_output.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(raw_output)
        return result
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")
        print(f"Raw output:\n{raw_output}")
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
    console.print(f"[bold purple]TOTAL AMBIGUITIES:[/bold purple] {result.get('ambiguity_count')}\n")

    # missing requirements
    missing = result.get("missing_requirements", [])
    if missing:
        console.print("[bold red]── MISSING REQUIREMENTS ──[/bold red]")
        t = Table(show_header=True, header_style="bold red")
        t.add_column("ID", width=6)
        t.add_column("Description", width=35)
        t.add_column("Clarification Question", width=45)
        t.add_column("Priority", width=8)
        for m in missing:
            p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(m.get("priority"),"white")
            t.add_row(
                m.get("id",""),
                m.get("description",""),
                m.get("clarification_question",""),
                f"[{p_color}]{m.get('priority','')}[/{p_color}]"
            )
        console.print(t)

    # conflicts
    conflicts = result.get("conflicts", [])
    if conflicts:
        console.print("\n[bold orange3]── CONFLICTS ──[/bold orange3]")
        t = Table(show_header=True, header_style="bold orange3")
        t.add_column("ID", width=6)
        t.add_column("Description", width=35)
        t.add_column("Clarification Question", width=45)
        t.add_column("Priority", width=8)
        for c in conflicts:
            p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(c.get("priority"),"white")
            t.add_row(
                c.get("id",""),
                c.get("description",""),
                c.get("clarification_question",""),
                f"[{p_color}]{c.get('priority','')}[/{p_color}]"
            )
        console.print(t)

    # vague statements
    vague = result.get("vague_statements", [])
    if vague:
        console.print("\n[bold yellow]── VAGUE STATEMENTS ──[/bold yellow]")
        t = Table(show_header=True, header_style="bold yellow")
        t.add_column("ID", width=6)
        t.add_column("Description", width=35)
        t.add_column("Clarification Question", width=45)
        t.add_column("Priority", width=8)
        for v in vague:
            p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(v.get("priority"),"white")
            t.add_row(
                v.get("id",""),
                v.get("description",""),
                v.get("clarification_question",""),
                f"[{p_color}]{v.get('priority','')}[/{p_color}]"
            )
        console.print(t)

    # summary
    if result.get("ambiguity_summary"):
        console.print(Panel(
            result["ambiguity_summary"],
            title="[bold]Ambiguity Summary[/bold]",
            border_style="cyan"
        ))

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_ambiguity_detection(test_input, stage1a_requirements)
    display_results(result)

    with open("stage1b_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full output saved to stage1b_output.json")
