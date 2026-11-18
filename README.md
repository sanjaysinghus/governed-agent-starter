# governed-agent-starter

A minimal, readable reference for running an AI agent in a regulated setting. About 200 lines of Python, no dependencies, runs without an API key.

It is the companion code to *The Pilot to P&L Brief, Industry Series No. 01: Healthcare*.

## What it shows

Most agent demos show what an agent can do. This one shows what stops it. Four controls sit around a plain plan-and-act loop:

| Control | File | What it does |
|---|---|---|
| Allow-list | `governed_agent/policy.py` | The agent can call only the tools you list. Anything else is denied. |
| Human sign-off | `governed_agent/agent.py` | Any tool marked `act` (it changes something outside the agent) waits for a named person to approve. |
| Hard limits | `governed_agent/policy.py` | A step limit stops runaway loops; blocked terms stop chosen identifiers leaving in tool arguments. |
| Audit trail | `governed_agent/audit.py` | Every decision, approval and tool call is written to an append-only log. Entries are hash-chained, so later edits are detectable. |

Policy is data, not prompt text. A risk or compliance reviewer can read `Policy(...)` without reading a prompt.

## Run it

```bash
python examples/referral_followup.py          # quick demo, auto-approves
python examples/referral_followup.py --ask    # you approve each action
python tests/test_governed_agent.py           # 6 tests
```

The example drafts a referral letter and books a follow-up after a clinic visit. All data is synthetic. Along the way the planner tries a bulk export that is not on the allow-list, and the policy denies it.

## Use a real model

`ScriptedPlanner` replays fixed steps so the loop runs anywhere. To use a model, write a class with one method, `next_step(goal, history) -> Step`, that calls your provider and turns its tool-call output into a `Step`. Nothing else changes: the policy, sign-off and audit log treat a model's plan exactly like a scripted one.

## What this is not

- Not a medical device and not clinical software. Do not use it with real patient data.
- Not a framework. For production you will also need identity and access control, secrets handling, monitoring, evaluation, and a privacy and security review for your jurisdiction.
- The blocked-terms check is a simple string match. It is a placeholder for a real data-loss-prevention control.

## Licence

MIT. See `LICENSE`.
