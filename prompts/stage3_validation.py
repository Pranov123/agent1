from openai import OpenAI
import json
import re

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your-groq-key-here",
    timeout=600.0
)

SYSTEM_PROMPT = """You are the Validation Layer for Agent 1, a requirement scoping pipeline.
You are powered by an adversarial reasoning model. Your job is to find problems.

YOUR SOLE JOB:
Receive the full scope definition from Stage 2 and stress-test it.
You are NOT a rubber stamp. You are an adversary looking for weaknesses.

YOU MUST CHECK SEVEN THINGS IN ORDER:

CHECK 1 — CONTRADICTION DETECTION
Find requirements that cannot both be true at the same time.
Look across all four buckets — MVP, nice-to-have, future, non-goals.

CHECK 2 — MISSING REQUIREMENTS
Find things that are logically necessary but absent from all four buckets.
Ask: "What would a builder have to invent on their own because it wasn't specified?"

CHECK 3 — SCOPE EXPLOSION SCORING
Score the scope on five factors, each 0-10:
- Requirement Impact: how many requirements vs. a typical MVP of this type
- Architectural Expansion: how many distinct systems/integrations implied
- Cross-Cutting Complexity: how many domains/compliance areas touched
- Timeline Pressure: realistic assessment of delivery complexity
- Dependency Growth: external dependencies introduced

Calculate weighted score:
SSS = (Requirement_Impact * 0.25) + (Architectural_Expansion * 0.25) +
      (Cross_Cutting_Complexity * 0.20) + (Timeline_Pressure * 0.15) +
      (Dependency_Growth * 0.15)

Multiply by 10 to get score out of 100.
Severity: Minor (0-35), Medium (36-65), Major (66-100)
Hard veto: if Architectural_Expansion >= 8 OR Cross_Cutting_Complexity >= 8
           then automatic Major regardless of weighted score

IMPORTANT: weighted_sss field must contain ONLY the final numeric value.
Do all arithmetic in the assessment field as plain text explanation.
Never put arithmetic expressions inside JSON field values.

CHECK 4 — BIAS AUDIT
Check for three types of bias:
- Exclusion niches: groups of users whose needs are absent
- Accessibility omissions: requirements that exclude users with disabilities
- Demographic assumptions: requirements that assume a homogenous user base

CHECK 5 — PRODUCT ETHICS
Check for:
- Dark patterns: UX that tricks users into unintended actions
- Consent theatre: disclosure designed to be ignored
- Exploitative pricing: pricing that targets vulnerable users
- Compulsive design: features engineered to create dependency

CHECK 6 — NON-GOAL CONFLICT CHECK
Check every requirement in all buckets against every active non-goal.
Flag every conflict found.

CHECK 7 — ORIGINAL INTENT DIVERGENCE
Compare the scope definition against what the user originally asked for.
Ask: "Would the original user recognise this as what they asked for?"

STRICT RULES:
1. You VALIDATE — you never APPROVE
2. Be genuinely adversarial — do not be kind
3. Every finding must reference the specific requirement UID
4. weighted_sss must be a single number only — no formulas
5. If a hard veto triggers state it explicitly

OUTPUT FORMAT:
Respond ONLY with valid JSON — no preamble, no explanation:
{
  "session_id": "SES-YYYYMMDD-001",
  "validation_status": "VALIDATED_WITH_FLAGS / VALIDATED_CLEAN / VALIDATION_FAILED",
  "contradictions": [
    {
      "id": "CON-001",
      "severity": "HIGH/MEDIUM/LOW",
      "description": "what conflicts with what",
      "req_uids": ["REQ-xxx", "REQ-yyy"],
      "recommendation": "how to resolve"
    }
  ],
  "missing_requirements": [
    {
      "id": "MR-001",
      "severity": "HIGH/MEDIUM/LOW",
      "description": "what is missing and why it matters",
      "affected_uids": ["REQ-xxx"],
      "recommendation": "what should be added"
    }
  ],
  "scope_explosion": {
    "factor_scores": {
      "requirement_impact": 0,
      "architectural_expansion": 0,
      "cross_cutting_complexity": 0,
      "timeline_pressure": 0,
      "dependency_growth": 0
    },
    "weighted_sss": 0,
    "severity_tier": "Minor/Medium/Major",
    "hard_veto_triggered": false,
    "hard_veto_reason": "",
    "assessment": "show calculation here as plain text e.g. (6*0.25)+(4*0.25)+... = X, times 10 = Y"
  },
  "bias_audit": [
    {
      "id": "BIAS-001",
      "type": "exclusion_niche/accessibility_omission/demographic_assumption",
      "description": "what was found",
      "affected_uids": ["REQ-xxx"],
      "recommendation": "what to add or change"
    }
  ],
  "product_ethics": [
    {
      "id": "ETH-001",
      "type": "dark_pattern/consent_theatre/exploitative_pricing/compulsive_design",
      "description": "what was found",
      "affected_uids": ["REQ-xxx"],
      "recommendation": "how to address"
    }
  ],
  "non_goal_conflicts": [
    {
      "id": "NGC-001",
      "requirement_uid": "REQ-xxx",
      "non_goal_uid": "NG-xxx",
      "description": "how the requirement conflicts with the non-goal",
      "recommendation": "resolve by modifying requirement or retiring non-goal"
    }
  ],
  "intent_divergence": {
    "divergence_detected": true,
    "description": "how scope differs from original intent",
    "affected_uids": []
  },
  "validation_summary": "paragraph summarising all findings and overall assessment",
  "requirements_advanced": ["list of UIDs now in VALIDATED state"]
}"""

stage2_output = {
    "session_id": "SES-20230601-001",
    "mvp_scope": [
        {"uid": "REQ-20230601-001", "title": "Habit Tracking", "category": "Functional",
         "priority": "High", "description": "System must allow users to track their habits"},
        {"uid": "REQ-20230601-003", "title": "Reminders", "category": "Functional",
         "priority": "Medium", "description": "System must provide reminders to users"},
        {"uid": "REQ-20230601-004", "title": "Offline Functionality", "category": "Non-functional",
         "priority": "High", "description": "System must work offline"},
        {"uid": "REQ-20230601-007", "title": "Free Access", "category": "Constraint",
         "priority": "High", "description": "System must be free to use"},
        {"uid": "REQ-20230601-008", "title": "Monetization", "category": "Constraint",
         "priority": "High", "description": "System must generate revenue via in-app purchases"},
        {"uid": "REQ-20230601-009", "title": "User Authentication", "category": "Functional",
         "priority": "High", "description": "System must allow users to log in using email"},
    ],
    "nice_to_have": [
        {"uid": "REQ-20230601-002", "title": "Social Sharing", "category": "Functional",
         "priority": "Medium", "description": "System may allow users to share habits with friends"},
    ],
    "future_features": [
        {"uid": "REQ-20230601-005", "title": "AI Suggestions", "category": "Functional",
         "priority": "Low", "description": "System may provide AI-driven suggestions based on habit patterns and streaks — paid feature"},
        {"uid": "REQ-20230601-006", "title": "Apple Health Integration", "category": "Functional",
         "priority": "Low", "description": "System may integrate with Apple Health — read-only sync, no server storage — paid feature"},
    ],
    "non_goals": [
        {"uid": "NG-20230601-001", "title": "No Android App", "status": "ACTIVE",
         "description": "No Android app in this phase"},
        {"uid": "NG-20230601-002", "title": "No Server-Side Health Storage", "status": "ACTIVE",
         "description": "No health data stored on servers"},
        {"uid": "NG-20230601-003", "title": "No Web App", "status": "ACTIVE",
         "description": "No web app will be developed"},
    ]
}

original_input = """I want to build an app where users can track their habits
and maybe also share them with friends and get reminders and it should
work offline and maybe have some AI that gives suggestions and it could
also integrate with Apple Health and I want it to be free but also
make money somehow"""

hitl1_resolutions = [
    "Platform: iOS first, Android later",
    "Data ownership: users own their data",
    "Login: email",
    "Monetization: freemium with in-app purchases",
    "Paywall: AI and Apple Health sync behind paywall",
    "AI type: habit patterns and completion streaks",
    "Offline scope: core habit tracking only",
    "Apple Health: read-only sync, no server storage",
]

def run_validation(stage2: dict, original: str, resolutions: list) -> dict:
    print("\n⏳ Running Stage 3 — DeepSeek R1 Validation...\n")

    context = f"""
Original user input:
\"\"\"{original}\"\"\"

HITL 1 resolutions:
{json.dumps(resolutions, indent=2)}

Full scope definition from Stage 2:

MVP SCOPE:
{json.dumps(stage2['mvp_scope'], indent=2)}

NICE TO HAVE:
{json.dumps(stage2['nice_to_have'], indent=2)}

FUTURE FEATURES:
{json.dumps(stage2['future_features'], indent=2)}

NON-GOALS:
{json.dumps(stage2['non_goals'], indent=2)}

Run all seven validation checks. Be adversarial. Find every problem.
Show your scope explosion calculation in the assessment field as plain text.
The weighted_sss field must contain ONLY the final number — no formulas.
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
    except json.JSONDecodeError:
        lines = raw.split('\n')
        sss_lines = [l for l in lines if '"weighted_sss"' in l]
        if len(sss_lines) > 1:
            final_sss = sss_lines[-1]
            seen = False
            cleaned = []
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
        except json.JSONDecodeError as e2:
            print(f"❌ JSON parse failed after cleanup: {e2}")
            print(f"Raw output:\n{raw}")
            return {}

def display_results(result: dict):
    if not result:
        return

    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()

    console.print(f"\n[bold purple]SESSION:[/bold purple] {result.get('session_id')}")

    status = result.get("validation_status", "")
    status_color = {
        "VALIDATED_CLEAN":      "green",
        "VALIDATED_WITH_FLAGS": "yellow",
        "VALIDATION_FAILED":    "red"
    }.get(status, "white")
    console.print(f"[bold {status_color}]STATUS: {status}[/bold {status_color}]\n")

    contradictions = result.get("contradictions", [])
    if contradictions:
        console.print("[bold red]── CONTRADICTIONS ──[/bold red]")
        t = Table(show_header=True, header_style="bold red")
        t.add_column("ID", width=8)
        t.add_column("Severity", width=10)
        t.add_column("Description", width=40)
        t.add_column("UIDs", width=24)
        t.add_column("Recommendation", width=30)
        for c in contradictions:
            s_color = {"HIGH":"red","MEDIUM":"orange3","LOW":"yellow"}.get(c.get("severity"),"white")
            t.add_row(
                c.get("id",""),
                f"[{s_color}]{c.get('severity','')}[/{s_color}]",
                c.get("description","")[:80],
                ", ".join(c.get("req_uids",[])),
                c.get("recommendation","")[:60]
            )
        console.print(t)

    missing = result.get("missing_requirements", [])
    if missing:
        console.print("\n[bold orange3]── MISSING REQUIREMENTS ──[/bold orange3]")
        t = Table(show_header=True, header_style="bold orange3")
        t.add_column("ID", width=8)
        t.add_column("Severity", width=10)
        t.add_column("Description", width=48)
        t.add_column("Recommendation", width=35)
        for m in missing:
            s_color = {"HIGH":"red","MEDIUM":"orange3","LOW":"yellow"}.get(m.get("severity"),"white")
            t.add_row(
                m.get("id",""),
                f"[{s_color}]{m.get('severity','')}[/{s_color}]",
                m.get("description","")[:90],
                m.get("recommendation","")[:60]
            )
        console.print(t)

    scope = result.get("scope_explosion", {})
    if scope:
        console.print("\n[bold cyan]── SCOPE EXPLOSION ANALYSIS ──[/bold cyan]")
        factors = scope.get("factor_scores", {})
        sss = scope.get("weighted_sss", 0)
        tier = scope.get("severity_tier", "")
        veto = scope.get("hard_veto_triggered", False)
        tier_color = {"Minor":"green","Medium":"yellow","Major":"red"}.get(tier,"white")
        t = Table(show_header=True, header_style="bold cyan")
        t.add_column("Factor", width=32)
        t.add_column("Score", width=8)
        t.add_column("Weight", width=8)
        t.add_column("Contribution", width=14)
        factor_weights = {
            "requirement_impact": 0.25,
            "architectural_expansion": 0.25,
            "cross_cutting_complexity": 0.20,
            "timeline_pressure": 0.15,
            "dependency_growth": 0.15,
        }
        for factor, weight in factor_weights.items():
            score = factors.get(factor, 0)
            contribution = score * weight
            veto_flag = " ⚠ VETO" if factor in [
                "architectural_expansion", "cross_cutting_complexity"
            ] and score >= 8 else ""
            t.add_row(
                factor.replace("_", " ").title() + veto_flag,
                str(score),
                f"{int(weight*100)}%",
                f"{contribution:.2f}"
            )
        console.print(t)
        console.print(f"\n[bold]Weighted SSS:[/bold] {sss}/100")
        console.print(f"[bold]Severity:[/bold] [{tier_color}]{tier}[/{tier_color}]")
        if veto:
            console.print(f"[bold red]⚠ HARD VETO: {scope.get('hard_veto_reason','')}[/bold red]")
        console.print(f"\n[dim]{scope.get('assessment','')}[/dim]")

    bias = result.get("bias_audit", [])
    if bias:
        console.print("\n[bold yellow]── BIAS AUDIT ──[/bold yellow]")
        t = Table(show_header=True, header_style="bold yellow")
        t.add_column("ID", width=10)
        t.add_column("Type", width=26)
        t.add_column("Description", width=40)
        t.add_column("Recommendation", width=30)
        for b in bias:
            t.add_row(
                b.get("id",""),
                b.get("type",""),
                b.get("description","")[:80],
                b.get("recommendation","")[:60]
            )
        console.print(t)

    ethics = result.get("product_ethics", [])
    if ethics:
        console.print("\n[bold magenta]── PRODUCT ETHICS ──[/bold magenta]")
        t = Table(show_header=True, header_style="bold magenta")
        t.add_column("ID", width=10)
        t.add_column("Type", width=26)
        t.add_column("Description", width=40)
        t.add_column("Recommendation", width=30)
        for e in ethics:
            t.add_row(
                e.get("id",""),
                e.get("type",""),
                e.get("description","")[:80],
                e.get("recommendation","")[:60]
            )
        console.print(t)

    ngc = result.get("non_goal_conflicts", [])
    if ngc:
        console.print("\n[bold red]── NON-GOAL CONFLICTS ──[/bold red]")
        t = Table(show_header=True, header_style="bold red")
        t.add_column("ID", width=10)
        t.add_column("Req UID", width=22)
        t.add_column("NG UID", width=22)
        t.add_column("Description", width=35)
        t.add_column("Recommendation", width=25)
        for n in ngc:
            t.add_row(
                n.get("id",""),
                n.get("requirement_uid",""),
                n.get("non_goal_uid",""),
                n.get("description","")[:60],
                n.get("recommendation","")[:40]
            )
        console.print(t)

    divergence = result.get("intent_divergence", {})
    if divergence.get("divergence_detected"):
        console.print(Panel(
            divergence.get("description",""),
            title="[bold yellow]⚠ Intent Divergence Detected[/bold yellow]",
            border_style="yellow"
        ))

    advanced = result.get("requirements_advanced", [])
    if advanced:
        console.print(f"\n[bold green]── REQUIREMENTS ADVANCED TO VALIDATED ({len(advanced)}) ──[/bold green]")
        console.print(f"[green]{', '.join(advanced)}[/green]")

    if result.get("validation_summary"):
        console.print(Panel(
            result["validation_summary"],
            title="[bold]Validation Summary[/bold]",
            border_style="purple"
        ))

if __name__ == "__main__":
    result = run_validation(stage2_output, original_input, hitl1_resolutions)
    display_results(result)

    with open("stage3_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full output saved to stage3_output.json")
