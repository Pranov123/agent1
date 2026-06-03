from datetime import datetime

# ── Valid states ──────────────────────────────────────────────
STATES = [
    "DRAFT",
    "EXTRACTED",
    "CLARIFICATION_PENDING",
    "CLARIFIED",
    "VALIDATED",
    "HUMAN_REVIEW",
    "ESCALATED",
    "DISPUTED",
    "APPROVED",
    "LOCKED",
    "REJECTED",
    "DEPRECATED",
    "REINSTATED",
    "ROLLBACK",
]

# ── Valid transitions ─────────────────────────────────────────
# (from_state, to_state) -> who can trigger it
# "system" = automatic
# "human"  = human only
# "any"    = either

TRANSITIONS = {
    ("DRAFT",                 "EXTRACTED")            : "system",
    ("EXTRACTED",             "CLARIFICATION_PENDING"): "system",
    ("EXTRACTED",             "CLARIFIED")            : "system",
    ("CLARIFICATION_PENDING", "CLARIFIED")            : "human",
    ("CLARIFIED",             "VALIDATED")            : "system",
    ("VALIDATED",             "HUMAN_REVIEW")         : "system",
    ("HUMAN_REVIEW",          "APPROVED")             : "human",
    ("HUMAN_REVIEW",          "REJECTED")             : "human",
    ("HUMAN_REVIEW",          "ESCALATED")            : "human",
    ("HUMAN_REVIEW",          "DISPUTED")             : "human",
    ("ESCALATED",             "HUMAN_REVIEW")         : "human",
    ("ESCALATED",             "REJECTED")             : "human",
    ("DISPUTED",              "HUMAN_REVIEW")         : "human",
    ("DISPUTED",              "REJECTED")             : "human",
    ("APPROVED",              "LOCKED")               : "system",
    ("LOCKED",                "DEPRECATED")           : "human",
    ("DEPRECATED",            "REINSTATED")           : "system",
    ("REINSTATED",            "DEPRECATED")           : "human",
    ("REJECTED",              "DRAFT")                : "human",
    # rollback can come from any state
    ("APPROVED",              "ROLLBACK")             : "human",
    ("LOCKED",                "ROLLBACK")             : "human",
    ("VALIDATED",             "ROLLBACK")             : "human",
    ("ROLLBACK",  "DRAFT")                : "system",   # auto re-enter pipeline
    ("ROLLBACK",  "CLARIFIED")            : "system",   # skip re-extraction if clean
}

# ── Hard block flags ──────────────────────────────────────────
# These flag types block HUMAN_REVIEW -> APPROVED transition
HARD_BLOCK_FLAGS = [
    "COMPLIANCE_HOLD",
    "LEGAL_CONFLICT",
    "NON_GOAL_CONFLICT",
]

# ── Soft flags ────────────────────────────────────────────────
# Must be acknowledged at HITL 2 but don't block transition
SOFT_FLAGS = [
    "BIAS_AUDIT",
    "ACCESSIBILITY_OMISSION",
    "PRODUCT_ETHICS",
    "SCOPE_EXPLOSION",
    "ASSUMPTION",
]

class StateMachine:
    """
    Enforces valid state transitions for requirements.
    Checks actor authority and blocking flags.
    """

    def __init__(self, session_manager):
        self.sm = session_manager

    # ── Check if transition is valid ──────────────────────────
    def can_transition(self, uid: str, to_state: str,
                       actor: str = "system") -> tuple[bool, str]:
        """
        Returns (True, "") if transition is allowed.
        Returns (False, reason) if not.
        """
        if uid not in self.sm.requirements:
            return False, f"Requirement {uid} not found"

        req        = self.sm.requirements[uid]
        from_state = req.get("status")

        # check transition exists
        key = (from_state, to_state)
        if key not in TRANSITIONS:
            return False, (
                f"No valid transition from {from_state} to {to_state}"
            )

        # check actor authority
        required_actor = TRANSITIONS[key]
        if required_actor == "human" and actor == "system":
            return False, (
                f"Transition {from_state} -> {to_state} "
                f"requires human action — system cannot perform it"
            )

        # check hard block flags on APPROVED transition
        if to_state == "APPROVED":
            blocking = [
                f for f in self.sm.flags.get(uid, [])
                if f["type"] in HARD_BLOCK_FLAGS
                and f["status"] == "OPEN"
            ]
            if blocking:
                flag_types = [f["type"] for f in blocking]
                return False, (
                    f"Cannot transition to APPROVED — "
                    f"hard block flags open: {flag_types}"
                )

        return True, ""

    # ── Perform transition ────────────────────────────────────
    def transition(self, uid: str, to_state: str,
                   actor: str = "system") -> tuple[bool, str]:
        """
        Performs the transition if valid.
        Returns (True, "") on success.
        Returns (False, reason) on failure.
        """
        allowed, reason = self.can_transition(uid, to_state, actor)
        if not allowed:
            return False, reason

        self.sm.transition_state(uid, to_state, actor)
        return True, ""

    # ── Bulk transition ───────────────────────────────────────
    def transition_many(self, uids: list, to_state: str,
                        actor: str = "system") -> dict:
        """
        Transitions multiple requirements.
        Returns dict of uid -> (success, reason)
        """
        results = {}
        for uid in uids:
            success, reason = self.transition(uid, to_state, actor)
            results[uid] = {"success": success, "reason": reason}
        return results

    # ── Get valid next states ─────────────────────────────────
    def valid_next_states(self, uid: str) -> list:
        """Returns list of states this requirement can move to."""
        if uid not in self.sm.requirements:
            return []

        current = self.sm.requirements[uid].get("status")
        return [
            to for (frm, to) in TRANSITIONS.keys()
            if frm == current
        ]

    # ── Validate entire session ───────────────────────────────
    def validate_session_states(self) -> dict:
        """
        Checks all requirements are in valid states.
        Returns a health report.
        """
        report = {
            "valid"   : [],
            "invalid" : [],
            "blocked" : []
        }

        for uid, req in self.sm.requirements.items():
            state = req.get("status")

            if state not in STATES:
                report["invalid"].append({
                    "uid"  : uid,
                    "state": state,
                    "issue": "Unknown state"
                })
            elif self.sm.has_blocking_flags(uid):
                report["blocked"].append({
                    "uid"  : uid,
                    "state": state,
                    "flags": [
                        f["type"] for f in self.sm.flags.get(uid, [])
                        if f["blocking"] and f["status"] == "OPEN"
                    ]
                })
            else:
                report["valid"].append(uid)

        return report
    
    def execute_rollback(self, uid: str, target_version: str,
                     actor: str = "human") -> tuple[bool, str]:
            """
            Roll back a requirement to a previous version.
            Restores the snapshot, marks current as DEPRECATED,
            creates new version, re-enters at CLARIFIED state.
            """
            if uid not in self.sm.requirements:
                return False, f"Requirement {uid} not found"

            req      = self.sm.requirements[uid]
            history  = req.get("version_history", [])

            # find target version in history
            target = next(
                (h for h in history if h.get("version") == target_version),
                None
            )
            if not target:
                return False, f"Version {target_version} not found in history"

            # mark current as deprecated
            self.sm.transition_state(uid, "DEPRECATED", actor,
                                    rationale=f"Rolled back to {target_version}")

            # restore snapshot as new version
            req["description"] = target.get("snapshot", req["description"])

            # re-enter at CLARIFIED
            ok, reason = self.transition(uid, "ROLLBACK", actor)
            if not ok:
                return False, reason

            # auto-advance to CLARIFIED for re-validation
            self.sm.transition_state(
                uid, "CLARIFIED", actor="system",
                rationale=f"Restored from {target_version} — awaiting re-validation"
            )

            return True, f"Rolled back to {target_version} — now in CLARIFIED state for re-validation"