"""Policy decides, before every tool call, whether to allow it, send it to a human, or block it.
Rules are data, not prompt text, so they can be reviewed by risk and compliance teams."""
from dataclasses import dataclass, field
from .tools import READ, DRAFT, ACT

ALLOW, NEEDS_APPROVAL, DENY = "allow", "needs_approval", "deny"


@dataclass
class Decision:
    outcome: str
    reason: str


@dataclass
class Policy:
    allowed_tools: set = field(default_factory=set)        # allow-list; anything else is denied
    approval_for: set = field(default_factory=lambda: {ACT})  # risk levels that need a human
    max_steps: int = 8                                     # hard stop on runaway loops
    blocked_terms: tuple = ()                              # e.g. identifiers that must not leave

    def check(self, tool, args, step_no):
        if step_no > self.max_steps:
            return Decision(DENY, f"step limit of {self.max_steps} reached")
        if tool is None:
            return Decision(DENY, "tool is not registered")
        if tool.name not in self.allowed_tools:
            return Decision(DENY, f"tool '{tool.name}' is not on the allow-list")
        text = " ".join(str(v) for v in args.values()).lower()
        for term in self.blocked_terms:
            if term.lower() in text:
                return Decision(DENY, f"arguments contain blocked term '{term}'")
        if tool.risk in self.approval_for:
            return Decision(NEEDS_APPROVAL, f"'{tool.risk}' actions need human sign-off")
        return Decision(ALLOW, "within policy")
