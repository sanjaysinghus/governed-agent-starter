"""Append-only, hash-chained audit log. Each entry carries the hash of the one before it,
so any later edit or deletion breaks the chain and is detectable with verify()."""
import hashlib, json, time
from pathlib import Path


class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last = self._tail_hash()

    def _tail_hash(self):
        if not self.path.exists():
            return "0" * 64
        lines = self.path.read_text().strip().splitlines()
        return json.loads(lines[-1])["hash"] if lines else "0" * 64

    def record(self, event, **data):
        entry = {"ts": time.time(), "event": event, "data": data, "prev": self._last}
        entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        with self.path.open("a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        self._last = entry["hash"]
        return entry

    def verify(self):
        prev = "0" * 64
        for line in self.path.read_text().strip().splitlines():
            entry = json.loads(line)
            claimed = entry.pop("hash")
            if entry["prev"] != prev:
                return False
            if hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest() != claimed:
                return False
            prev = claimed
        return True
