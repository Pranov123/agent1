import json
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.session_manager import SessionManager
from core.state_machine import StateMachine
from core import get_client, get_primary_model, get_validation_model
import config

console = Console()

class Displayer:
    """Handles all rich table display after each stage."""

    def __init__(self, console: Console):
        self.console = console

    def stage1a(self, result: dict):
        reqs = result.get("requirements", [])
        if not reqs:
            return
        self.console.print(f"\n[bold green]── EXTRACTED REQUIREMENTS ({len(reqs)}) ──[/bold green]")
        t = Table(show_header=True, header_style="bold green")
        t.add_column("UID",         width=20)
        t.add_column("Title",       width=22)
        t.add_column("Category",    width=16)
        t.add_column("Priority",    width=10)
        t.add_column("Confidence",  width=10)
        t.add_column("Description", width=40)
        for r in reqs:
            p_color = {
                "Critical":"red","High":"orange3",
                "Medium":"yellow","Low":"green"
            }.get(r.get("priority",""), "white")
            c_color = {
                "HIGH":"green","MEDIUM":"yellow","LOW":"red"
            }.get(r.get("confidence",""), "white")
            t.add_row(
                r.get("uid","—"),
                r.get("title",""),
                r.get("category",""),
                f"[{p_color}]{r.get('priority','')}[/{p_color}]",
                f"[{c_color}]{r.get('confidence','')}[/{c_color}]",
                r.get("description","")[:70]
            )
        self.console.print(t)
        if result.get("extraction_notes"):
            self.console.print(f"[dim]Notes: {result['extraction_notes']}[/dim]")

    def stage1b(self, result: dict):
        missing   = result.get("missing_requirements", [])
        conflicts = result.get("conflicts", [])
        vague     = result.get("vague_statements", [])

        if missing:
            self.console.print(f"\n[bold red]── MISSING REQUIREMENTS ({len(missing)}) ──[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("ID",       width=6)
            t.add_column("Priority", width=8)
            t.add_column("Description",          width=38)
            t.add_column("Clarification Question", width=44)
            for m in missing:
                p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(m.get("priority",""),"white")
                t.add_row(
                    m.get("id",""),
                    f"[{p_color}]{m.get('priority','')}[/{p_color}]",
                    m.get("description","")[:70],
                    m.get("clarification_question","")[:80]
                )
            self.console.print(t)

        if conflicts:
            self.console.print(f"\n[bold orange3]── CONFLICTS ({len(conflicts)}) ──[/bold orange3]")
            t = Table(show_header=True, header_style="bold orange3")
            t.add_column("ID",       width=6)
            t.add_column("Priority", width=8)
            t.add_column("Description",          width=38)
            t.add_column("Clarification Question", width=44)
            for c in conflicts:
                p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(c.get("priority",""),"white")
                t.add_row(
                    c.get("id",""),
                    f"[{p_color}]{c.get('priority','')}[/{p_color}]",
                    c.get("description","")[:70],
                    c.get("clarification_question","")[:80]
                )
            self.console.print(t)

        if vague:
            self.console.print(f"\n[bold yellow]── VAGUE STATEMENTS ({len(vague)}) ──[/bold yellow]")
            t = Table(show_header=True, header_style="bold yellow")
            t.add_column("ID",       width=6)
            t.add_column("Priority", width=8)
            t.add_column("Description",          width=38)
            t.add_column("Clarification Question", width=44)
            for v in vague:
                p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(v.get("priority",""),"white")
                t.add_row(
                    v.get("id",""),
                    f"[{p_color}]{v.get('priority','')}[/{p_color}]",
                    v.get("description","")[:70],
                    v.get("clarification_question","")[:80]
                )
            self.console.print(t)

        if result.get("ambiguity_summary"):
            self.console.print(Panel(
                result["ambiguity_summary"],
                title="[bold]Ambiguity Summary[/bold]",
                border_style="cyan"
            ))

    def hitl1_resolutions(self, resolutions: list, assumptions: list):
        if resolutions:
            self.console.print(f"\n[bold green]── RESOLUTIONS ({len(resolutions)}) ──[/bold green]")
            t = Table(show_header=True, header_style="bold green")
            t.add_column("Ref",    width=6)
            t.add_column("Status", width=14)
            t.add_column("Answer", width=38)
            t.add_column("Note",   width=34)
            for r in resolutions:
                s = r.get("status","")
                s_color = "green" if s == "RESOLVED" else "yellow"
                t.add_row(
                    r.get("ambiguity_ref",""),
                    f"[{s_color}]{s}[/{s_color}]",
                    r.get("human_answer","")[:70],
                    r.get("resolution_note","")[:60]
                )
            self.console.print(t)

        if assumptions:
            self.console.print(f"\n[bold red]── STATED ASSUMPTIONS ({len(assumptions)}) ──[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("Ref",        width=6)
            t.add_column("Assumption", width=50)
            t.add_column("Reason",     width=30)
            for a in assumptions:
                t.add_row(
                    a.get("ambiguity_ref",""),
                    a.get("assumption","")[:90],
                    a.get("reason","")[:55]
                )
            self.console.print(t)

    def stage2(self, result: dict):
        bucket_config = [
            ("mvp_scope",       "MVP SCOPE",        "bold green",  "green"),
            ("nice_to_have",    "NICE TO HAVE",     "bold yellow", "yellow"),
            ("future_features", "FUTURE FEATURES",  "bold cyan",   "cyan"),
        ]
        for key, label, header_style, _ in bucket_config:
            items = result.get(key, [])
            if not items:
                continue
            self.console.print(f"\n[{header_style}]── {label} ({len(items)} items) ──[/{header_style}]")
            t = Table(show_header=True, header_style=header_style)
            t.add_column("UID",         width=20)
            t.add_column("Title",       width=22)
            t.add_column("Priority",    width=10)
            t.add_column("Description", width=42)
            t.add_column("Reason",      width=28)
            for item in items:
                p_color = {
                    "Critical":"red","High":"orange3",
                    "Medium":"yellow","Low":"green"
                }.get(item.get("priority",""), "white")
                t.add_row(
                    item.get("uid",""),
                    item.get("title",""),
                    f"[{p_color}]{item.get('priority','')}[/{p_color}]",
                    item.get("description","")[:75],
                    item.get("placement_reason","")[:50]
                )
            self.console.print(t)

        non_goals = result.get("non_goals", [])
        if non_goals:
            self.console.print(f"\n[bold red]── EXPLICIT NON-GOALS ({len(non_goals)}) ──[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("NG-UID",      width=20)
            t.add_column("Title",       width=22)
            t.add_column("Description", width=38)
            t.add_column("Reason",      width=36)
            for ng in non_goals:
                t.add_row(
                    ng.get("uid",""),
                    ng.get("title",""),
                    ng.get("description","")[:65],
                    ng.get("reason","")[:60]
                )
            self.console.print(t)

        new_reqs = result.get("new_requirements_surfaced", [])
        if new_reqs:
            self.console.print(f"\n[bold cyan]── NEW REQUIREMENTS SURFACED ({len(new_reqs)}) ──[/bold cyan]")
            for r in new_reqs:
                self.console.print(
                    f"  [cyan]{r.get('uid','')}[/cyan] — "
                    f"{r.get('title','')}: {r.get('description','')[:80]}"
                )

        if result.get("scope_summary"):
            self.console.print(Panel(
                result["scope_summary"],
                title="[bold]Scope Summary[/bold]",
                border_style="purple"
            ))

    def stage3(self, result: dict):
        from rich.table import Table

        contradictions = result.get("contradictions", [])
        if contradictions:
            self.console.print(f"\n[bold red]── CONTRADICTIONS ({len(contradictions)}) ──[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("ID",             width=8)
            t.add_column("Severity",       width=10)
            t.add_column("Description",    width=42)
            t.add_column("UIDs",           width=24)
            t.add_column("Recommendation", width=28)
            for c in contradictions:
                s_color = {"HIGH":"red","MEDIUM":"orange3","LOW":"yellow"}.get(c.get("severity",""),"white")
                t.add_row(
                    c.get("id",""),
                    f"[{s_color}]{c.get('severity','')}[/{s_color}]",
                    c.get("description","")[:75],
                    ", ".join(c.get("req_uids",[])),
                    c.get("recommendation","")[:50]
                )
            self.console.print(t)

        missing = result.get("missing_requirements", [])
        if missing:
            self.console.print(f"\n[bold orange3]── MISSING REQUIREMENTS ({len(missing)}) ──[/bold orange3]")
            t = Table(show_header=True, header_style="bold orange3")
            t.add_column("ID",             width=8)
            t.add_column("Severity",       width=10)
            t.add_column("Description",    width=48)
            t.add_column("Recommendation", width=32)
            for m in missing:
                s_color = {"HIGH":"red","MEDIUM":"orange3","LOW":"yellow"}.get(m.get("severity",""),"white")
                t.add_row(
                    m.get("id",""),
                    f"[{s_color}]{m.get('severity','')}[/{s_color}]",
                    m.get("description","")[:85],
                    m.get("recommendation","")[:55]
                )
            self.console.print(t)

        scope = result.get("scope_explosion", {})
        if scope:
            self.console.print(f"\n[bold cyan]── SCOPE EXPLOSION ANALYSIS ──[/bold cyan]")
            factors = scope.get("factor_scores", {})
            sss     = scope.get("weighted_sss", 0)
            tier    = scope.get("severity_tier", "")
            veto    = scope.get("hard_veto_triggered", False)
            tier_color = {"Minor":"green","Medium":"yellow","Major":"red"}.get(tier,"white")
            factor_weights = {
                "requirement_impact":       0.25,
                "architectural_expansion":  0.25,
                "cross_cutting_complexity": 0.20,
                "timeline_pressure":        0.15,
                "dependency_growth":        0.15,
            }
            t = Table(show_header=True, header_style="bold cyan")
            t.add_column("Factor",       width=32)
            t.add_column("Score",        width=8)
            t.add_column("Weight",       width=8)
            t.add_column("Contribution", width=14)
            for factor, weight in factor_weights.items():
                score        = factors.get(factor, 0)
                contribution = score * weight
                veto_flag    = " ⚠" if factor in [
                    "architectural_expansion","cross_cutting_complexity"
                ] and score >= 8 else ""
                t.add_row(
                    factor.replace("_"," ").title() + veto_flag,
                    str(score),
                    f"{int(weight*100)}%",
                    f"{contribution:.2f}"
                )
            self.console.print(t)
            self.console.print(f"\n[bold]Weighted SSS:[/bold] {sss}/100  "
                               f"[bold]Severity:[/bold] [{tier_color}]{tier}[/{tier_color}]")
            if veto:
                self.console.print(
                    f"[bold red]⚠ HARD VETO: {scope.get('hard_veto_reason','')}[/bold red]"
                )
            self.console.print(f"[dim]{scope.get('assessment','')}[/dim]")

        bias = result.get("bias_audit", [])
        if bias:
            self.console.print(f"\n[bold yellow]── BIAS AUDIT ({len(bias)}) ──[/bold yellow]")
            t = Table(show_header=True, header_style="bold yellow")
            t.add_column("ID",             width=10)
            t.add_column("Type",           width=26)
            t.add_column("Description",    width=40)
            t.add_column("Recommendation", width=28)
            for b in bias:
                t.add_row(
                    b.get("id",""),
                    b.get("type",""),
                    b.get("description","")[:72],
                    b.get("recommendation","")[:50]
                )
            self.console.print(t)

        ethics = result.get("product_ethics", [])
        if ethics:
            self.console.print(f"\n[bold magenta]── PRODUCT ETHICS ({len(ethics)}) ──[/bold magenta]")
            t = Table(show_header=True, header_style="bold magenta")
            t.add_column("ID",             width=10)
            t.add_column("Type",           width=26)
            t.add_column("Description",    width=40)
            t.add_column("Recommendation", width=28)
            for e in ethics:
                t.add_row(
                    e.get("id",""),
                    e.get("type",""),
                    e.get("description","")[:72],
                    e.get("recommendation","")[:50]
                )
            self.console.print(t)

        ngc = result.get("non_goal_conflicts", [])
        if ngc:
            self.console.print(f"\n[bold red]── NON-GOAL CONFLICTS ({len(ngc)}) ──[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("ID",             width=10)
            t.add_column("Req UID",        width=22)
            t.add_column("NG UID",         width=22)
            t.add_column("Description",    width=36)
            t.add_column("Recommendation", width=24)
            for n in ngc:
                t.add_row(
                    n.get("id",""),
                    n.get("requirement_uid",""),
                    n.get("non_goal_uid",""),
                    n.get("description","")[:60],
                    n.get("recommendation","")[:40]
                )
            self.console.print(t)

        divergence = result.get("intent_divergence", {})
        if divergence.get("divergence_detected"):
            self.console.print(Panel(
                divergence.get("description",""),
                title="[bold yellow]⚠ Intent Divergence Detected[/bold yellow]",
                border_style="yellow"
            ))

        if result.get("validation_summary"):
            self.console.print(Panel(
                result["validation_summary"],
                title="[bold]Validation Summary[/bold]",
                border_style="purple"
            ))

class Pipeline:
    def __init__(self):
        self.sm               = SessionManager()
        self.machine          = StateMachine(self.sm)
        self.client           = get_client()
        self.primary_model    = get_primary_model()
        self.validation_model = get_validation_model()
        self.display          = Displayer(console)

    def run(self, user_input: str) -> dict:
        self.sm.raw_input = user_input
        console.print(Rule(f"[bold purple]AGENT 1 — SESSION {self.sm.session_id}[/bold purple]"))
        console.print(f"[dim]Input received — {len(user_input)} characters[/dim]\n")

        stage1a      = self._run_stage1a(user_input)
        stage1b      = self._run_stage1b(user_input, stage1a)
        self._load_requirements_from_1a(stage1a)
        hitl1_result = self._run_hitl1(stage1b)
        stage2       = self._run_stage2(stage1a, hitl1_result)
        self._load_scope_from_stage2(stage2)
        stage3       = self._run_stage3(stage2, user_input, hitl1_result)
        self._apply_validation_flags(stage3)
        self._advance_to_validated(stage3)
        self._run_hitl2(stage3)

        path = self.sm.save()
        console.print(f"\n[bold green]✅ Session complete — saved to {path}[/bold green]")
        return self.sm.summary()

    # ── Stage 1A ──────────────────────────────────────────────
    def _run_stage1a(self, user_input: str) -> dict:
        console.print(Rule("[bold cyan]Stage 1A — Requirement Extraction[/bold cyan]"))

        SYSTEM_PROMPT = """You are the Requirement Extractor for Agent 1.

YOUR SOLE JOB:
Extract atomic, traceable requirements from raw user input.

STRICT RULES:
1. NEVER invent requirements not stated or strongly implied
2. NEVER include implementation details or technology choices
3. NEVER combine two requirements into one — keep atomic
4. NEVER hallucinate — if not stated or implied, it does not exist
5. If user used "maybe", "could", "might" — mark confidence: LOW
6. If clearly stated — mark confidence: HIGH
7. If implied but not stated — mark confidence: MEDIUM

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "session_id": "string",
  "requirements": [
    {
      "uid": "",
      "title": "short title",
      "description": "clear testable description",
      "category": "Functional/Non-functional/Constraint",
      "priority": "Critical/High/Medium/Low",
      "status": "EXTRACTED",
      "dependencies": [],
      "source_quote": "exact phrase from input",
      "confidence": "HIGH/MEDIUM/LOW"
    }
  ],
  "extraction_notes": "observations"
}"""

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Extract requirements from:\n\n{user_input}"}
            ],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        self.sm.store_stage_output("stage1a", result)
        count = len(result.get("requirements", []))
        console.print(f"[green]✓ Extracted {count} requirements[/green]")
        self.display.stage1a(result)
        return result

    # ── Stage 1B ──────────────────────────────────────────────
    def _run_stage1b(self, user_input: str, stage1a: dict) -> dict:
        console.print(Rule("[bold cyan]Stage 1B — Ambiguity Detection[/bold cyan]"))

        req_context = "\n".join([
            f"- {r.get('uid') or 'TBD'}: {r['title']}"
            for r in stage1a.get("requirements", [])
        ])

        SYSTEM_PROMPT = """You are the Ambiguity Detector for Agent 1.

YOUR SOLE JOB:
Find every ambiguity, conflict, and gap in the raw user input.
You are NOT extracting requirements — you are finding problems.

THREE CLASSES:
1. MISSING REQUIREMENTS — implied but not stated
2. CONFLICTS — statements that contradict each other
3. VAGUE STATEMENTS — cannot be built or tested without more info

STRICT RULES:
1. NEVER suggest solutions — only identify problems
2. NEVER invent conflicts that are not there
3. Every item must have a specific clarification question
4. Prioritise: P1=blocks all scoping, P2=blocks feature, P3=can assume

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "session_id": "string",
  "ambiguity_count": 0,
  "missing_requirements": [
    {"id":"M1","description":"","affected_requirements":[],"clarification_question":"","priority":"P1"}
  ],
  "conflicts": [
    {"id":"C1","description":"","affected_requirements":[],"clarification_question":"","priority":"P1"}
  ],
  "vague_statements": [
    {"id":"V1","description":"","affected_requirements":[],"clarification_question":"","priority":"P2"}
  ],
  "ambiguity_summary": "one paragraph"
}"""

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Raw input:\n\"\"\"{user_input}\"\"\"\n\n"
                    f"Requirements extracted by Stage 1A:\n{req_context}\n\n"
                    f"Detect all ambiguities."
                )}
            ],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        self.sm.store_stage_output("stage1b", result)
        count = result.get("ambiguity_count", 0)
        console.print(f"[yellow]⚠ Found {count} ambiguities[/yellow]")
        self.display.stage1b(result)
        return result

    # ── HITL 1 ────────────────────────────────────────────────
    def _run_hitl1(self, stage1b: dict) -> dict:
        console.print(Rule("[bold purple]HITL 1 — Intent Checkpoint[/bold purple]"))

        all_items = (
            stage1b.get("missing_requirements", []) +
            stage1b.get("conflicts", []) +
            stage1b.get("vague_statements", [])
        )

        if not all_items:
            console.print("[green]No ambiguities — skipping HITL 1[/green]")
            return {"resolutions": [], "assumptions_fired": []}

        resolved_ids     = []
        all_resolutions  = []
        all_assumptions  = []
        open_items       = all_items.copy()

        for round_num in range(1, config.MAX_CLARIFICATION_ROUNDS + 1):
            if not open_items:
                break

            console.print(f"\n[bold purple]── Round {round_num} of {config.MAX_CLARIFICATION_ROUNDS} ──[/bold purple]")

            questions = self._generate_hitl1_questions(round_num, open_items, resolved_ids)
            if not questions:
                break

            answers = {}
            console.print("\n[bold cyan]Please answer the following:[/bold cyan]")
            for q in questions:
                p_color = {"P1":"red","P2":"orange3","P3":"yellow"}.get(q.get("priority"), "white")
                console.print(Panel(
                    f"[bold]{q.get('question')}[/bold]",
                    title=f"[{p_color}]{q.get('question_id')} ({q.get('priority')})[/{p_color}]",
                    border_style=p_color
                ))
                answer = input(f"  Your answer: ").strip()
                answers[q.get("question_id")] = {
                    "ambiguity_ref": q.get("ambiguity_ref"),
                    "answer": answer
                }

            is_final   = (round_num == config.MAX_CLARIFICATION_ROUNDS)
            asked_refs = [q.get("ambiguity_ref") for q in questions]
            remaining  = [i for i in open_items if i["id"] not in asked_refs]

            resolutions = self._process_hitl1_answers(
                round_num, questions, answers, remaining, is_final
            )

            self.sm.log_hitl1_round(
                round_num, questions, answers,
                resolutions.get("resolutions", [])
            )

            for res in resolutions.get("resolutions", []):
                if res.get("status") == "RESOLVED":
                    resolved_ids.append(res.get("ambiguity_ref"))
                    all_resolutions.append(res)

            for assumption in resolutions.get("assumptions_fired", []):
                all_assumptions.append(assumption)
                resolved_ids.append(assumption.get("ambiguity_ref"))

            open_items = [i for i in open_items if i["id"] not in resolved_ids]

            if resolutions.get("clarification_complete") or not open_items:
                break

        console.print(
            f"\n[green]✓ HITL 1 complete — {len(all_resolutions)} resolved, "
            f"{len(all_assumptions)} assumptions[/green]"
        )
        self.display.hitl1_resolutions(all_resolutions, all_assumptions)
        return {"resolutions": all_resolutions, "assumptions_fired": all_assumptions}

    def _generate_hitl1_questions(self, round_num, open_items, resolved_ids):
        SYSTEM_PROMPT = """You are the HITL 1 Question Generator for Agent 1.

Generate clear prioritised questions for the human reviewer.
Pick P1 items first. Maximum 5 questions per round.
Never ask compound questions. Never suggest answers.

OUTPUT FORMAT — valid JSON only:
{
  "round": 1,
  "questions": [
    {
      "question_id": "Q1",
      "ambiguity_ref": "M1",
      "priority": "P1",
      "question": "exact question to ask"
    }
  ]
}"""

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Round {round_num} of 3.\n"
                    f"Already resolved: {resolved_ids or 'none'}\n"
                    f"Open items:\n{json.dumps(open_items, indent=2)}\n"
                    f"Generate questions for this round."
                )}
            ],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        return result.get("questions", [])

    def _process_hitl1_answers(self, round_num, questions, answers, remaining, is_final):
        SYSTEM_PROMPT = """You are the HITL 1 Answer Processor for Agent 1.

Process human answers. Mark resolved items RESOLVED.
Mark vague answers STILL_VAGUE.
If this is the final round, fire STATED_ASSUMPTION for anything still open.
Stated assumptions must be conservative — assume the smaller interpretation.

OUTPUT FORMAT — valid JSON only:
{
  "round": 1,
  "resolutions": [
    {
      "ambiguity_ref": "M1",
      "status": "RESOLVED/STILL_VAGUE",
      "human_answer": "what they said",
      "resolution_note": "how this resolves it"
    }
  ],
  "assumptions_fired": [
    {
      "ambiguity_ref": "V3",
      "assumption": "stated assumption text",
      "reason": "rounds exhausted / answer too vague"
    }
  ],
  "still_open": [],
  "clarification_complete": true
}"""

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Round {round_num}. Final round: {is_final}\n"
                    f"Questions asked:\n{json.dumps(questions, indent=2)}\n"
                    f"Human answers:\n{json.dumps(answers, indent=2)}\n"
                    f"Remaining open items:\n{json.dumps(remaining, indent=2)}\n"
                    f"Process the answers."
                )}
            ],
            temperature=0.1
        )

        return self._parse_json(response.choices[0].message.content)

    # ── Stage 2 ───────────────────────────────────────────────
    def _run_stage2(self, stage1a: dict, hitl1: dict) -> dict:
        console.print(Rule("[bold cyan]Stage 2 — Scope Definition[/bold cyan]"))

        SYSTEM_PROMPT = """You are the Scope Definition engine for Agent 1.

Organise clarified requirements into four buckets:
1. MVP SCOPE — minimum viable product, critical features only
2. NICE TO HAVE — valuable but not launch-blocking
3. FUTURE FEATURES — explicitly deferred
4. EXPLICIT NON-GOALS — deliberately excluded, with NG-UIDs

RULES:
1. Every requirement must appear in exactly one bucket
2. Use HITL 1 resolutions to make placement decisions
3. Non-goals must only come from actual HITL 1 decisions — never invent them
4. New requirements surfaced during clarification get new UIDs
5. Each requirement keeps its original UID from Stage 1A

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "session_id": "string",
  "mvp_scope": [
    {
      "uid":"","title":"","description":"","category":"",
      "priority":"","status":"CLARIFIED","dependencies":[],
      "scope_bucket":"MVP","placement_reason":""
    }
  ],
  "nice_to_have": [],
  "future_features": [],
  "non_goals": [
    {
      "uid":"NG-YYYYMMDD-001","title":"","description":"",
      "reason":"","status":"ACTIVE","source":""
    }
  ],
  "new_requirements_surfaced": [],
  "scope_summary": "one paragraph"
}"""

        resolutions_text  = json.dumps(hitl1.get("resolutions", []), indent=2)
        requirements_text = json.dumps(stage1a.get("requirements", []), indent=2)

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                        f"Requirements from Stage 1A:\n{requirements_text}\n\n"
                        f"HITL 1 resolutions:\n{resolutions_text}\n\n"
                        f"Define the full scope using these EXACT placement rules:\n\n"
                        f"MVP RULES:\n"
                        f"- Core functionality without which the app cannot launch\n"
                        f"- Free access constraint belongs in MVP\n"
                        f"- Monetization/revenue model belongs in MVP — the app cannot sustain without it\n"
                        f"- Offline functionality if clearly stated belongs in MVP\n"
                        f"- Authentication if required belongs in MVP\n\n"
                        f"NICE TO HAVE RULES:\n"
                        f"- Social features that enhance but don't define the product\n"
                        f"- Features the user hedged with 'maybe' that are NOT behind a paywall\n\n"
                        f"FUTURE FEATURES RULES:\n"
                        f"- Features explicitly placed behind a paywall in HITL 1\n"
                        f"- AI features if HITL 1 said they are paid\n"
                        f"- Health integrations if HITL 1 said they are paid\n\n"
                        f"NON-GOALS RULES:\n"
                        f"- MUST generate non-goals from HITL 1 platform decisions\n"
                        f"- MUST generate non-goals from HITL 1 data storage decisions\n"
                        f"- Example: if HITL 1 said iOS only — non-goal is No Android app\n"
                        f"- Example: if HITL 1 said no server storage — non-goal is No server-side data storage\n"
                        f"- Example: if HITL 1 said read-only health data — non-goal is No writing to Apple Health\n"
                        f"- Do NOT invent non-goals that were never discussed\n\n"
                        f"CRITICAL: Read the HITL 1 resolutions carefully for paywall decisions. "
                        f"Anything explicitly stated as paid/premium/behind paywall goes to FUTURE, not NICE TO HAVE.\n\n"
                        f"Make sure ALL requirements appear in exactly one bucket."
                )}
            ],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content)
        self.sm.store_stage_output("stage2", result)

        mvp_count    = len(result.get("mvp_scope", []))
        nth_count    = len(result.get("nice_to_have", []))
        future_count = len(result.get("future_features", []))
        ng_count     = len(result.get("non_goals", []))
        console.print(
            f"[green]✓ Scope defined — {mvp_count} MVP, {nth_count} nice-to-have, "
            f"{future_count} future, {ng_count} non-goals[/green]"
        )
        self.display.stage2(result)
        return result

    # ── Stage 3 ───────────────────────────────────────────────
    def _run_stage3(self, stage2: dict, original_input: str, hitl1: dict) -> dict:
        console.print(Rule("[bold cyan]Stage 3 — DeepSeek R1 Validation[/bold cyan]"))

        SYSTEM_PROMPT = """You are the Validation Layer for Agent 1.
You are adversarial. Your job is to find problems.

CHECK SEVEN THINGS:
1. CONTRADICTIONS — requirements that cannot both be true
2. MISSING REQUIREMENTS — logically necessary but absent
3. SCOPE EXPLOSION — score 5 factors 0-10, weighted SSS out of 100
   Weights: Req Impact 25%, Arch Expansion 25%, Cross-Cutting 20%, Timeline 15%, Dependency 15%
   Hard veto if Arch Expansion >= 8 OR Cross-Cutting >= 8
   weighted_sss must be a SINGLE NUMBER only — no formulas in the field
4. BIAS AUDIT — exclusion niches, accessibility, demographic assumptions
5. PRODUCT ETHICS — dark patterns, consent theatre, exploitative pricing
6. NON-GOAL CONFLICTS — requirements that violate active non-goals
7. INTENT DIVERGENCE — does scope match original user intent

RULES:
- You VALIDATE, never APPROVE
- Be adversarial — a clean report with no findings is a failure
- Every finding must reference specific UIDs
- weighted_sss = single number only

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "session_id": "string",
  "validation_status": "VALIDATED_WITH_FLAGS/VALIDATED_CLEAN/VALIDATION_FAILED",
  "contradictions": [{"id":"","severity":"HIGH/MEDIUM/LOW","description":"","req_uids":[],"recommendation":""}],
  "missing_requirements": [{"id":"","severity":"","description":"","affected_uids":[],"recommendation":""}],
  "scope_explosion": {
    "factor_scores": {
      "requirement_impact":0,"architectural_expansion":0,
      "cross_cutting_complexity":0,"timeline_pressure":0,"dependency_growth":0
    },
    "weighted_sss": 0,
    "severity_tier": "Minor/Medium/Major",
    "hard_veto_triggered": false,
    "hard_veto_reason": "",
    "assessment": "calculation shown as plain text"
  },
  "bias_audit": [{"id":"","type":"","description":"","affected_uids":[],"recommendation":""}],
  "product_ethics": [{"id":"","type":"","description":"","affected_uids":[],"recommendation":""}],
  "non_goal_conflicts": [{"id":"","requirement_uid":"","non_goal_uid":"","description":"","recommendation":""}],
  "intent_divergence": {"divergence_detected":false,"description":"","affected_uids":[]},
  "validation_summary": "paragraph",
  "requirements_advanced": []
}"""

        response = self.client.chat.completions.create(
            model=self.validation_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Original input:\n\"\"\"{original_input}\"\"\"\n\n"
                    f"HITL 1 resolutions:\n"
                    f"{json.dumps(hitl1.get('resolutions',[]), indent=2)}\n\n"
                    f"MVP:\n{json.dumps(stage2.get('mvp_scope',[]), indent=2)}\n\n"
                    f"Nice to have:\n{json.dumps(stage2.get('nice_to_have',[]), indent=2)}\n\n"
                    f"Future:\n{json.dumps(stage2.get('future_features',[]), indent=2)}\n\n"
                    f"Non-goals:\n{json.dumps(stage2.get('non_goals',[]), indent=2)}\n\n"
                    f"Run all seven checks. weighted_sss must be a single number only."
                )}
            ],
            temperature=0.1
        )

        result = self._parse_json(response.choices[0].message.content, fix_sss=True)
        self.sm.store_stage_output("stage3", result)

        status = result.get("validation_status", "UNKNOWN")
        color  = {
            "VALIDATED_CLEAN":      "green",
            "VALIDATED_WITH_FLAGS": "yellow",
            "VALIDATION_FAILED":    "red"
        }.get(status, "white")
        console.print(f"[{color}]✓ Validation: {status}[/{color}]")
        self.display.stage3(result)
        return result

    # ── HITL 2 ────────────────────────────────────────────────
    def _run_hitl2(self, stage3: dict):
        console.print(Rule("[bold purple]HITL 2 — Scope Approval[/bold purple]"))
        self._display_hitl2_brief(stage3)

        console.print("\n[bold cyan]REVIEWER ACTION[/bold cyan]")
        console.print("[dim]Options: approve / reject / modify[/dim]\n")

        reviewer_id = input("  Your reviewer ID: ").strip() or "reviewer_001"
        action      = input("  Action (approve/reject/modify): ").strip().lower()
        notes       = input("  Notes (optional): ").strip()

        if action == "approve":
            # advance all requirements in HUMAN_REVIEW to APPROVED then LOCKED
            approved_count = 0
            blocked_uids   = []

            for uid, req in self.sm.requirements.items():
                if req.get("status") == "HUMAN_REVIEW":
                    if self.sm.has_blocking_flags(uid):
                        blocked_uids.append(uid)
                        continue
                    self.sm.requirements[uid]["status"] = "APPROVED"
                    self.sm.requirements[uid]["approved_by"] = reviewer_id
                    self.sm.requirements[uid]["updated_at"]  = datetime.now().isoformat()
                    self.sm.requirements[uid]["status"] = "LOCKED"
                    approved_count += 1

            self.sm.log_hitl2_action(reviewer_id, "APPROVED", [], notes)
            console.print(f"\n[green]✓ Approved and locked: {approved_count} requirements[/green]")
            if blocked_uids:
                console.print(f"[red]⚠ Blocked by hard flags: {blocked_uids}[/red]")

        elif action == "reject":
            rejected = []
            for uid, req in self.sm.requirements.items():
                if req.get("status") == "HUMAN_REVIEW":
                    self.sm.requirements[uid]["status"] = "REJECTED"
                    rejected.append(uid)
            self.sm.log_hitl2_action(reviewer_id, "REJECTED", rejected, notes)
            console.print(f"[red]✗ Rejected {len(rejected)} requirements[/red]")

        else:
            console.print("[yellow]Modification requested — requirements remain in HUMAN_REVIEW[/yellow]")
            self.sm.log_hitl2_action(reviewer_id, "MODIFY_REQUESTED", [], notes)

    def _display_hitl2_brief(self, stage3: dict):
        console.print("\n[bold]── SCOPE FOR REVIEW ──[/bold]")

        # MVP table
        mvp = self.sm.get_by_bucket("MVP")
        if mvp:
            console.print(f"\n[bold green]MVP SCOPE ({len(mvp)} items)[/bold green]")
            t = Table(show_header=True, header_style="bold green")
            t.add_column("UID",         width=22)
            t.add_column("Title",       width=22)
            t.add_column("Priority",    width=10)
            t.add_column("Description", width=44)
            t.add_column("Reason",      width=28)
            for r in mvp:
                p_color = {
                    "Critical":"red","High":"orange3",
                    "Medium":"yellow","Low":"green"
                }.get(r.get("priority",""), "white")
                t.add_row(
                    r.get("uid",""),
                    r.get("title",""),
                    f"[{p_color}]{r.get('priority','')}[/{p_color}]",
                    r.get("description","")[:80],
                    r.get("placement_reason","")[:50]
                )
            console.print(t)

        # Nice to have table
        nth = self.sm.get_by_bucket("NICE_TO_HAVE")
        if nth:
            console.print(f"\n[bold yellow]NICE TO HAVE ({len(nth)} items)[/bold yellow]")
            t = Table(show_header=True, header_style="bold yellow")
            t.add_column("UID",         width=22)
            t.add_column("Title",       width=22)
            t.add_column("Priority",    width=10)
            t.add_column("Description", width=44)
            t.add_column("Reason",      width=28)
            for r in nth:
                t.add_row(
                    r.get("uid",""),
                    r.get("title",""),
                    r.get("priority",""),
                    r.get("description","")[:80],
                    r.get("placement_reason","")[:50]
                )
            console.print(t)

        # Future features table
        future = self.sm.get_by_bucket("FUTURE")
        if future:
            console.print(f"\n[bold cyan]FUTURE FEATURES ({len(future)} items)[/bold cyan]")
            t = Table(show_header=True, header_style="bold cyan")
            t.add_column("UID",         width=22)
            t.add_column("Title",       width=22)
            t.add_column("Priority",    width=10)
            t.add_column("Description", width=44)
            t.add_column("Reason",      width=28)
            for r in future:
                t.add_row(
                    r.get("uid",""),
                    r.get("title",""),
                    r.get("priority",""),
                    r.get("description","")[:80],
                    r.get("placement_reason","")[:50]
                )
            console.print(t)

        # Non-goals table
        if self.sm.non_goals:
            console.print(f"\n[bold red]EXPLICIT NON-GOALS ({len(self.sm.non_goals)} items)[/bold red]")
            t = Table(show_header=True, header_style="bold red")
            t.add_column("NG-UID",      width=22)
            t.add_column("Title",       width=22)
            t.add_column("Description", width=38)
            t.add_column("Reason",      width=34)
            for ng in self.sm.non_goals.values():
                t.add_row(
                    ng.get("uid",""),
                    ng.get("title",""),
                    ng.get("description","")[:60],
                    ng.get("reason","")[:55]
                )
            console.print(t)

        # Validation flags summary
        cons = stage3.get("contradictions", [])
        miss = stage3.get("missing_requirements", [])
        bias = stage3.get("bias_audit", [])
        eth  = stage3.get("product_ethics", [])
        ngc  = stage3.get("non_goal_conflicts", [])
        sss  = stage3.get("scope_explosion", {})
        tier = sss.get("severity_tier", "Unknown")
        tier_color = {"Minor":"green","Medium":"yellow","Major":"red"}.get(tier,"white")

        console.print(f"\n[bold]── VALIDATION FLAGS ──[/bold]")
        console.print(
            f"[bold]Scope severity:[/bold]       "
            f"[{tier_color}]{tier} (SSS: {sss.get('weighted_sss',0)}/100)[/{tier_color}]"
        )
        console.print(f"[bold]Contradictions:[/bold]       {len(cons)}")
        console.print(f"[bold]Missing requirements:[/bold] {len(miss)}")
        console.print(f"[bold]Bias flags:[/bold]           {len(bias)}")
        console.print(f"[bold]Ethics flags:[/bold]         {len(eth)}")
        console.print(f"[bold]Non-goal conflicts:[/bold]   {len(ngc)}")

        if cons:
            console.print("\n[bold red]Contradictions:[/bold red]")
            for c in cons:
                console.print(
                    f"  • {c.get('id','')} [{c.get('severity','')}] "
                    f"{c.get('description','')[:100]}"
                )

        if miss:
            console.print("\n[bold orange3]Missing requirements:[/bold orange3]")
            for m in miss:
                console.print(
                    f"  • {m.get('id','')} — {m.get('description','')[:100]}"
                )

        if self.sm.non_goals:
            console.print(f"\n[bold red]Standing non-goals (cannot be violated):[/bold red]")
            for ng in self.sm.non_goals.values():
                console.print(f"  ✗ {ng.get('uid','')} — {ng.get('title','')}")

    # ── Load requirements from 1A ─────────────────────────────
    def _load_requirements_from_1a(self, stage1a: dict):
        for req in stage1a.get("requirements", []):
            uid = self.sm.add_requirement(req)
            self.sm.requirements[uid]["status"] = "EXTRACTED"

    # ── Load scope from stage 2 ───────────────────────────────
    def _load_scope_from_stage2(self, stage2: dict):
        bucket_map = {
            "mvp_scope":       "MVP",
            "nice_to_have":    "NICE_TO_HAVE",
            "future_features": "FUTURE",
        }
        for key, bucket in bucket_map.items():
            for req in stage2.get(key, []):
                uid = req.get("uid")
                if uid and uid in self.sm.requirements:
                    self.sm.requirements[uid]["scope_bucket"]      = bucket
                    self.sm.requirements[uid]["placement_reason"]  = req.get("placement_reason","")
                    self.sm.requirements[uid]["status"]            = "CLARIFIED"
                else:
                    # not in session yet — add it
                    req["scope_bucket"] = bucket
                    new_uid = self.sm.add_requirement(req)
                    self.sm.requirements[new_uid]["status"] = "CLARIFIED"

        for req in stage2.get("new_requirements_surfaced", []):
            uid = req.get("uid")
            if uid and uid in self.sm.requirements:
                self.sm.requirements[uid]["status"] = "CLARIFIED"
            else:
                req["scope_bucket"] = "MVP"
                new_uid = self.sm.add_requirement(req)
                self.sm.requirements[new_uid]["status"] = "CLARIFIED"

        for ng in stage2.get("non_goals", []):
            self.sm.add_non_goal(ng)

    # ── Apply validation flags ────────────────────────────────
    def _apply_validation_flags(self, stage3: dict):
        for c in stage3.get("contradictions", []):
            for uid in c.get("req_uids", []):
                if uid in self.sm.requirements:
                    self.sm.add_flag(uid, "CONTRADICTION", c.get("description",""),
                                     blocking=False, source="stage3")

        for ngc in stage3.get("non_goal_conflicts", []):
            uid = ngc.get("requirement_uid")
            if uid and uid in self.sm.requirements:
                self.sm.add_flag(uid, "NON_GOAL_CONFLICT", ngc.get("description",""),
                                 blocking=True, source="stage3")

        for b in stage3.get("bias_audit", []):
            for uid in b.get("affected_uids", []):
                if uid in self.sm.requirements:
                    self.sm.add_flag(uid, "BIAS_AUDIT", b.get("description",""),
                                     blocking=False, source="stage3")

        for e in stage3.get("product_ethics", []):
            for uid in e.get("affected_uids", []):
                if uid in self.sm.requirements:
                    self.sm.add_flag(uid, "PRODUCT_ETHICS", e.get("description",""),
                                     blocking=False, source="stage3")

    # ── Advance to validated ──────────────────────────────────
    def _advance_to_validated(self, stage3: dict):
        for uid, req in self.sm.requirements.items():
            if req.get("status") == "CLARIFIED":
                self.sm.requirements[uid]["status"] = "VALIDATED"
                self.sm.requirements[uid]["status"] = "HUMAN_REVIEW"

    # ── JSON parser ───────────────────────────────────────────
    def _parse_json(self, raw: str, fix_sss: bool = False) -> dict:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            if fix_sss:
                lines     = raw.split('\n')
                sss_lines = [l for l in lines if '"weighted_sss"' in l]
                if len(sss_lines) > 1:
                    final_sss = sss_lines[-1]
                    seen      = False
                    cleaned   = []
                    for line in lines:
                        if '"weighted_sss"' in line:
                            if not seen:
                                cleaned.append(final_sss)
                                seen = True
                        else:
                            cleaned.append(line)
                    raw = '\n'.join(cleaned)
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass
            return {}