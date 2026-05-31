from openai import OpenAI
import json

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your-groq-key-here",
    timeout=600.0
)

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are the HITL 1 (Human-In-The-Loop) Checkpoint manager for Agent 1.

YOUR JOB:
You receive ambiguity findings from Stage 1B.
You generate clear, prioritised questions for the human reviewer.
You process their answers and update the requirement record.
You track rounds and fire stated assumptions when rounds are exhausted.

STRICT RULES:

1. NEVER ask more than 5 questions per round
   Pick the highest priority unresolved items first (P1 before P2 before P3)

2. NEVER ask compound questions
   BAD: "What platform and what login method?"
   GOOD: Two separate questions

3. NEVER suggest answers inside the question
   BAD: "Should this be iOS — since most habit apps are iOS first?"
   GOOD: "Which platform should this target: iOS, Android, Web, or cross-platform?"

4. AFTER receiving human answers:
   - Mark resolved items as RESOLVED with the human's answer
   - Mark unresolved or vague answers as STILL_VAGUE
   - If an answer is STILL_VAGUE after round 3, fire a STATED_ASSUMPTION

5. STATED ASSUMPTIONS must be:
   - Conservative — assume the smaller, simpler interpretation
   - Explicit — clearly state what is being assumed
   - Flagged — marked visibly for downstream reviewers

6. Track round number carefully — never exceed MAX_ROUNDS = 3

OUTPUT FORMAT for question generation:
{
  "round": <current round number>,
  "max_rounds": 3,
  "questions": [
    {
      "question_id": "Q1",
      "ambiguity_ref": "M1/C1/V1 etc",
      "priority": "P1/P2/P3",
      "question": "the exact question to ask the human"
    }
  ],
  "resolved_so_far": [],
  "still_open": ["list of ambiguity ids not yet asked"]
}

OUTPUT FORMAT after processing human answers:
{
  "round": <round number just completed>,
  "resolutions": [
    {
      "ambiguity_ref": "M1",
      "status": "RESOLVED",
      "human_answer": "what the human said",
      "resolution_note": "how this resolves the ambiguity"
    }
  ],
  "assumptions_fired": [
    {
      "ambiguity_ref": "V3",
      "assumption": "stated assumption text",
      "reason": "rounds exhausted / answer too vague"
    }
  ],
  "still_open": ["ambiguity ids still needing resolution"],
  "clarification_complete": true/false
}"""

# ── Load previous stage outputs ───────────────────────────────
# In real pipeline these come from files written by 1A and 1B
stage1a_output = {
    "session_id": "SES-20231012-001",
    "requirements": [
        {"uid": "REQ-20231012-001", "title": "Habit Tracking"},
        {"uid": "REQ-20231012-002", "title": "Friend Sharing"},
        {"uid": "REQ-20231012-003", "title": "Reminders"},
        {"uid": "REQ-20231012-004", "title": "Offline Functionality"},
        {"uid": "REQ-20231012-005", "title": "AI Suggestions"},
        {"uid": "REQ-20231012-006", "title": "Apple Health Integration"},
        {"uid": "REQ-20231012-007", "title": "Monetization"},
    ]
}

stage1b_output = {
    "session_id": "SES-20231012-001",
    "ambiguity_count": 8,
    "missing_requirements": [
        {"id": "M1", "description": "Platform not specified", "priority": "P1",
         "clarification_question": "Should the app be developed for iOS, Android, Web, or cross-platform?"},
        {"id": "M2", "description": "Data ownership not defined", "priority": "P1",
         "clarification_question": "Who owns the data collected through habit tracking?"},
        {"id": "M3", "description": "User identity model undefined", "priority": "P2",
         "clarification_question": "Should users log in with social media, email, or another method?"},
        {"id": "M4", "description": "Monetization model unclear", "priority": "P1",
         "clarification_question": "Should the app be completely free or use freemium/ads/subscriptions?"},
    ],
    "conflicts": [
        {"id": "C1", "description": "Free vs monetization conflict", "priority": "P1",
         "clarification_question": "Should the app be free with optional premium features, or include ads/subscriptions?"},
    ],
    "vague_statements": [
        {"id": "V1", "description": "AI suggestions scope undefined", "priority": "P2",
         "clarification_question": "Should AI suggestions be based on habit patterns, calendar data, or health metrics?"},
        {"id": "V2", "description": "Offline functionality scope ambiguous", "priority": "P2",
         "clarification_question": "Should offline functionality cover all features or only core habit tracking?"},
        {"id": "V3", "description": "Apple Health integration scope vague", "priority": "P3",
         "clarification_question": "Should integration include data sync, goal alignment, or third-party API access?"},
        {"id": "V4", "description": "Monetization method too vague", "priority": "P3",
         "clarification_question": "Should monetization use ads, subscriptions, in-app purchases, or data monetization?"},
    ]
}

# ── Generate questions for a round ───────────────────────────
def generate_questions(round_num: int, open_items: list, resolved_ids: list) -> dict:
    context = f"""
Current round: {round_num} of 3
Already resolved: {resolved_ids if resolved_ids else 'none'}

Open ambiguities still needing resolution:
{json.dumps(open_items, indent=2)}

Generate the questions for this round.
Pick P1 items first. Maximum 5 questions.
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
        print(f"❌ JSON parse failed: {e}\nRaw: {raw}")
        return {}

# ── Process human answers ─────────────────────────────────────
def process_answers(round_num: int, questions: list, answers: dict,
                    remaining_open: list, is_final_round: bool) -> dict:
    context = f"""
Round {round_num} just completed.
Is this the final round (round 3)? {is_final_round}

Questions that were asked:
{json.dumps(questions, indent=2)}

Human answers received:
{json.dumps(answers, indent=2)}

Remaining open ambiguities (not asked this round):
{json.dumps(remaining_open, indent=2)}

Process the answers. Mark resolved items. 
If this is the final round, fire STATED_ASSUMPTION for anything still open or vague.
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
        print(f"❌ JSON parse failed: {e}\nRaw: {raw}")
        return {}

# ── Display helpers ───────────────────────────────────────────
def display_questions(questions_output: dict):
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    round_num = questions_output.get("round", 1)
    questions = questions_output.get("questions", [])

    console.print(f"\n[bold purple]── HITL 1 ROUND {round_num} of 3 ──[/bold purple]")
    console.print(f"[dim]{len(questions)} questions to answer[/dim]\n")

    for q in questions:
        p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(q.get("priority"),"white")
        console.print(Panel(
            f"[bold]{q.get('question')}[/bold]",
            title=f"[{p_color}]{q.get('question_id')} ({q.get('priority')}) — ref: {q.get('ambiguity_ref')}[/{p_color}]",
            border_style=p_color
        ))

def display_resolutions(resolution_output: dict):
    from rich.console import Console
    from rich.table import Table
    console = Console()

    resolutions = resolution_output.get("resolutions", [])
    assumptions = resolution_output.get("assumptions_fired", [])

    if resolutions:
        console.print("\n[bold green]── RESOLUTIONS ──[/bold green]")
        t = Table(show_header=True, header_style="bold green")
        t.add_column("Ref", width=6)
        t.add_column("Status", width=14)
        t.add_column("Answer", width=40)
        t.add_column("Note", width=35)
        for r in resolutions:
            status = r.get("status","")
            s_color = "green" if status == "RESOLVED" else "yellow"
            t.add_row(
                r.get("ambiguity_ref",""),
                f"[{s_color}]{status}[/{s_color}]",
                r.get("human_answer",""),
                r.get("resolution_note","")
            )
        console.print(t)

    if assumptions:
        console.print("\n[bold red]── STATED ASSUMPTIONS FIRED ──[/bold red]")
        t = Table(show_header=True, header_style="bold red")
        t.add_column("Ref", width=6)
        t.add_column("Assumption", width=50)
        t.add_column("Reason", width=30)
        for a in assumptions:
            t.add_row(
                a.get("ambiguity_ref",""),
                a.get("assumption",""),
                a.get("reason","")
            )
        console.print(t)

    complete = resolution_output.get("clarification_complete", False)
    if complete:
        console.print("\n[bold green]✅ Clarification complete — ready for Stage 2[/bold green]")
    else:
        still_open = resolution_output.get("still_open", [])
        console.print(f"\n[yellow]⚠ Still open: {still_open}[/yellow]")

# ── Main loop ─────────────────────────────────────────────────
def run_hitl1():
    from rich.console import Console
    console = Console()

    console.print("\n[bold purple]═══ HITL 1 — INTENT CHECKPOINT ═══[/bold purple]")
    console.print("[dim]Maximum 3 rounds. Unanswered items become stated assumptions.[/dim]\n")

    # build flat list of all open items
    all_items = (
        stage1b_output["missing_requirements"] +
        stage1b_output["conflicts"] +
        stage1b_output["vague_statements"]
    )

    resolved_ids = []
    open_items = all_items.copy()
    all_resolutions = []
    all_assumptions = []
    session_log = []

    for round_num in range(1, 4):
        if not open_items:
            console.print("[green]All ambiguities resolved — exiting early.[/green]")
            break

        # generate questions
        console.print(f"\n⏳ Generating round {round_num} questions...")
        q_output = generate_questions(round_num, open_items, resolved_ids)
        if not q_output:
            break

        display_questions(q_output)

        # collect human answers
        questions = q_output.get("questions", [])
        answers = {}
        console.print("\n[bold cyan]YOUR ANSWERS:[/bold cyan]")
        console.print("[dim]Type your answer and press Enter for each question.[/dim]\n")

        for q in questions:
            answer = input(f"  {q.get('question_id')} — {q.get('question')}\n  > ").strip()
            answers[q.get("question_id")] = {
                "ambiguity_ref": q.get("ambiguity_ref"),
                "answer": answer
            }

        # figure out which items weren't asked this round
        asked_refs = [q.get("ambiguity_ref") for q in questions]
        remaining = [item for item in open_items if item["id"] not in asked_refs]

        is_final = (round_num == 3)

        # process answers
        console.print(f"\n⏳ Processing round {round_num} answers...")
        r_output = process_answers(round_num, questions, answers, remaining, is_final)
        if not r_output:
            break

        display_resolutions(r_output)
        session_log.append({"round": round_num, "questions": q_output, "resolutions": r_output})

        # update tracking
        for res in r_output.get("resolutions", []):
            if res.get("status") == "RESOLVED":
                resolved_ids.append(res.get("ambiguity_ref"))
                all_resolutions.append(res)

        for assumption in r_output.get("assumptions_fired", []):
            all_assumptions.append(assumption)
            resolved_ids.append(assumption.get("ambiguity_ref"))

        # remove resolved from open
        open_items = [item for item in open_items if item["id"] not in resolved_ids]

        if r_output.get("clarification_complete") or not open_items:
            break

    # final summary
    console.print("\n[bold purple]═══ HITL 1 COMPLETE ═══[/bold purple]")
    console.print(f"[green]Resolved: {len(all_resolutions)}[/green]")
    console.print(f"[red]Stated assumptions: {len(all_assumptions)}[/red]")
    console.print(f"[yellow]Still open: {len(open_items)}[/yellow]")

    # save output
    final_output = {
        "session_id": stage1b_output["session_id"],
        "rounds_used": min(round_num, 3),
        "resolutions": all_resolutions,
        "assumptions_fired": all_assumptions,
        "session_log": session_log
    }

    with open("hitl1_output.json", "w") as f:
        json.dump(final_output, f, indent=2)
    console.print("\n✅ Full output saved to hitl1_output.json")

# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    run_hitl1()
