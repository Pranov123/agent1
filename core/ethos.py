import json
from datetime import datetime
from core import get_client, get_primary_model, get_validation_model
import config

# ── Risk tier constants ───────────────────────────────────────
RISK_LOW    = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH   = "HIGH"

# ── Confidence band constants ─────────────────────────────────
BAND_HIGH      = "HIGH"       # >= 0.72
BAND_UNCERTAIN = "UNCERTAIN"  # 0.50 - 0.71
BAND_LOW       = "LOW"        # < 0.50

# ── Review levels ─────────────────────────────────────────────
REVIEW_STANDARD        = "STANDARD"
REVIEW_INDEPENDENT     = "INDEPENDENT_REVIEW"
REVIEW_SENIOR          = "SENIOR_REVIEW"
REVIEW_EXTERNAL_AUDIT  = "EXTERNAL_AUDIT"

# ── Pattern severity weights ──────────────────────────────────
PATTERN_SEVERITY = {
    "algorithmic_decisions":  1.0,
    "health_data":            0.9,
    "financial_data":         0.9,
    "employee_monitoring":    0.9,
    "covert_surveillance":    1.0,
    "child_users_sensitive":  0.7,
    "child_exploitation":     1.0,  
    "regulated_industry":     0.8,
    "pii_handling":           0.5,
    "third_party_sharing":    0.5,
    "behavioural_profiling":  0.6,
    "location_tracking":      0.5,
    "biometric_processing":   0.8,
    "data_retention":         0.3,
}

HIGH_SEVERITY_PATTERNS = {
    "algorithmic_decisions",
    "covert_surveillance",
    "employee_monitoring",
    "child_exploitation",
}

# ── Auto-escalation — specific phrases only ───────────────────
# FIX: HR domain removed from auto-escalation
# HR only escalates if high-severity patterns detected
AUTO_ESCALATE_PHRASES = [
    "patient records",
    "clinical decision",
    "medical diagnosis",
    "treatment plan",
    "electronic health record",
    "ehr system",
    "hipaa",
    "medical device",
    "fda regulated",
    "financial transactions",
    "payment processing",
    "banking system",
    "investment advice",
    "monitor employees",
    "track employee",
    "employee communications",
    "surveillance system",
    "without their knowledge",
    "without user consent",
]

# FIX: hr_workforce removed — only clinical healthcare and fintech auto-escalate
AUTO_ESCALATE_DOMAINS = {
    "healthcare":      "clinical/diagnostic healthcare system detected",
    "fintech":         "financial services domain detected",
    "legal_compliance":"legal/compliance domain detected",
}


# ══════════════════════════════════════════════════════════════
# ETHOS ENGINE
# ══════════════════════════════════════════════════════════════
class ETHOSEngine:

    def __init__(self):
        self.client           = get_client()
        self.primary_model    = get_primary_model()
        self.validation_model = get_validation_model()

    # ── Main entry point ──────────────────────────────────────
    def run(self, raw_input: str,
            hitl1_context: str = "") -> dict:
        context = raw_input
        if hitl1_context:
            context = (
                f"{raw_input}\n\n"
                f"Clarifications from HITL 1:\n{hitl1_context}"
            )
            
        self._current_input = raw_input
        domain_result  = self._run_domain_inference(context)
        pattern_result = self._run_risk_patterns(context)

        auto_escalated, escalation_reason = self._check_auto_escalation(
            domain_result, raw_input
        )

        output = self._aggregate(
            domain_result,
            pattern_result,
            auto_escalated,
            escalation_reason,
            is_rerun=bool(hitl1_context)
        )

        return output

    # ── Stage 1A — Semantic domain inference ─────────────────
    def _run_domain_inference(self, context: str) -> dict:
        SYSTEM_PROMPT = """You are the Semantic Domain Inference engine for ETHOS governance.

DOMAIN DEFINITIONS:
- consumer_app: general consumer mobile or web product (fitness, productivity, lifestyle)
- saas: business software sold as a service to organisations
- hardware_iot: physical device with embedded software as the PRIMARY product
  USE THIS if a dedicated physical device is required for the product to function
  Examples: smart bottle, wearable, smart lock, drone, sensor, tracker
- healthcare: ONLY clinical, diagnostic, treatment, patient-record, or FDA-regulated medical systems
  NOTE: wellness apps, fitness trackers, hydration reminders, sleep apps are NOT healthcare
  NOTE: healthcare = doctors + patients + diagnoses + treatments + medical records
- fintech: payment processing, banking, investment, insurance systems
- hr_workforce: employee management, hiring, scheduling, leave management, payroll
  NOTE: hr_workforce does NOT imply monitoring — it is a neutral domain
- legal_compliance: legal case management, regulatory compliance tools
- ecommerce: retail, marketplace, shopping
- social: social networks, community, messaging
- productivity: task management, notes, collaboration
- education: learning, courses, student management
- other: none of the above

STRICT RULES:
1. If a dedicated physical device is the core product, primary domain = hardware_iot
2. wellness, hydration, fitness, sleep tracking = consumer_app NOT healthcare
3. hr_workforce = neutral workplace tool, NOT automatically risky
4. confidence must be honest — if unsure, set below 0.6
5. secondary_domains: list up to 2 relevant additional domains

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "primary_domain": "hardware_iot",
  "secondary_domains": ["consumer_app"],
  "confidence": 0.88,
  "domain_reasoning": "one sentence explaining the classification"
}"""

        response = self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Classify:\n\n{context}"}
            ],
            temperature=0.1
        )
        return self._parse_json(response.choices[0].message.content)

    # ── Stage 1B — Risk pattern detection ────────────────────
    def _run_risk_patterns(self, context: str) -> dict:
        SYSTEM_PROMPT = """You are the Risk Pattern Detection engine for ETHOS governance.

PATTERNS AND DEFINITIONS:
- pii_handling: personal identifiable information explicitly collected
- health_data: REGULATED health/medical data — NOT general wellness/fitness
- financial_data: payment, banking, financial transaction data
- employee_monitoring: The system EXPLICITLY tracks or records employee
  BEHAVIOUR, COMMUNICATIONS, KEYSTROKES, SCREEN ACTIVITY, or PRODUCTIVITY.
  DOES NOT INCLUDE: leave requests, attendance records, scheduling,
  payroll, directories, performance reviews, or standard HR admin.
  REQUIRES explicit words: "monitor", "track productivity",
  "record communications", "surveillance", "keystroke", "screen capture".
- child_users_sensitive: System collects BEHAVIOURAL data, location,
  or communications FROM children and uses it for profiling or targeting.
  DOES NOT INCLUDE: attendance tracking, grades, learning progress.
  School admin tools = NOT this pattern.
  REQUIRES explicit sensitive processing involving children.
- child_exploitation: System targets, exploits, or harms children.
- covert_surveillance: monitoring without user knowledge or consent
- algorithmic_decisions: automated decisions affecting legal rights or employment
- regulated_industry: explicitly under HIPAA, PCI, GDPR enforcement
- data_retention: long-term storage of personal data
- third_party_sharing: data explicitly shared with third parties
- location_tracking: precise real-time location data collected
- behavioural_profiling: behaviour patterns analysed for profiling purposes
- biometric_processing: facial recognition, fingerprint,
  iris scan, voiceprint, or other biometric identifiers

STRICT RULES:
1. Only flag with DIRECT evidence — quote the input
2. General wellness/fitness/hydration is NOT health_data
3. Storing usage data is NOT behavioural_profiling
4. Working offline is NOT data_retention
5. If you cannot quote evidence, do NOT flag

IMPORTANT NEGATIVE EXAMPLES:
- Attendance tracking is NOT pii_handling.
- School attendance systems are NOT pii_handling.
- Class rosters are NOT pii_handling.
- Grades and academic progress are NOT pii_handling.
- Parent notifications are NOT pii_handling.
- Learning management systems are NOT pii_handling.
- Educational administration systems are NOT pii_handling.

Only flag pii_handling when the input explicitly states:
- collection of personal information,
- storage of personal information,
- sharing of personal information,
- selling of personal information,
- processing of personal information,
- or handling of personally identifiable information (PII).

OUTPUT FORMAT — valid JSON only, no preamble:
{
  "patterns_detected": [
    {
      "pattern": "pii_handling",
      "severity": 0.5,
      "confidence": 0.8,
      "evidence": "exact quote from input"
    }
  ],
  "overall_risk_signal": "LOW",
  "pattern_reasoning": "one sentence"
}"""

        response = self.client.chat.completions.create(
            model=self.validation_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Detect risk patterns in:\n\n{context}"}
            ],
            temperature=0.1
        )
        return self._parse_json(response.choices[0].message.content)

    # ── Auto-escalation ───────────────────────────────────────
    def _check_auto_escalation(self, domain_result: dict,
                                raw_input: str) -> tuple[bool, str]:
        input_lower    = raw_input.lower()
        primary_domain = domain_result.get("primary_domain", "").lower()

        if primary_domain in AUTO_ESCALATE_DOMAINS:
            return True, AUTO_ESCALATE_DOMAINS[primary_domain]

        for phrase in AUTO_ESCALATE_PHRASES:
            if phrase in input_lower:
                return True, f"specific phrase '{phrase}' detected"

        return False, ""

    # ── Convergent aggregator ─────────────────────────────────
    def _aggregate(self, domain_result: dict, pattern_result: dict,
                   auto_escalated: bool, escalation_reason: str,
                   is_rerun: bool) -> dict:

        domain_confidence = domain_result.get("confidence", 0.5)
        primary_domain    = domain_result.get("primary_domain", "other")
        patterns          = pattern_result.get("patterns_detected", [])
        risk_signal       = pattern_result.get("overall_risk_signal", "LOW")

        # pattern confidence — use domain confidence as neutral baseline
        if patterns:
            pattern_confidence = (
                sum(p.get("confidence", 0.5) for p in patterns) / len(patterns)
            )
        else:
            pattern_confidence = domain_confidence

        # disagreement penalty
        domain_risk_proxy = {
            "healthcare": 0.9, "fintech": 0.9, "hr_workforce": 0.4,
            "legal_compliance": 0.8, "other": 0.3, "consumer_app": 0.2,
            "hardware_iot": 0.2, "saas": 0.4, "social": 0.5,
            "productivity": 0.2, "education": 0.3, "ecommerce": 0.3,
        }.get(primary_domain, 0.4)

        pattern_risk_proxy = {
            "LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.9
        }.get(risk_signal, 0.4)

        disagreement         = abs(domain_risk_proxy - pattern_risk_proxy)
        disagreement_penalty = round(disagreement * 0.3, 3)

        # patterns are primary evidence — weight them more heavily when present
        if patterns:
            combined_confidence = (
                (domain_confidence * 0.35) +
                (pattern_confidence * 0.65) -
                disagreement_penalty
            )
        else:
            combined_confidence = (
                (domain_confidence * 0.6) +
                (pattern_confidence * 0.4) -
                disagreement_penalty
            )
            
        # input quality scales confidence without flattening it
        input_quality = self._assess_input_quality(
            self._current_input if hasattr(self, '_current_input') else ""
        )
        # multiply rather than cap — preserves variation
        combined_confidence = round(
            max(0.10, min(0.95,
                combined_confidence * input_quality
            )),
            3
        )
        
        # confidence band
        if combined_confidence >= config.ETHOS_CONFIDENCE_THRESHOLD_HIGH:
            band = BAND_HIGH
        elif combined_confidence >= config.ETHOS_CONFIDENCE_THRESHOLD_UNCERTAIN:
            band = BAND_UNCERTAIN
        else:
            band = BAND_LOW

        # risk tier — based on evidence only, NOT confidence
        severity_score = self._calculate_pattern_severity(patterns)

        if auto_escalated:
            risk_tier         = RISK_HIGH
            escalation_source = "AUTO_ESCALATION"
        elif severity_score >= 0.85:
            risk_tier         = RISK_HIGH
            escalation_source = "HIGH_SEVERITY_PATTERNS"
        elif severity_score >= 0.45:
            risk_tier         = RISK_MEDIUM
            escalation_source = "MEDIUM_SEVERITY_PATTERNS"
        elif risk_signal == "HIGH":
            risk_tier         = RISK_HIGH
            escalation_source = "PATTERN_SIGNAL"
        elif risk_signal == "MEDIUM":
            risk_tier         = RISK_MEDIUM
            escalation_source = "PATTERN_SIGNAL"
        elif primary_domain == "hr_workforce":
            risk_tier         = RISK_LOW
            escalation_source = "HR_ADMINISTRATIVE"
        elif band == BAND_LOW and primary_domain == "other":
            risk_tier         = RISK_MEDIUM
            escalation_source = "AMBIGUOUS_INPUT"
        else:
            risk_tier         = RISK_LOW
            escalation_source = "HEURISTIC_CLEAN"
            
        risk_category = self._classify_risk_category(
            patterns, auto_escalated, escalation_reason, primary_domain
        )

        # governance decision — separated from risk tier
        governance = self._build_governance_decision(
            risk_tier, band, auto_escalated
        )

        # ambiguity flag
        is_ambiguous   = band in [BAND_LOW, BAND_UNCERTAIN]
        ambiguity_note = ""
        if is_ambiguous:
            ambiguity_note = (
                f"Confidence is {band} ({combined_confidence}). "
                f"Risk tier reflects evidence — governance controls elevated. "
                f"Human must review classification at HITL 2."
            )

        # domain clarification question
        domain_clarification_question = ""
        if band == BAND_LOW:
            domain_clarification_question = self._build_domain_clarification(
                primary_domain,
                domain_result.get("domain_reasoning", "")
            )

        # final escalation reason
        if auto_escalated:
            final_reason = escalation_reason
        else:
            final_reason = (
                f"{escalation_source} | "
                f"Domain: {primary_domain} | "
                f"Patterns: {len(patterns)} | "
                f"Severity: {severity_score:.2f}"
            )

        return {
            # ── Primary outputs ───────────────────────────────
            "risk_tier":                      risk_tier,
            "risk_category":                  risk_category,
            "recommended_action":             governance["recommended_action"],
            "review_level":                   governance["review_level"],
            "governance_required":            governance["governance_required"],
            "confidence_score":               combined_confidence,
            "confidence_band":                band,

            # ── Governance decision (structured) ──────────────
            "governance_decision":            governance,

            # ── Traceability — raw engine outputs ─────────────
            "raw_domain_inference": {
                "primary_domain":    primary_domain,
                "secondary_domains": domain_result.get("secondary_domains", []),
                "confidence":        domain_confidence,
                "reasoning":         domain_result.get("domain_reasoning", ""),
            },
            "raw_pattern_detection": {
                "patterns_detected":  patterns,
                "overall_risk_signal": risk_signal,
                "reasoning":          pattern_result.get("pattern_reasoning", ""),
                "severity_score":     round(severity_score, 3),
                "risk_category":      risk_category, 
            },

            # ── Escalation traceability ───────────────────────
            "escalation_reason":              final_reason,
            "escalation_source":              escalation_source,
            "auto_escalated":                 auto_escalated,
            "disagreement_penalty":           disagreement_penalty,

            # ── Ambiguity ─────────────────────────────────────
            "is_ambiguous":                   is_ambiguous,
            "ambiguity_note":                 ambiguity_note,
            "domain_clarification_question":  domain_clarification_question,

            # ── Convenience fields ────────────────────────────
            "domain":                         primary_domain,
            "secondary_domains":              domain_result.get("secondary_domains", []),
            "patterns_detected":              patterns,
            "pattern_severity_score":         round(severity_score, 3),

            # ── Meta ──────────────────────────────────────────
            "ethos_rerun_triggered":          is_rerun,
            "generated_at":                   datetime.now().isoformat(),
        }
    
    def _classify_risk_category(self, patterns: list, auto_escalated: bool,
                              escalation_reason: str,
                              primary_domain: str) -> str:
        """
        Classify the primary reason for the risk tier.
        Helps reviewers understand WHY a project is risky.
        """
        if auto_escalated:
            reason = escalation_reason.lower()

            if any(x in reason for x in [
                "monitor",
                "surveillance",
                "employee",
                "communications"
            ]):
                return "SURVEILLANCE"

            if any(x in reason for x in [
                "financial",
                "bank",
                "payment",
                "fintech"
            ]):
                return "REGULATORY"

            if any(x in reason for x in [
                "medical",
                "clinical",
                "healthcare",
                "patient"
            ]):
                return "REGULATORY"

            return "REGULATORY"

        if not patterns:
            return "NONE"

        # check for highest severity pattern type
        pattern_names = {p.get("pattern") for p in patterns}

        if (
            "algorithmic_decisions" in pattern_names
            and primary_domain == "hr_workforce"
        ):
            return "EMPLOYMENT_DECISION"
        if "algorithmic_decisions" in pattern_names:
            return "ALGORITHMIC_DECISION"
        if "covert_surveillance" in pattern_names or "employee_monitoring" in pattern_names:
            return "SURVEILLANCE"
        if "health_data" in pattern_names:
            return "REGULATORY"
        if "financial_data" in pattern_names:
            return "REGULATORY"
        if "child_users_sensitive" in pattern_names:
            return "SAFETY"
        if "child_exploitation" in pattern_names:
            return "SAFETY"
        if "pii_handling" in pattern_names or "behavioural_profiling" in pattern_names:
            return "PRIVACY"
        if "regulated_industry" in pattern_names:
            return "REGULATORY"

        return "PRIVACY"

    # ── Pattern severity calculator ───────────────────────────
    def _calculate_pattern_severity(self, patterns: list) -> float:
        if not patterns:
            return 0.0

        total = 0.0
        for p in patterns:
            name       = p.get("pattern", "")
            confidence = p.get("confidence", 0.5)
            severity   = p.get("severity") or PATTERN_SEVERITY.get(name, 0.4)
            total     += severity * confidence

            if name in HIGH_SEVERITY_PATTERNS and confidence >= 0.7:
                total = max(total, 0.85)

        return min(1.0, total)

    # ── Governance decision builder ───────────────────────────
    def _build_governance_decision(self, risk_tier: str, band: str,
                                    auto_escalated: bool) -> dict:
        base = {
            RISK_LOW: {
                "review_level":         REVIEW_STANDARD,
                "audit_required":       False,
                "governance_required":  False,
                "recommended_action":   "Standard HITL review. No elevated governance.",
            },
            RISK_MEDIUM: {
                "review_level":         REVIEW_INDEPENDENT,
                "audit_required":       False,
                "governance_required":  True,
                "recommended_action":   (
                    "Independent reviewer required at HITL 2. "
                    "Session initiator cannot self-review."
                ),
            },
            RISK_HIGH: {
                "review_level":         REVIEW_SENIOR,
                "audit_required":       True,
                "governance_required":  True,
                "recommended_action":   (
                    "Senior stakeholder co-sign mandatory. "
                    "External audit required at HITL 2."
                ),
            },
        }

        decision = dict(base.get(risk_tier, base[RISK_LOW]))

        # confidence band elevates governance controls without changing risk_tier
        if band == BAND_LOW:
            if decision["review_level"] == REVIEW_STANDARD:
                decision["review_level"] = REVIEW_INDEPENDENT
            decision["classification_review_required"] = True
            decision["recommended_action"] += (
                " ADDITIONALLY: Confidence LOW — human must confirm "
                "or override risk classification at HITL 2."
            )
        elif band == BAND_UNCERTAIN:
            decision["classification_review_required"] = True
            decision["recommended_action"] += (
                " NOTE: Confidence UNCERTAIN — "
                "human should review classification at HITL 2."
            )
        else:
            decision["classification_review_required"] = False

        return decision

    # ── Domain clarification question ─────────────────────────
    def _build_domain_clarification(self, domain: str,
                                     reasoning: str) -> str:
        questions = {
            "other":        "What is the primary purpose and intended audience?",
            "consumer_app": "Is this for general consumers or a specific professional group?",
            "saas":         "What industry or business type is this primarily serving?",
            "hardware_iot": "Is this a consumer device or industrial/enterprise?",
            "social":       "Is this for general public or a specific community?",
            "hr_workforce": (
                "Does the system only manage HR administration "
                "(leave, payroll, scheduling), or does it monitor "
                "employees or make employment decisions?"
            ),
        }
        return questions.get(
            domain,
            "Can you clarify the primary purpose and intended audience?"
        )

    # ── JSON parser ───────────────────────────────────────────
    def _parse_json(self, raw: str) -> dict:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
        
    def _assess_input_quality(self, raw_input: str) -> float:
        """
        Returns 0.3 - 1.0 as a multiplier.
        Scales confidence without flattening it.
        Short vague input: 0.3-0.5 (halves confidence)
        Detailed specific input: 0.85-1.0 (minimal reduction)
        """
        if not raw_input:
            return 0.4
        words      = raw_input.split()
        word_count = len(words)

        if word_count < 5:
            base = 0.65
        elif word_count < 10:
            base = 0.82
        elif word_count < 15:
            base = 0.90
        elif word_count < 25:
            base = 0.95
        else:
            base = 1.0

        specific_terms = [
            "patient","invoice","employee","transaction","diagnosis",
            "medical","payment","clinical","financial","monitor",
            "track","sync","offline","bluetooth","encrypt","gdpr",
            "hipaa","compliance","sensor","database","authentication",
            "biometric","surveillance","algorithm","automated","decision",
        ]
        bonus = sum(0.03 for term in specific_terms if term in raw_input.lower())
        return min(1.0, base + bonus)