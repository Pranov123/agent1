import json
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

import config

# ── Colour palette ────────────────────────────────────────────
PURPLE     = colors.HexColor("#4B3AAB")
TEAL       = colors.HexColor("#0F6E56")
AMBER      = colors.HexColor("#854F0B")
RED        = colors.HexColor("#A32D2D")
BLUE       = colors.HexColor("#185FA5")
DARK_GRAY  = colors.HexColor("#444441")
LIGHT_GRAY = colors.HexColor("#F1EFE8")
MID_GRAY   = colors.HexColor("#CCCCCC")
WHITE      = colors.white
GREEN      = colors.HexColor("#3B6D11")
ORANGE     = colors.HexColor("#8B4513")

# ── Style definitions ─────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontSize=32, textColor=PURPLE,
            spaceAfter=8, fontName="Helvetica-Bold",
            alignment=TA_CENTER
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base["Normal"],
            fontSize=14, textColor=TEAL,
            spaceAfter=6, fontName="Helvetica",
            alignment=TA_CENTER
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", parent=base["Normal"],
            fontSize=10, textColor=DARK_GRAY,
            spaceAfter=4, fontName="Helvetica",
            alignment=TA_CENTER
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontSize=16, textColor=PURPLE,
            spaceBefore=16, spaceAfter=6,
            fontName="Helvetica-Bold"
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontSize=12, textColor=TEAL,
            spaceBefore=12, spaceAfter=4,
            fontName="Helvetica-Bold"
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"],
            fontSize=10, textColor=DARK_GRAY,
            spaceBefore=8, spaceAfter=3,
            fontName="Helvetica-Bold"
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=9, textColor=DARK_GRAY,
            spaceAfter=4, fontName="Helvetica",
            leading=14
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontSize=9, textColor=DARK_GRAY,
            spaceAfter=2, fontName="Helvetica",
            leftIndent=12, leading=13
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontSize=8, textColor=DARK_GRAY,
            fontName="Helvetica-Bold"
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"],
            fontSize=8, textColor=DARK_GRAY,
            fontName="Helvetica"
        ),
        "tag_green": ParagraphStyle(
            "tag_green", parent=base["Normal"],
            fontSize=8, textColor=GREEN,
            fontName="Helvetica-Bold"
        ),
        "tag_amber": ParagraphStyle(
            "tag_amber", parent=base["Normal"],
            fontSize=8, textColor=AMBER,
            fontName="Helvetica-Bold"
        ),
        "tag_red": ParagraphStyle(
            "tag_red", parent=base["Normal"],
            fontSize=8, textColor=RED,
            fontName="Helvetica-Bold"
        ),
        "tag_blue": ParagraphStyle(
            "tag_blue", parent=base["Normal"],
            fontSize=8, textColor=BLUE,
            fontName="Helvetica-Bold"
        ),
        "note": ParagraphStyle(
            "note", parent=base["Normal"],
            fontSize=8, textColor=BLUE,
            fontName="Helvetica-Oblique",
            leftIndent=8, spaceAfter=4
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontSize=7, textColor=MID_GRAY,
            fontName="Helvetica",
            alignment=TA_CENTER
        ),
    }
    return styles


# ── Table style helpers ───────────────────────────────────────
def header_table_style(header_color=PURPLE):
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  header_color),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  8),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("TEXTCOLOR",   (0, 1), (-1, -1), DARK_GRAY),
        ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])


def priority_color(priority: str):
    return {
        "Critical": RED,
        "High":     ORANGE,
        "Medium":   AMBER,
        "Low":      GREEN,
    }.get(priority, DARK_GRAY)


def confidence_color(confidence: str):
    return {
        "HIGH":   GREEN,
        "MEDIUM": AMBER,
        "LOW":    RED,
    }.get(confidence, DARK_GRAY)


# ══════════════════════════════════════════════════════════════
# ARTEFACT GENERATOR
# ══════════════════════════════════════════════════════════════
class ArtefactGenerator:
    """
    Generates a PDF scope document from a completed Agent 1 session.
    Intended audience: downstream development team or handoff recipient.
    """

    def __init__(self, session_path: str):
        with open(session_path) as f:
            self.session = json.load(f)
        self.styles = build_styles()
        self.story  = []

    def generate(self, output_path: str = None) -> str:
        session_id = self.session.get("session_id", "UNKNOWN")

        if not output_path:
            output_dir = Path(config.OUTPUT_DIR)
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f"{session_id}_scope.pdf")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=20*mm,  bottomMargin=20*mm,
            title=f"Scope Document — {session_id}",
            author="Agent 1 — Requirement Scoping Agent",
        )

        self._build_cover()
        self._build_summary()
        self._build_raw_input()
        self._build_decisions()
        self._build_scope_buckets()
        self._build_non_goals()
        self._build_requirements_detail()
        self._build_validation_report()
        self._build_assumptions()
        self._build_hitl_log()

        doc.build(self.story)
        return output_path

    # ── Helpers ───────────────────────────────────────────────
    def _add(self, *elements):
        for el in elements:
            self.story.append(el)

    def _h1(self, text):
        self._add(
            HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=4),
            Paragraph(text, self.styles["h1"])
        )

    def _h2(self, text):
        self._add(Paragraph(text, self.styles["h2"]))

    def _h3(self, text):
        self._add(Paragraph(text, self.styles["h3"]))

    def _body(self, text):
        self._add(Paragraph(text, self.styles["body"]))

    def _bullet(self, text):
        self._add(Paragraph(f"• {text}", self.styles["bullet"]))

    def _space(self, h=4):
        self._add(Spacer(1, h*mm))

    def _note(self, text):
        self._add(Paragraph(f"ℹ  {text}", self.styles["note"]))

    def _page_break(self):
        self._add(PageBreak())

    def _colored_para(self, text, color):
        style = ParagraphStyle(
            "tmp", parent=self.styles["body"],
            textColor=color, fontName="Helvetica-Bold"
        )
        return Paragraph(text, style)

    # ── Cover page ────────────────────────────────────────────
    def _build_cover(self):
        session    = self.session
        session_id = session.get("session_id", "")
        created    = session.get("created_at", "")[:10]

        self._space(30)
        self._add(Paragraph("SCOPE DOCUMENT", self.styles["cover_title"]))
        self._space(2)
        self._add(Paragraph("Agent 1 — Requirement Scoping Agent", self.styles["cover_sub"]))
        self._space(8)
        self._add(HRFlowable(width="60%", thickness=2, color=PURPLE,
                              hAlign="CENTER", spaceAfter=8))
        self._space(4)

        reqs        = session.get("requirements", {})
        non_goals   = session.get("non_goals", {})
        decisions   = session.get("decisions", [])
        assumptions = session.get("assumptions", [])

        meta_data = [
            ["Session ID",    session_id],
            ["Generated",     created],
            ["Requirements",  str(len(reqs))],
            ["Non-goals",     str(len(non_goals))],
            ["Key decisions", str(len(decisions))],
            ["Assumptions",   str(len(assumptions))],
            ["Status",        session.get("status", "ACTIVE")],
        ]

        w = 180*mm
        col_w = [60*mm, 120*mm]
        table_data = [[
            Paragraph(k, self.styles["label"]),
            Paragraph(v, self.styles["value"])
        ] for k, v in meta_data]

        t = Table(table_data, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (0, -1), LIGHT_GRAY),
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
        ]))
        self._add(t)
        self._page_break()

    # ── Executive summary ─────────────────────────────────────
    def _build_summary(self):
        self._h1("1. Executive Summary")
        session = self.session

        reqs      = session.get("requirements", {})
        mvp       = [r for r in reqs.values() if r.get("scope_bucket") == "MVP"]
        nth       = [r for r in reqs.values() if r.get("scope_bucket") == "NICE_TO_HAVE"]
        future    = [r for r in reqs.values() if r.get("scope_bucket") == "FUTURE"]
        non_goals = session.get("non_goals", {})
        flags     = session.get("flags", {})

        open_flags = sum(
            1 for fl_list in flags.values()
            for fl in fl_list if fl.get("status") == "OPEN"
        )
        blocking_flags = sum(
            1 for fl_list in flags.values()
            for fl in fl_list
            if fl.get("status") == "OPEN" and fl.get("blocking")
        )

        summary_data = [
            ["Metric", "Value"],
            ["MVP requirements",      str(len(mvp))],
            ["Nice-to-have",          str(len(nth))],
            ["Future features",       str(len(future))],
            ["Explicit non-goals",    str(len(non_goals))],
            ["Open flags",            str(open_flags)],
            ["Blocking flags",        str(blocking_flags)],
            ["HITL 1 rounds used",    str(len(session.get("hitl1_log", [])))],
            ["Key decisions logged",  str(len(session.get("decisions", [])))],
        ]

        col_w = [90*mm, 80*mm]
        t = Table(summary_data, colWidths=col_w)
        t.setStyle(header_table_style(TEAL))
        self._add(t)
        self._space()

        # raw input summary
        raw = session.get("raw_input", "")
        if raw:
            self._h2("Original Input")
            self._body(raw[:500] + ("..." if len(raw) > 500 else ""))
        self._space()

    # ── Raw input ─────────────────────────────────────────────
    def _build_raw_input(self):
        pass  # already shown in summary

    # ── Key decisions ─────────────────────────────────────────
    def _build_decisions(self):
        decisions = self.session.get("decisions", [])
        if not decisions:
            return

        self._h1("2. Key Decisions")
        self._body(
            "The following decisions were made during the clarification process "
            "and form the foundation of the scope definition."
        )
        self._space(2)

        data = [["Decision", "Rationale", "Affected Requirements"]]
        for d in decisions:
            data.append([
                Paragraph(d.get("decision", ""), self.styles["body"]),
                Paragraph(d.get("rationale", ""), self.styles["body"]),
                Paragraph(
                    ", ".join(d.get("affected_uids", [])) or "—",
                    self.styles["body"]
                ),
            ])

        col_w = [65*mm, 75*mm, 35*mm]
        t = Table(data, colWidths=col_w)
        t.setStyle(header_table_style(PURPLE))
        self._add(t)
        self._space()

    # ── Scope buckets ─────────────────────────────────────────
    def _build_scope_buckets(self):
        self._h1("3. Scope Definition")
        reqs = self.session.get("requirements", {})

        buckets = [
            ("MVP",          "3.1 MVP Scope",          TEAL,   "The minimum set of requirements needed to ship a working product."),
            ("NICE_TO_HAVE", "3.2 Nice to Have",        AMBER,  "Valuable features that are not launch-blocking."),
            ("FUTURE",       "3.3 Future Features",     BLUE,   "Explicitly deferred to a later phase."),
        ]

        for bucket_key, title, color, description in buckets:
            items = [r for r in reqs.values() if r.get("scope_bucket") == bucket_key]
            if not items:
                continue

            self._h2(f"{title} ({len(items)} items)")
            self._body(description)
            self._space(2)

            data = [["UID", "Title", "Priority", "Description", "Placement Reason"]]
            for r in items:
                p = r.get("priority", "")
                data.append([
                    Paragraph(r.get("uid", ""), self.styles["value"]),
                    Paragraph(r.get("title", ""), self.styles["label"]),
                    self._colored_para(p, priority_color(p)),
                    Paragraph(r.get("description", "")[:120], self.styles["value"]),
                    Paragraph(r.get("placement_reason", "")[:80], self.styles["value"]),
                ])

            col_w = [25*mm, 30*mm, 18*mm, 60*mm, 42*mm]
            t = Table(data, colWidths=col_w)
            t.setStyle(header_table_style(color))
            self._add(t)
            self._space(3)

    # ── Non-goals ─────────────────────────────────────────────
    def _build_non_goals(self):
        non_goals = self.session.get("non_goals", {})
        if not non_goals:
            return

        self._h1("4. Explicit Non-Goals")
        self._body(
            "The following are deliberately excluded from this product phase. "
            "Each non-goal is derived from an explicit decision made during clarification. "
            "These are hard boundaries — not deferred features."
        )
        self._space(2)

        data = [["NG-UID", "Title", "Description", "Reason"]]
        for ng in non_goals.values():
            data.append([
                Paragraph(ng.get("uid", ""), self.styles["value"]),
                Paragraph(ng.get("title", ""), self.styles["label"]),
                Paragraph(ng.get("description", "")[:100], self.styles["value"]),
                Paragraph(ng.get("reason", "")[:100], self.styles["value"]),
            ])

        col_w = [25*mm, 35*mm, 55*mm, 60*mm]
        t = Table(data, colWidths=col_w)
        t.setStyle(header_table_style(RED))
        self._add(t)
        self._space()

    # ── Requirements detail ───────────────────────────────────
    def _build_requirements_detail(self):
        self._page_break()
        self._h1("5. Requirements Detail")
        self._body(
            "Full specification for each requirement including acceptance criteria, "
            "dependencies, and traceability information."
        )
        self._space(2)

        reqs = self.session.get("requirements", {})
        flags = self.session.get("flags", {})

        for uid, req in reqs.items():
            bucket = req.get("scope_bucket", "UNKNOWN")
            bucket_color = {
                "MVP":          TEAL,
                "NICE_TO_HAVE": AMBER,
                "FUTURE":       BLUE,
            }.get(bucket, DARK_GRAY)

            # requirement header
            header_data = [[
                Paragraph(uid, self.styles["label"]),
                Paragraph(req.get("title", ""), self.styles["h3"]),
                self._colored_para(bucket, bucket_color),
                self._colored_para(
                    req.get("priority", ""),
                    priority_color(req.get("priority", ""))
                ),
                self._colored_para(
                    req.get("confidence", ""),
                    confidence_color(req.get("confidence", ""))
                ),
            ]]

            t = Table(header_data, colWidths=[28*mm, 55*mm, 28*mm, 22*mm, 22*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, -1), LIGHT_GRAY),
                ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
                ("TOPPADDING",  (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ]))
            self._add(t)

            # description
            desc_data = [[
                Paragraph("Description", self.styles["label"]),
                Paragraph(req.get("description", ""), self.styles["body"]),
            ]]
            t = Table(desc_data, colWidths=[28*mm, 147*mm])
            t.setStyle(TableStyle([
                ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
                ("TOPPADDING",  (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ]))
            self._add(t)

            # acceptance criteria
            criteria = req.get("acceptance_criteria", [])
            if criteria:
                criteria_text = "\n".join([f"✓  {c}" for c in criteria])
                crit_data = [[
                    Paragraph("Acceptance Criteria", self.styles["label"]),
                    Paragraph(criteria_text.replace("\n", "<br/>"), self.styles["body"]),
                ]]
                t = Table(crit_data, colWidths=[28*mm, 147*mm])
                t.setStyle(TableStyle([
                    ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
                    ("TOPPADDING",  (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN",      (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND",  (0, 0), (0, -1), LIGHT_GRAY),
                ]))
                self._add(t)

            # dependencies + related ambiguities
            deps = req.get("dependencies", [])
            ambs = req.get("related_ambiguities", [])
            if deps or ambs:
                meta_data = [[
                    Paragraph("Dependencies", self.styles["label"]),
                    Paragraph(", ".join(deps) if deps else "None", self.styles["body"]),
                    Paragraph("Related Ambiguities", self.styles["label"]),
                    Paragraph(", ".join(ambs) if ambs else "None", self.styles["body"]),
                ]]
                t = Table(meta_data, colWidths=[28*mm, 55*mm, 36*mm, 56*mm])
                t.setStyle(TableStyle([
                    ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
                    ("TOPPADDING",  (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND",  (0, 0), (0, -1), LIGHT_GRAY),
                    ("BACKGROUND",  (2, 0), (2, -1), LIGHT_GRAY),
                ]))
                self._add(t)

            # flags
            req_flags = [f for f in flags.get(uid, []) if f.get("status") == "OPEN"]
            if req_flags:
                for fl in req_flags:
                    blocking = fl.get("blocking", False)
                    flag_color = RED if blocking else AMBER
                    flag_label = "HARD BLOCK" if blocking else "SOFT FLAG"
                    flag_data = [[
                        self._colored_para(f"⚠ {flag_label}: {fl.get('type','')}", flag_color),
                        Paragraph(fl.get("description", "")[:150], self.styles["body"]),
                    ]]
                    t = Table(flag_data, colWidths=[40*mm, 135*mm])
                    t.setStyle(TableStyle([
                        ("GRID",        (0, 0), (-1, -1), 0.3, flag_color),
                        ("TOPPADDING",  (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ]))
                    self._add(t)

            # status + version
            status_data = [[
                Paragraph("Status", self.styles["label"]),
                Paragraph(req.get("status", ""), self.styles["body"]),
                Paragraph("Version", self.styles["label"]),
                Paragraph(req.get("version", "V1"), self.styles["body"]),
                Paragraph("Category", self.styles["label"]),
                Paragraph(req.get("category", ""), self.styles["body"]),
            ]]
            t = Table(status_data, colWidths=[20*mm, 35*mm, 18*mm, 20*mm, 22*mm, 60*mm])
            t.setStyle(TableStyle([
                ("GRID",        (0, 0), (-1, -1), 0.3, MID_GRAY),
                ("TOPPADDING",  (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND",  (0, 0), (0, -1), LIGHT_GRAY),
                ("BACKGROUND",  (2, 0), (2, -1), LIGHT_GRAY),
                ("BACKGROUND",  (4, 0), (4, -1), LIGHT_GRAY),
            ]))
            self._add(t)
            self._space(4)

    # ── Validation report ─────────────────────────────────────
    def _build_validation_report(self):
        self._page_break()
        self._h1("6. Validation Report")

        stage3 = self.session.get("stage_outputs", {}).get("stage3", {}).get("output", {})
        if not stage3:
            self._body("No validation data available.")
            return

        status = stage3.get("validation_status", "UNKNOWN")
        status_color = {
            "VALIDATED_CLEAN":      GREEN,
            "VALIDATED_WITH_FLAGS": AMBER,
            "VALIDATION_FAILED":    RED,
        }.get(status, DARK_GRAY)

        self._add(self._colored_para(f"Validation Status: {status}", status_color))
        self._space(2)

        # scope explosion
        scope = stage3.get("scope_explosion", {})
        if scope:
            self._h2("Scope Explosion Analysis")
            factors = scope.get("factor_scores", {})
            sss     = scope.get("weighted_sss", 0)
            tier    = scope.get("severity_tier", "")
            tier_color = {"Minor": GREEN, "Medium": AMBER, "Major": RED}.get(tier, DARK_GRAY)

            factor_data = [["Factor", "Score", "Weight", "Contribution"]]
            factor_weights = {
                "requirement_impact":       0.25,
                "architectural_expansion":  0.25,
                "cross_cutting_complexity": 0.20,
                "timeline_pressure":        0.15,
                "dependency_growth":        0.15,
            }
            for factor, weight in factor_weights.items():
                score = factors.get(factor, 0)
                factor_data.append([
                    factor.replace("_", " ").title(),
                    str(score),
                    f"{int(weight*100)}%",
                    f"{score * weight:.2f}",
                ])

            t = Table(factor_data, colWidths=[70*mm, 25*mm, 25*mm, 35*mm])
            t.setStyle(header_table_style(BLUE))
            self._add(t)
            self._space(2)
            self._add(self._colored_para(
                f"Weighted SSS: {sss}/100 — Severity: {tier}", tier_color
            ))
            self._body(scope.get("assessment", ""))
            self._space(3)

        # contradictions
        contradictions = stage3.get("contradictions", [])
        if contradictions:
            self._h2(f"Contradictions ({len(contradictions)})")
            data = [["ID", "Severity", "Description", "Recommendation"]]
            for c in contradictions:
                data.append([
                    c.get("id", ""),
                    c.get("severity", ""),
                    Paragraph(c.get("description", "")[:120], self.styles["body"]),
                    Paragraph(c.get("recommendation", "")[:100], self.styles["body"]),
                ])
            t = Table(data, colWidths=[15*mm, 20*mm, 80*mm, 60*mm])
            t.setStyle(header_table_style(RED))
            self._add(t)
            self._space(3)

        # missing requirements
        missing = stage3.get("missing_requirements", [])
        if missing:
            self._h2(f"Missing Requirements ({len(missing)})")
            data = [["ID", "Severity", "Description", "Recommendation"]]
            for m in missing:
                data.append([
                    m.get("id", ""),
                    m.get("severity", ""),
                    Paragraph(m.get("description", "")[:120], self.styles["body"]),
                    Paragraph(m.get("recommendation", "")[:100], self.styles["body"]),
                ])
            t = Table(data, colWidths=[15*mm, 20*mm, 80*mm, 60*mm])
            t.setStyle(header_table_style(AMBER))
            self._add(t)
            self._space(3)

        # bias audit
        bias = stage3.get("bias_audit", [])
        if bias:
            self._h2(f"Bias Audit ({len(bias)})")
            data = [["ID", "Type", "Description", "Recommendation"]]
            for b in bias:
                data.append([
                    b.get("id", ""),
                    b.get("type", ""),
                    Paragraph(b.get("description", "")[:120], self.styles["body"]),
                    Paragraph(b.get("recommendation", "")[:100], self.styles["body"]),
                ])
            t = Table(data, colWidths=[15*mm, 35*mm, 75*mm, 50*mm])
            t.setStyle(header_table_style(AMBER))
            self._add(t)
            self._space(3)

        # product ethics
        ethics = stage3.get("product_ethics", [])
        if ethics:
            self._h2(f"Product Ethics ({len(ethics)})")
            data = [["ID", "Type", "Description", "Recommendation"]]
            for e in ethics:
                data.append([
                    e.get("id", ""),
                    e.get("type", ""),
                    Paragraph(e.get("description", "")[:120], self.styles["body"]),
                    Paragraph(e.get("recommendation", "")[:100], self.styles["body"]),
                ])
            t = Table(data, colWidths=[15*mm, 35*mm, 75*mm, 50*mm])
            t.setStyle(header_table_style(colors.HexColor("#6B21A8")))
            self._add(t)
            self._space(3)

        # validation summary
        summary = stage3.get("validation_summary", "")
        if summary:
            self._h2("Validation Summary")
            self._body(summary)

    # ── Assumptions ───────────────────────────────────────────
    def _build_assumptions(self):
        assumptions = self.session.get("assumptions", [])
        if not assumptions:
            return

        self._page_break()
        self._h1("7. Assumptions Register")
        self._body(
            "The following assumptions were made when clarification questions "
            "could not be fully resolved. These must be validated with stakeholders "
            "before implementation."
        )
        self._space(2)

        data = [["Ref", "Assumption", "Reason", "Status"]]
        for a in assumptions:
            data.append([
                a.get("ambiguity_ref", ""),
                Paragraph(a.get("assumption", ""), self.styles["body"]),
                Paragraph(a.get("reason", ""), self.styles["body"]),
                a.get("status", "ACTIVE"),
            ])

        t = Table(data, colWidths=[15*mm, 75*mm, 65*mm, 20*mm])
        t.setStyle(header_table_style(AMBER))
        self._add(t)
        self._space()

    # ── HITL log ──────────────────────────────────────────────
    def _build_hitl_log(self):
        hitl1_log = self.session.get("hitl1_log", [])
        hitl2_log = self.session.get("hitl2_log", [])

        if not hitl1_log and not hitl2_log:
            return

        self._page_break()
        self._h1("8. Review Log")
        self._body("Complete audit trail of all human review actions.")

        if hitl1_log:
            self._h2("HITL 1 — Intent Checkpoint")
            for round_data in hitl1_log:
                self._h3(f"Round {round_data.get('round', '?')}")
                resolutions = round_data.get("resolutions", [])
                if resolutions:
                    data = [["Ref", "Status", "Answer", "Note"]]
                    for r in resolutions:
                        s = r.get("status", "")
                        s_color = GREEN if s == "RESOLVED" else AMBER
                        data.append([
                            r.get("ambiguity_ref", ""),
                            self._colored_para(s, s_color),
                            Paragraph(r.get("human_answer", "")[:100], self.styles["body"]),
                            Paragraph(r.get("resolution_note", "")[:80], self.styles["body"]),
                        ])
                    t = Table(data, colWidths=[15*mm, 25*mm, 80*mm, 55*mm])
                    t.setStyle(header_table_style(TEAL))
                    self._add(t)
                    self._space(3)

        if hitl2_log:
            self._h2("HITL 2 — Scope Approval")
            data = [["Reviewer", "Action", "Timestamp", "Notes"]]
            for action in hitl2_log:
                data.append([
                    action.get("reviewer_id", ""),
                    action.get("action", ""),
                    action.get("timestamp", "")[:16],
                    Paragraph(action.get("notes", "")[:100], self.styles["body"]),
                ])
            t = Table(data, colWidths=[30*mm, 30*mm, 35*mm, 80*mm])
            t.setStyle(header_table_style(PURPLE))
            self._add(t)


# ══════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════
def generate_from_session(session_id: str = None, session_path: str = None) -> str:
    """
    Generate a PDF artefact from a session.
    Pass either a session_id (looks in output/) or a full session_path.
    """
    if session_path:
        path = session_path
    elif session_id:
        path = str(Path(config.OUTPUT_DIR) / f"{session_id}.json")
    else:
        # use most recent session
        output_dir = Path(config.OUTPUT_DIR)
        sessions   = sorted(output_dir.glob("SES-*.json"), key=lambda p: p.stat().st_mtime)
        if not sessions:
            raise FileNotFoundError("No sessions found in output/ directory")
        path = str(sessions[-1])

    generator = ArtefactGenerator(path)
    pdf_path  = generator.generate()
    return pdf_path


if __name__ == "__main__":
    import sys
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    pdf_path   = generate_from_session(session_id=session_id)
    print(f"✅ PDF generated: {pdf_path}")