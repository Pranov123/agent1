from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your-groq-key-here"
)

# ── Output schema ─────────────────────────────────────────────
class Requirement(BaseModel):
    uid: str
    title: str
    description: str
    category: str        # Functional / Non-functional / Constraint / Assumption
    priority: str        # Critical / High / Medium / Low
    status: str          # EXTRACTED
    dependencies: list[str]
    source_quote: str    # exact phrase from user input that led to this requirement
    confidence: str      # HIGH / MEDIUM / LOW - how clearly stated it was

class ExtractionResult(BaseModel):
    session_id: str
    raw_input: str
    requirements: list[Requirement]
    extraction_notes: str   # anything unusual about the input

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Requirement Extractor for Agent 1, a requirement scoping pipeline.

YOUR SOLE JOB:
Extract atomic, traceable requirements from raw user input. Nothing more.

STRICT RULES — these are non-negotiable:

1. NEVER invent requirements that are not stated or strongly implied by the user input.
2. NEVER include implementation details, technology choices, or architecture decisions.
   BAD: "System must use PostgreSQL for data storage"
   GOOD: "System must persistently store user data"
3. NEVER include vague requirements you cannot later validate or test.
   BAD: "System should be good"
   GOOD: "System must respond to user actions within 2 seconds" (only if stated)
4. NEVER combine two requirements into one. Each requirement must be atomic.
   BAD: "System must allow login and registration"
   GOOD: REQ-001 "System must allow user login" + REQ-002 "System must allow user registration"
5. NEVER hallucinate. If something is not stated or directly implied, it does not exist.
6. If the user used words like "maybe", "could", "might", "possibly" — mark confidence: LOW
7. If clearly stated with no hedging — mark confidence: HIGH
8. If implied but not directly stated — mark confidence: MEDIU
9. Mark implementation-laden language — if the user said "use WebSockets", extract the
   functional need (real-time updates) not the technology.

WHAT YOU MUST DO:

- Extract every requirement clearly stated in the input
- Extract requirements that are STRONGLY IMPLIED (mark confidence: LOW)
- Assign a uid in format REQ-YYYYMMDD-NNN (use today's date)
- Assign category: Functional, Non-functional, Constraint, or Assumption
- Assign priority: Critical, High, Medium, Low — based on how the user described importance
  If no priority is indicated, assign Medium
- Record the exact source_quote from the input that led to each requirement
- Note dependencies between requirements (by uid) where obvious

OUTPUT FORMAT:
Respond ONLY with a valid JSON object matching this exact structure — no preamble, no explanation:
{
  "session_id": "SES-YYYYMMDD-001",
  "raw_input": "<the full input you received>",
  "requirements": [
    {
      "uid": "REQ-YYYYMMDD-001",
      "title": "short title",
      "description": "clear, testable description of what is required",
      "category": "Functional",
      "priority": "High",
      "status": "EXTRACTED",
      "dependencies": [],
      "source_quote": "exact phrase from input",
      "confidence": "HIGH"
    }
  ],
  "extraction_notes": "any observations about the input quality or extraction decisions"
}"""

# ── Test input ─────────────────────────────────────────────────
test_input = """I want to build an app where users can track their habits 
and maybe also share them with friends and get reminders and it should 
work offline and maybe have some AI that gives suggestions and it could 
also integrate with Apple Health and I want it to be free but also 
make money somehow"""

# ── Run extraction ─────────────────────────────────────────────
def run_extraction(user_input: str) -> dict:
    print("\n⏳ Running Stage 1A — Requirement Extraction...\n")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract requirements from this input:\n\n{user_input}"}
        ],
        temperature=0.1   # low temperature — we want consistent, precise extraction
    )
    
    raw_output = response.choices[0].message.content
    
    # strip any markdown code fences if model wraps output
    if "```json" in raw_output:
        raw_output = raw_output.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_output:
        raw_output = raw_output.split("```")[1].split("```")[0].strip()
    
    try:
        result = json.loads(raw_output)
        return result
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")
        print(f"Raw output was:\n{raw_output}")
        return {}

# ── Pretty print results ───────────────────────────────────────
def display_results(result: dict):
    if not result:
        return
    
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    
    console = Console()
    
    console.print(f"\n[bold purple]SESSION:[/bold purple] {result.get('session_id')}")
    console.print(f"[bold purple]REQUIREMENTS EXTRACTED:[/bold purple] {len(result.get('requirements', []))}\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("UID", style="dim", width=18)
    table.add_column("Title", width=24)
    table.add_column("Category", width=16)
    table.add_column("Priority", width=10)
    table.add_column("Confidence", width=10)
    table.add_column("Description", width=40)
    
    for req in result.get("requirements", []):
        priority_color = {
            "Critical": "red", "High": "orange3",
            "Medium": "yellow", "Low": "green"
        }.get(req.get("priority"), "white")
        
        conf_color = {
            "HIGH": "green", "MEDIUM": "yellow", "LOW": "red"
        }.get(req.get("confidence"), "white")
        
        table.add_row(
            req.get("uid", ""),
            req.get("title", ""),
            req.get("category", ""),
            f"[{priority_color}]{req.get('priority', '')}[/{priority_color}]",
            f"[{conf_color}]{req.get('confidence', '')}[/{conf_color}]",
            req.get("description", "")[:80]
        )
    
    console.print(table)
    
    if result.get("extraction_notes"):
        console.print(f"\n[bold]Extraction Notes:[/bold] {result['extraction_notes']}")

# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_extraction(test_input)
    display_results(result)
    
    # save raw output for inspection
    with open("stage1a_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full output saved to stage1a_output.json")
