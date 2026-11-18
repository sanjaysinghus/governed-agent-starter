"""Tools are plain functions with a declared risk level. The agent can only call what is registered."""
from dataclasses import dataclass
from typing import Callable

READ, DRAFT, ACT = "read", "draft", "act"   # ACT = changes something outside the agent


@dataclass
class Tool:
    name: str
    risk: str
    fn: Callable
    description: str = ""


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, risk, description=""):
        def wrap(fn):
            self._tools[name] = Tool(name, risk, fn, description)
            return fn
        return wrap

    def get(self, name):
        return self._tools.get(name)

    def names(self):
        return sorted(self._tools)
