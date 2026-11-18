"""Example: after a visit, draft a referral letter and book a follow-up.
All data is synthetic. Nothing here is a real patient, clinic or system.

Run:  python examples/referral_followup.py            (auto-approves, for a quick demo)
      python examples/referral_followup.py --ask      (asks you to approve each action)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from governed_agent import AuditLog, Policy, ToolRegistry, GovernedAgent, Step, ScriptedPlanner
from governed_agent.tools import READ, DRAFT, ACT

VISIT = {"visit_id": "V-1001", "patient_ref": "SYNTH-0042",
         "summary": "Persistent knee pain for 8 weeks, no injury. X-ray normal. Physio advised.",
         "plan": "Refer to orthopaedics. Review in 6 weeks."}
OUTBOX, CALENDAR = [], []
tools = ToolRegistry()


@tools.register("get_visit_summary", READ, "Read the signed visit summary")
def get_visit_summary(visit_id):
    return VISIT if visit_id == VISIT["visit_id"] else {"error": "not found"}


@tools.register("draft_referral", DRAFT, "Draft a referral letter; does not send it")
def draft_referral(patient_ref, specialty, reason):
    return {"draft": f"Referral to {specialty} for patient {patient_ref}. Reason: {reason}"}


@tools.register("send_referral", ACT, "Send the referral to the receiving clinic")
def send_referral(draft):
    OUTBOX.append(draft)
    return {"sent": True, "outbox_size": len(OUTBOX)}


@tools.register("book_followup", ACT, "Book a follow-up appointment")
def book_followup(patient_ref, weeks):
    CALENDAR.append((patient_ref, weeks))
    return {"booked": True, "in_weeks": weeks}


@tools.register("export_records", ACT, "Bulk export of records")
def export_records(destination):
    return {"exported": True}


def last_result(history, tool):
    return next(h["result"] for h in reversed(history) if h["tool"] == tool and h["status"] == "done")


planner = ScriptedPlanner([
    Step("get_visit_summary", {"visit_id": "V-1001"}),
    lambda h: Step("draft_referral", {"patient_ref": last_result(h, "get_visit_summary")["patient_ref"],
                                      "specialty": "orthopaedics",
                                      "reason": last_result(h, "get_visit_summary")["summary"]}),
    Step("export_records", {"destination": "external-share"}),          # not on the allow-list: denied
    lambda h: Step("send_referral", {"draft": last_result(h, "draft_referral")["draft"]}),
    Step("book_followup", {"patient_ref": "SYNTH-0042", "weeks": 6}),
    Step(None, final="Referral sent and follow-up booked, both signed off by the clinician."),
])

policy = Policy(allowed_tools={"get_visit_summary", "draft_referral", "send_referral", "book_followup"})


def approver(tool, args):
    if "--ask" in sys.argv:
        print(f"\nAPPROVAL NEEDED: {tool}\n  {args}")
        return input("Approve? [y/N] ").strip().lower() == "y", "clinician (console)"
    return True, "clinician (auto-approved demo)"


if __name__ == "__main__":
    log_path = pathlib.Path(__file__).parent / "audit_log.jsonl"
    log_path.unlink(missing_ok=True)
    audit = AuditLog(log_path)
    result, history = GovernedAgent(planner, tools, policy, audit, approver).run(
        "Complete the post-visit actions for visit V-1001")
    print("\nRESULT:", result)
    for h in history:
        print(f"  {h['tool']:<20} {h['status']}" + (f"  ({h['reason']})" if "reason" in h else ""))
    print(f"\nAudit log: {log_path}  chain intact: {audit.verify()}")
