import json, sys, pathlib, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from governed_agent import AuditLog, Policy, ToolRegistry, GovernedAgent, Step, ScriptedPlanner
from governed_agent.tools import READ, ACT


def build(steps, approve=True, **policy_kw):
    tools, calls = ToolRegistry(), []
    tools.register("read", READ)(lambda q: {"ok": q})
    tools.register("send", ACT)(lambda msg: calls.append(msg) or {"sent": True})
    tools.register("hidden", ACT)(lambda: calls.append("hidden") or {})
    audit = AuditLog(pathlib.Path(tempfile.mkdtemp()) / "log.jsonl")
    policy = Policy(allowed_tools={"read", "send"}, **policy_kw)
    agent = GovernedAgent(ScriptedPlanner(steps), tools, policy, audit, lambda t, a: (approve, "tester"))
    return agent, audit, calls


class GovernedAgentTests(unittest.TestCase):
    def test_read_runs_without_approval(self):
        agent, audit, _ = build([Step("read", {"q": "x"}), Step(None, final="done")])
        result, history = agent.run("g")
        self.assertEqual(result, "done")
        self.assertEqual(history[0]["status"], "done")
        self.assertNotIn("human_review", audit.path.read_text())

    def test_action_needs_approval_and_is_blocked_when_rejected(self):
        agent, audit, calls = build([Step("send", {"msg": "hi"}), Step(None, final="done")], approve=False)
        _, history = agent.run("g")
        self.assertEqual(history[0]["status"], "rejected")
        self.assertEqual(calls, [])
        self.assertIn("human_review", audit.path.read_text())

    def test_tool_off_allow_list_is_denied(self):
        agent, _, calls = build([Step("hidden", {}), Step("nope", {}), Step(None, final="done")])
        _, history = agent.run("g")
        self.assertEqual([h["status"] for h in history], ["denied", "denied"])
        self.assertEqual(calls, [])

    def test_blocked_terms_stop_data_leaving(self):
        agent, _, calls = build([Step("send", {"msg": "health card 1234"}), Step(None, final="done")],
                                blocked_terms=("health card",))
        _, history = agent.run("g")
        self.assertEqual(history[0]["status"], "denied")
        self.assertEqual(calls, [])

    def test_step_limit_stops_runaway_loop(self):
        agent, _, _ = build([Step("read", {"q": i}) for i in range(50)], max_steps=3)
        result, history = agent.run("g")
        self.assertTrue(result.startswith("Stopped"))
        self.assertEqual(sum(h["status"] == "done" for h in history), 3)

    def test_audit_chain_detects_tampering(self):
        agent, audit, _ = build([Step("read", {"q": "x"}), Step(None, final="done")])
        agent.run("g")
        self.assertTrue(audit.verify())
        lines = audit.path.read_text().splitlines()
        entry = json.loads(lines[1]); entry["data"]["outcome"] = "allow-edited"
        lines[1] = json.dumps(entry, sort_keys=True)
        audit.path.write_text("\n".join(lines) + "\n")
        self.assertFalse(audit.verify())


if __name__ == "__main__":
    unittest.main()
