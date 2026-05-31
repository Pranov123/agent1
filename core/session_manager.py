import json
import uuid
from datetime import datetime
from pathlib import Path
import config

class SessionManager:
    """
    Manages the lifecycle of a single Agent 1 pipeline run.
    Tracks all requirements, their states, versions, flags,
    and produces the final session record.
    """

    def __init__(self):
        self.session_id  = self._generate_session_id()
        self.created_at  = datetime.now().isoformat()
        self.raw_input   = ""
        self.requirements = {}   # uid -> requirement dict
        self.non_goals    = {}   # uid -> non-goal dict
        self.flags        = {}   # uid -> list of flags
        self.hitl1_log    = []   # list of rounds
        self.hitl2_log    = []   # list of reviewer actions
        self.ethos_output = {}   # risk tier, confidence, etc
        self.stage_outputs = {}  # stage name -> raw output
        self.version_counters = {}  # uid -> current version int
        self.status = "ACTIVE"

    # ── Session ID ────────────────────────────────────────────
    def _generate_session_id(self) -> str:
        date  = datetime.now().strftime("%Y%m%d")
        short = str(uuid.uuid4())[:6].upper()
        return f"SES-{date}-{short}"

    # ── Requirement UID generator ─────────────────────────────
    def generate_req_uid(self) -> str:
        date  = datetime.now().strftime("%Y%m%d")
        count = len(self.requirements) + 1
        return f"REQ-{date}-{count:03d}"

    # ── Non-goal UID generator ────────────────────────────────
    def generate_ng_uid(self) -> str:
        date  = datetime.now().strftime("%Y%m%d")
        count = len(self.non_goals) + 1
        return f"NG-{date}-{count:03d}"

    # ── Add requirement ───────────────────────────────────────
    def add_requirement(self, req: dict) -> str:
        """Add a new requirement. Assigns UID if not present."""
        if "uid" not in req or not req["uid"]:
            req["uid"] = self.generate_req_uid()

        uid = req["uid"]

        # initialise version tracking
        if uid not in self.version_counters:
            self.version_counters[uid] = 1

        req["version"]         = f"V{self.version_counters[uid]}"
        req["created_at"]      = datetime.now().isoformat()
        req["updated_at"]      = datetime.now().isoformat()
        req["version_history"] = []
        req["session_id"]      = self.session_id

        self.requirements[uid] = req
        self.flags[uid]        = []
        return uid

    # ── Update requirement state ──────────────────────────────
    def transition_state(self, uid: str, new_state: str, actor: str = "system") -> bool:
        """
        Transition a requirement to a new state.
        Logs the transition. Returns False if uid not found.
        """
        if uid not in self.requirements:
            return False

        req       = self.requirements[uid]
        old_state = req.get("status", "UNKNOWN")

        # archive current version before changing
        req["version_history"].append({
            "version"    : req.get("version"),
            "status"     : old_state,
            "snapshot"   : req.get("description"),
            "changed_at" : datetime.now().isoformat(),
            "changed_by" : actor
        })

        req["status"]     = new_state
        req["updated_at"] = datetime.now().isoformat()
        return True

    # ── Bulk state transition ─────────────────────────────────
    def transition_all(self, uids: list, new_state: str, actor: str = "system"):
        for uid in uids:
            self.transition_state(uid, new_state, actor)

    # ── Add flag ──────────────────────────────────────────────
    def add_flag(self, uid: str, flag_type: str, description: str,
                 blocking: bool = False, source: str = "system"):
        """
        Attach a flag to a requirement.
        blocking=True means it hard-blocks the APPROVED transition.
        """
        if uid not in self.flags:
            self.flags[uid] = []

        self.flags[uid].append({
            "type"        : flag_type,
            "description" : description,
            "blocking"    : blocking,
            "status"      : "OPEN",
            "source"      : source,
            "created_at"  : datetime.now().isoformat(),
            "resolved_at" : None,
            "resolved_by" : None
        })

    # ── Check blocking flags ──────────────────────────────────
    def has_blocking_flags(self, uid: str) -> bool:
        return any(
            f["blocking"] and f["status"] == "OPEN"
            for f in self.flags.get(uid, [])
        )

    # ── Add non-goal ──────────────────────────────────────────
    def add_non_goal(self, ng: dict) -> str:
        if "uid" not in ng or not ng["uid"]:
            ng["uid"] = self.generate_ng_uid()
        uid          = ng["uid"]
        ng["status"] = "ACTIVE"
        ng["created_at"] = datetime.now().isoformat()
        self.non_goals[uid] = ng
        return uid

    # ── Store stage output ────────────────────────────────────
    def store_stage_output(self, stage: str, output: dict):
        self.stage_outputs[stage] = {
            "output"     : output,
            "stored_at"  : datetime.now().isoformat()
        }

    # ── Store ETHOS output ────────────────────────────────────
    def store_ethos(self, ethos: dict):
        self.ethos_output = ethos

    # ── Log HITL 1 round ─────────────────────────────────────
    def log_hitl1_round(self, round_num: int, questions: list,
                        answers: dict, resolutions: list):
        self.hitl1_log.append({
            "round"       : round_num,
            "questions"   : questions,
            "answers"     : answers,
            "resolutions" : resolutions,
            "timestamp"   : datetime.now().isoformat()
        })

    # ── Log HITL 2 action ─────────────────────────────────────
    def log_hitl2_action(self, reviewer_id: str, action: str,
                         affected_uids: list, notes: str = ""):
        self.hitl2_log.append({
            "reviewer_id"  : reviewer_id,
            "action"       : action,
            "affected_uids": affected_uids,
            "notes"        : notes,
            "timestamp"    : datetime.now().isoformat()
        })

    # ── Get requirements by state ─────────────────────────────
    def get_by_state(self, state: str) -> list:
        return [
            r for r in self.requirements.values()
            if r.get("status") == state
        ]

    # ── Get requirements by bucket ────────────────────────────
    def get_by_bucket(self, bucket: str) -> list:
        return [
            r for r in self.requirements.values()
            if r.get("scope_bucket") == bucket
        ]

    # ── Session summary ───────────────────────────────────────
    def summary(self) -> dict:
        states = {}
        for r in self.requirements.values():
            s = r.get("status", "UNKNOWN")
            states[s] = states.get(s, 0) + 1

        return {
            "session_id"       : self.session_id,
            "status"           : self.status,
            "created_at"       : self.created_at,
            "total_requirements": len(self.requirements),
            "total_non_goals"  : len(self.non_goals),
            "states"           : states,
            "hitl1_rounds"     : len(self.hitl1_log),
            "hitl2_actions"    : len(self.hitl2_log),
            "ethos_risk_tier"  : self.ethos_output.get("risk_tier", "unknown"),
            "flags_open"       : sum(
                1 for flags in self.flags.values()
                for f in flags if f["status"] == "OPEN"
            )
        }

    # ── Save session to disk ──────────────────────────────────
    def save(self):
        Path(config.OUTPUT_DIR).mkdir(exist_ok=True)
        path = Path(config.OUTPUT_DIR) / f"{self.session_id}.json"

        payload = {
            "session_id"    : self.session_id,
            "created_at"    : self.created_at,
            "status"        : self.status,
            "raw_input"     : self.raw_input,
            "requirements"  : self.requirements,
            "non_goals"     : self.non_goals,
            "flags"         : self.flags,
            "ethos_output"  : self.ethos_output,
            "hitl1_log"     : self.hitl1_log,
            "hitl2_log"     : self.hitl2_log,
            "stage_outputs" : self.stage_outputs,
        }

        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

        return str(path)

    # ── Load session from disk ────────────────────────────────
    @classmethod
    def load(cls, session_id: str) -> "SessionManager":
        path = Path(config.OUTPUT_DIR) / f"{session_id}.json"
        with open(path) as f:
            data = json.load(f)

        sm = cls()
        sm.session_id      = data["session_id"]
        sm.created_at      = data["created_at"]
        sm.status          = data["status"]
        sm.raw_input       = data["raw_input"]
        sm.requirements    = data["requirements"]
        sm.non_goals       = data["non_goals"]
        sm.flags           = data["flags"]
        sm.ethos_output    = data["ethos_output"]
        sm.hitl1_log       = data["hitl1_log"]
        sm.hitl2_log       = data["hitl2_log"]
        sm.stage_outputs   = data["stage_outputs"]
        return sm