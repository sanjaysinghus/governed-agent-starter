"""Planner interface. A planner looks at the goal and the history and returns the next Step.

ScriptedPlanner lets the whole loop run with no API key, which is what the tests and the example use.
To use a real model, write a class with the same next_step() method that calls your provider
(for example Amazon Bedrock, Azure OpenAI or a local model) and parses its tool-call output into a Step."""
from .agent import Step


class ScriptedPlanner:
    def __init__(self, steps):
        self._steps = list(steps)

    def next_step(self, goal, history):
        if not self._steps:
            return Step(tool=None, args={}, final="No further steps.")
        nxt = self._steps.pop(0)
        return nxt(history) if callable(nxt) else nxt
