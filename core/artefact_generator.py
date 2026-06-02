import json
from pathlib import Path
from datetime import datetime

import config


# ══════════════════════════════════════════════════════════════
# ARTEFACT GENERATOR — Markdown output
# ══════════════════════════════════════════════════════════════
class ArtefactGenerator:
    """
    Generates a Markdown scope document from a completed Agent 1 session.
    Intended audience: downstream development team or handoff recipient.
    """

    def __init__(self, session_path: str):
        with open(session_path) as f:
            self.session = json.load(f)
        self.lines = []

    def generate(self, output_path: str = None) -> str:
        session_id = self.session.get("session_id", "UNKNOWN")

        if not output_path:
            output_dir = Path(config.OUTPUT_DIR)
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f"{session_id}_scope.md")

        self._build_header()
        self._build_summary()
        self._build_decisions()
        self._build_scope_buckets()
        self._build_non_goals()
        self._build_requirements_detail()
        self._build_validation_report()
        self._build_assumptions()
        self._build_hitl_log()
        self._build_footer()

        with open(output_path, "w") as f:
            f.write("\n".join(self.lines))

        return output_path

    # ── Helpers ───────────────────────────────────────────────
    def _add(self, line=""):
        self.lines.append(line)

    def _h1(self, text):
        self._add(f"# {text}")
        self._add()

    def _h2(self, text):
        self._add(f"## {text}")
        self._add()

    def _h3(self, text):
        self._add(f"### {text}")
        self._add()

    def _h4(self, text):
        self._add(f"#### {text}")
        self._add()

    def _body(self, text):
        self._add(text)
        self._add()

    def _bullet(self, text):
        self._add(f"- {text}")

    def _divider(self):
        self._add("---")
        self._add()

    def _badge(self, text, kind="default"):
        symbols = {
            "critical": "🔴",
            "high":     "🟠",
            "medium":   "🟡",
            "low":      "🟢",
            "mvp":      "✅",
            "nice":     "💛",
            "future":   "🔵",
            "flag":     "⚠️",
            "block":    "🚫",
            "check":    "✓",
            "decision": "📌",
            "lock":     "🔒",
        }
        return f"{symbols.get(kind, '')} {text}".strip()

    def _priority_badge(self, priority):
        mapping = {
            "Critical": self._badge(priority, "critical"),
            "High":     self._badge(priority, "high"),
            "Medium":   self._badge(priority, "medium"),
            "Low":      self._badge(priority, "low"),
        }
        return mapping.get(priority, priority)

    def _confidence_badge(self, confidence):
        mapping = {
            "HIGH":   "🟢 HIGH",
            "MEDIUM": "🟡 MEDIUM",
            "LOW":    "🔴 LOW",
        }
        return mapping.get(confidence, confidence)

    def _table_row(self, cells):
        self._add("| " + " | ".join(str(c) for c in cells) + " |")

    def _table_divider(self, count):
        self._add("| " + " | ".join(["---"] * count) + " |")

    # ── Header ────────────────────────────────────────────────
    def _build_header(self):
        session    = self.session
        session_id = session.get("session_id", "")
        created    = session.get("created_at", "")
        reqs       = session.get("requirements", {})
        non_goals  = session.get("non_goals", {})
        decisions  = session.get("decisions", [])
        assumptions = session.get("assumptions", [])

        self._add(f"# Scope Document")
        self._add()
        self._add(f"> **Agent 1 — Requirement Scoping Agent**  ")
        self._add(f"> Generated on `{created}` | Session `{session_id}`")
        self._add()
        self._divider()

        self._add("| Field | Value |")
        self._add("| --- | --- |")
        self._add(f"| Session ID | `{session_id}` |")
        self._add(f"| Generated | {created} |")
        self._add(f"| Total Requirements | {len(reqs)} |")
        self._add(f"| Non-goals | {len(non_goals)} |")
        self._add(f"| Key Decisions | {len(decisions)} |")
        self._add(f"| Assumptions | {len(assumptions)} |")
        self._add(f"| Status | {session.get('status', 'ACTIVE')} |")
        self._add()
        self._divider()

    # ── Summary ───────────────────────────────────────────────
    def _build_summary(self):
        self._h1("1. Summary")

        session = self.session
        reqs    = session.get("requirements", {})
        flags   = session.get("flags", {})

        mvp    = [r for r in reqs.values() if r.get("scope_bucket") == "MVP"]
        nth    = [r for r in reqs.values() if r.get("scope_bucket") == "NICE_TO_HAVE"]
        future = [r for r in reqs.values() if r.get("scope_bucket") == "FUTURE"]

        open_flags = sum(
            1 for fl_list in flags.values()
            for fl in fl_list if fl.get("status") == "OPEN"
        )
        blocking = sum(
            1 for fl_list in flags.values()
            for fl in fl_list
            if fl.get("status") == "OPEN" and fl.get("blocking")
        )
        advisory = open_flags - blocking

        self._add("| Metric | Value |")
        self._add("| --- | --- |")
        self._add(f"| ✅ MVP requirements | {len(mvp)} |")
        self._add(f"| 💛 Nice-to-have | {len(nth)} |")
        self._add(f"| 🔵 Future features | {len(future)} |")
        self._add(f"| 🚫 Explicit non-goals | {len(session.get('non_goals', {}))} |")
        self._add(f"| 🚫 Blocking flags (hard block) | {blocking} |")
        self._add(f"| ⚠️ Advisory flags (soft, non-blocking) | {advisory} |")
        self._add(f"| HITL 1 rounds | {len(session.get('hitl1_log', []))} |")
        self._add(f"| Key decisions | {len(session.get('decisions', []))} |")
        self._add()

        raw = session.get("raw_input", "")
        if raw:
            self._h2("Original Input")
            self._add(f"> {raw}")
            self._add()

        self._divider()

    # ── Decisions ─────────────────────────────────────────────
    def _build_decisions(self):
        decisions = self.session.get("decisions", [])
        if not decisions:
            return

        self._h1("2. Key Decisions")
        self._body(
            "These decisions were made during the clarification process "
            "and form the foundation of the scope."
        )

        self._add("| 📌 Decision | Rationale | Affected Requirements |")
        self._add("| --- | --- | --- |")
        for d in decisions:
            uids = ", ".join(d.get("affected_uids", [])) or "—"
            self._add(
                f"| {d.get('decision','')} "
                f"| {d.get('rationale','')} "
                f"| `{uids}` |"
            )
        self._add()
        self._divider()

    # ── Scope buckets ─────────────────────────────────────────
    def _build_scope_buckets(self):
        self._h1("3. Scope Definition")

        reqs = self.session.get("requirements", {})

        buckets = [
            ("MVP",          "3.1 ✅ MVP Scope",         "The minimum set of requirements needed to ship a working product."),
            ("NICE_TO_HAVE", "3.2 💛 Nice to Have",       "Valuable features that are not launch-blocking."),
            ("FUTURE",       "3.3 🔵 Future Features",    "Explicitly deferred to a later phase."),
        ]

        for bucket_key, title, description in buckets:
            items = [r for r in reqs.values() if r.get("scope_bucket") == bucket_key]
            if not items:
                continue

            self._h2(f"{title} ({len(items)} items)")
            self._body(description)

            self._add("| UID | Title | Priority | Description | Placement Reason |")
            self._add("| --- | --- | --- | --- | --- |")
            for r in items:
                self._add(
                    f"| `{r.get('uid','')}` "
                    f"| **{r.get('title','')}** "
                    f"| {self._priority_badge(r.get('priority',''))} "
                    f"| {r.get('description','')} "
                    f"| {r.get('placement_reason','')} |"
                )
            self._add()

        self._divider()

    # ── Non-goals ─────────────────────────────────────────────
    def _build_non_goals(self):
        non_goals = self.session.get("non_goals", {})
        if not non_goals:
            return

        self._h1("4. 🚫 Explicit Non-Goals")
        self._body(
            "These are deliberately excluded from this product phase. "
            "Each non-goal is derived from an explicit decision made during clarification. "
            "These are hard boundaries — not deferred features."
        )

        self._add("| NG-UID | Title | Description | Reason |")
        self._add("| --- | --- | --- | --- |")
        for ng in non_goals.values():
            self._add(
                f"| `{ng.get('uid','')}` "
                f"| **{ng.get('title','')}** "
                f"| {ng.get('description','')} "
                f"| {ng.get('reason','')} |"
            )
        self._add()
        self._divider()

    # ── Requirements detail ───────────────────────────────────
    def _build_requirements_detail(self):
        self._h1("5. Requirements Detail")
        self._body(
            "Full specification for each requirement including "
            "acceptance criteria, dependencies, and traceability."
        )

        reqs  = self.session.get("requirements", {})
        flags = self.session.get("flags", {})

        bucket_icon = {
            "MVP":          "✅",
            "NICE_TO_HAVE": "💛",
            "FUTURE":       "🔵",
        }

        for uid, req in reqs.items():
            bucket = req.get("scope_bucket", "UNKNOWN")
            icon   = bucket_icon.get(bucket, "⬜")

            self._h3(
                f"{icon} `{uid}` — {req.get('title', '')}"
            )

            # metadata row
            self._add("| Field | Value |")
            self._add("| --- | --- |")
            self._add(f"| **Priority** | {self._priority_badge(req.get('priority',''))} |")
            self._add(f"| **Confidence** | {self._confidence_badge(req.get('confidence',''))} |")
            self._add(f"| **Category** | {req.get('category','')} |")
            self._add(f"| **Status** | `{req.get('status','')}` |")
            self._add(f"| **Version** | `{req.get('version','V1')}` |")
            self._add(f"| **Bucket** | {bucket} |")
            self._add()

            # description
            self._add(f"**Description:** {req.get('description', '')}")
            self._add()

            # acceptance criteria
            criteria = req.get("acceptance_criteria", [])
            if criteria:
                self._add("**Acceptance Criteria:**")
                for c in criteria:
                    self._add(f"- ✓ {c}")
                self._add()

            # full traceability chain
            self._add("**Traceability Chain:**")
            self._add()
            self._add("| Stage | Reference | Detail |")
            self._add("| --- | --- | --- |")

            # source — original user input quote
            source = req.get("source_context") or req.get("source_quote", "")
            if source:
                self._add(f"| 📝 User Input | Source quote | {source} |")

            # ambiguities linked to this requirement
            ambs = req.get("related_ambiguities", [])
            if ambs:
                # look up the actual ambiguity questions from stage1b
                stage1b = self.session.get("stage_outputs", {}).get("stage1b", {}).get("output", {})
                all_ambs = (
                    stage1b.get("missing_requirements", []) +
                    stage1b.get("conflicts", []) +
                    stage1b.get("vague_statements", [])
                )
                amb_map = {a.get("id"): a for a in all_ambs}
                for amb_id in ambs:
                    amb = amb_map.get(amb_id, {})
                    q   = amb.get("clarification_question", "")
                    self._add(f"| ❓ Ambiguity | `{amb_id}` | {q} |")

            # HITL 1 resolutions linked via ambiguity refs
            hitl1_log = self.session.get("hitl1_log", [])
            all_resolutions = []
            for round_data in hitl1_log:
                all_resolutions.extend(round_data.get("resolutions", []))
            res_map = {r.get("ambiguity_ref"): r for r in all_resolutions}
            for amb_id in ambs:
                res = res_map.get(amb_id)
                if res:
                    self._add(
                        f"| 💬 HITL 1 Answer | `{amb_id}` resolved | "
                        f"{res.get('human_answer', '')[:120]} |"
                    )

            # decisions that affected this requirement
            decisions = self.session.get("decisions", [])
            uid = req.get("uid", "")
            for d in decisions:
                if uid in d.get("affected_uids", []):
                    self._add(f"| 📌 Decision | {d.get('decision','')} | {d.get('rationale','')} |")

            # validation findings
            flags = self.session.get("flags", {})
            req_flags = [f for f in flags.get(uid, []) if f.get("status") == "OPEN"]
            for fl in req_flags:
                self._add(
                    f"| {'🚫' if fl.get('blocking') else '⚠️'} Validation Flag | "
                    f"{fl.get('type','')} | {fl.get('description','')[:120]} |"
                )

            # approval
            hitl2_log = self.session.get("hitl2_log", [])
            for action in hitl2_log:
                if action.get("action") in ["APPROVED", "LOCKED"]:
                    self._add(
                        f"| ✅ Approval | {action.get('reviewer_id','')} | "
                        f"{action.get('action','')} on {action.get('timestamp','')[:16]} |"
                    )

            self._add()

            # dependencies
            deps = req.get("dependencies", [])
            if deps:
                self._add(f"**Dependencies:** {', '.join([f'`{d}`' for d in deps])}")
                self._add()

            # flags
            req_flags = [f for f in flags.get(uid, []) if f.get("status") == "OPEN"]
            if req_flags:
                for fl in req_flags:
                    blocking  = fl.get("blocking", False)
                    flag_icon = "🚫" if blocking else "⚠️"
                    flag_type = "HARD BLOCK" if blocking else "SOFT FLAG"
                    self._add(
                        f"> {flag_icon} **{flag_type} — {fl.get('type','')}:** "
                        f"{fl.get('description','')}"
                    )
                    self._add()

            self._add("---")
            self._add()

    # ── Validation report ─────────────────────────────────────
    def _build_validation_report(self):
        self._h1("6. Validation Report")

        stage3 = self.session.get("stage_outputs", {}).get("stage3", {}).get("output", {})
        if not stage3:
            self._body("No validation data available.")
            return

        status = stage3.get("validation_status", "UNKNOWN")
        status_icon = {
            "VALIDATED_CLEAN":      "✅",
            "VALIDATED_WITH_FLAGS": "⚠️",
            "VALIDATION_FAILED":    "🚫",
        }.get(status, "❓")

        self._add(f"**Validation Status:** {status_icon} `{status}`")
        self._add()

        # scope explosion
        scope = stage3.get("scope_explosion", {})
        if scope:
            self._h2("Scope Explosion Analysis")

            sss  = scope.get("weighted_sss", 0)
            tier = scope.get("severity_tier", "")
            tier_icon = {"Minor": "🟢", "Medium": "🟡", "Major": "🔴"}.get(tier, "⬜")
            veto = scope.get("hard_veto_triggered", False)

            factors = scope.get("factor_scores", {})
            factor_weights = {
                "requirement_impact":       0.25,
                "architectural_expansion":  0.25,
                "cross_cutting_complexity": 0.20,
                "timeline_pressure":        0.15,
                "dependency_growth":        0.15,
            }

            self._add("| Factor | Score | Weight | Contribution |")
            self._add("| --- | --- | --- | --- |")
            for factor, weight in factor_weights.items():
                score = factors.get(factor, 0)
                self._add(
                    f"| {factor.replace('_',' ').title()} "
                    f"| {score} "
                    f"| {int(weight*100)}% "
                    f"| {score * weight:.2f} |"
                )
            self._add()
            self._add(f"**Weighted SSS:** `{sss}/100` | **Severity:** {tier_icon} {tier}")
            if veto:
                self._add(f"> 🚫 **HARD VETO TRIGGERED:** {scope.get('hard_veto_reason','')}")
            self._add()
            self._body(scope.get("assessment", ""))

        # contradictions
        contradictions = stage3.get("contradictions", [])
        if contradictions:
            self._h2(f"Contradictions ({len(contradictions)})")
            self._add("| ID | Severity | Description | Recommendation |")
            self._add("| --- | --- | --- | --- |")
            for c in contradictions:
                self._add(
                    f"| {c.get('id','')} "
                    f"| {c.get('severity','')} "
                    f"| {c.get('description','')} "
                    f"| {c.get('recommendation','')} |"
                )
            self._add()

        # missing requirements
        missing = stage3.get("missing_requirements", [])
        if missing:
            self._h2(f"Missing Requirements ({len(missing)})")
            self._add("| ID | Severity | Description | Recommendation |")
            self._add("| --- | --- | --- | --- |")
            for m in missing:
                self._add(
                    f"| {m.get('id','')} "
                    f"| {m.get('severity','')} "
                    f"| {m.get('description','')} "
                    f"| {m.get('recommendation','')} |"
                )
            self._add()

        # bias audit
        bias = stage3.get("bias_audit", [])
        if bias:
            self._h2(f"Bias Audit ({len(bias)})")
            self._add("| ID | Type | Description | Recommendation |")
            self._add("| --- | --- | --- | --- |")
            for b in bias:
                self._add(
                    f"| {b.get('id','')} "
                    f"| {b.get('type','')} "
                    f"| {b.get('description','')} "
                    f"| {b.get('recommendation','')} |"
                )
            self._add()

        # product ethics
        ethics = stage3.get("product_ethics", [])
        if ethics:
            self._h2(f"Product Ethics ({len(ethics)})")
            self._add("| ID | Type | Description | Recommendation |")
            self._add("| --- | --- | --- | --- |")
            for e in ethics:
                self._add(
                    f"| {e.get('id','')} "
                    f"| {e.get('type','')} "
                    f"| {e.get('description','')} "
                    f"| {e.get('recommendation','')} |"
                )
            self._add()

        # non-goal conflicts
        ngc = stage3.get("non_goal_conflicts", [])
        if ngc:
            self._h2(f"Non-Goal Conflicts ({len(ngc)})")
            self._add("| ID | Req UID | NG UID | Description | Recommendation |")
            self._add("| --- | --- | --- | --- | --- |")
            for n in ngc:
                self._add(
                    f"| {n.get('id','')} "
                    f"| `{n.get('requirement_uid','')}` "
                    f"| `{n.get('non_goal_uid','')}` "
                    f"| {n.get('description','')} "
                    f"| {n.get('recommendation','')} |"
                )
            self._add()

        # summary
        summary = stage3.get("validation_summary", "")
        if summary:
            self._h2("Validation Summary")
            self._add(f"> {summary}")
            self._add()

        self._divider()

    # ── Assumptions ───────────────────────────────────────────
    def _build_assumptions(self):
        assumptions = self.session.get("assumptions", [])
        if not assumptions:
            return

        self._h1("7. Assumptions Register")
        self._body(
            "These assumptions were made when clarification questions could not be "
            "fully resolved. Validate with stakeholders before implementation."
        )

        self._add("| Ref | Assumption | Reason | Status |")
        self._add("| --- | --- | --- | --- |")
        for a in assumptions:
            self._add(
                f"| {a.get('ambiguity_ref','')} "
                f"| {a.get('assumption','')} "
                f"| {a.get('reason','')} "
                f"| `{a.get('status','ACTIVE')}` |"
            )
        self._add()
        self._divider()

    # ── HITL log ──────────────────────────────────────────────
    def _build_hitl_log(self):
        hitl1_log = self.session.get("hitl1_log", [])
        hitl2_log = self.session.get("hitl2_log", [])

        if not hitl1_log and not hitl2_log:
            return

        self._h1("8. Review Log")
        self._body("Complete audit trail of all human review actions.")

        if hitl1_log:
            self._h2("HITL 1 — Intent Checkpoint")
            for round_data in hitl1_log:
                self._h3(f"Round {round_data.get('round','?')}")
                resolutions = round_data.get("resolutions", [])
                if resolutions:
                    self._add("| Ref | Status | Answer | Note |")
                    self._add("| --- | --- | --- | --- |")
                    for r in resolutions:
                        s = r.get("status", "")
                        s_icon = "✅" if s == "RESOLVED" else "⚠️"
                        self._add(
                            f"| {r.get('ambiguity_ref','')} "
                            f"| {s_icon} {s} "
                            f"| {r.get('human_answer','')} "
                            f"| {r.get('resolution_note','')} |"
                        )
                    self._add()

        if hitl2_log:
            self._h2("HITL 2 — Scope Approval")
            self._add("| Reviewer | Action | Timestamp | Notes |")
            self._add("| --- | --- | --- | --- |")
            for action in hitl2_log:
                self._add(
                    f"| {action.get('reviewer_id','')} "
                    f"| **{action.get('action','')}** "
                    f"| {action.get('timestamp','')} "
                    f"| {action.get('notes','')} |"
                )
            self._add()

        self._divider()

    # ── Footer ────────────────────────────────────────────────
    def _build_footer(self):
        self._add()
        self._add("---")
        self._add()
        self._add(
            f"*Generated by Agent 1 — Requirement Scoping Agent "
            f"| Session `{self.session.get('session_id','')}` "
            f"| {self.session.get('created_at','')}*"
        )


# ══════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════
def generate_from_session(session_id: str = None,
                          session_path: str = None) -> str:
    if session_path:
        path = session_path
    elif session_id:
        path = str(Path(config.OUTPUT_DIR) / f"{session_id}.json")
    else:
        output_dir = Path(config.OUTPUT_DIR)
        sessions   = sorted(
            output_dir.glob("SES-*.json"),
            key=lambda p: p.stat().st_mtime
        )
        if not sessions:
            raise FileNotFoundError("No sessions found in output/ directory")
        path = str(sessions[-1])

    generator = ArtefactGenerator(path)
    md_path   = generator.generate()
    return md_path


if __name__ == "__main__":
    import sys
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    md_path    = generate_from_session(session_id=session_id)
    print(f"✅ Markdown artefact generated: {md_path}")