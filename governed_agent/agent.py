"""The governed loop: plan -> policy check -> (human sign-off) -> act -> record -> repeat."""
from dataclasses import dataclass, field
from .policy import ALLOW, NEEDS_APPROVAL, DENY


@dataclass
class Step:
    tool: str | None
    args: dict = field(default_factory=dict)
    final: str | None = None      # set when the planner is done


class GovernedAgent:
    def __init__(self, planner, tools, policy, audit, approver):
        """approver(tool_name, args) -> (approved: bool, reviewer: str). It is always a person."""
        self.planner, self.tools, self.policy, self.audit, self.approver = planner, tools, policy, audit, approver

    def run(self, goal):
        history, step_no = [], 0
        self.audit.record("run_started", goal=goal)
        while True:
            step_no += 1
            step = self.planner.next_step(goal, history)
            if step.final is not None:
                self.audit.record("run_finished", result=step.final, steps=step_no - 1)
                return step.final, history
            tool = self.tools.get(step.tool)
            decision = self.policy.check(tool, step.args, step_no)
            self.audit.record("policy_decision", tool=step.tool, args=step.args,
                              outcome=decision.outcome, reason=decision.reason)
            if decision.outcome == DENY:
                history.append({"tool": step.tool, "status": "denied", "reason": decision.reason})
                if "step limit" in decision.reason:
                    self.audit.record("run_stopped", reason=decision.reason)
                    return f"Stopped: {decision.reason}", history
                continue
            if decision.outcome == NEEDS_APPROVAL:
                approved, reviewer = self.approver(step.tool, step.args)
                self.audit.record("human_review", tool=step.tool, approved=approved, reviewer=reviewer)
                if not approved:
                    history.append({"tool": step.tool, "status": "rejected", "reviewer": reviewer})
                    continue
            result = tool.fn(**step.args)
            self.audit.record("tool_called", tool=step.tool, result=result)
            history.append({"tool": step.tool, "status": "done", "result": result})
