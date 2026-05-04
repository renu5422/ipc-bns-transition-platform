import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "ipc_bns_mapping.json"

class MappingService:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> list:
        if DATA_PATH.exists():
            with open(DATA_PATH, encoding="utf-8") as f:
                return json.load(f)
        return []

    def search(self, query: str) -> list:
        q = query.lower()
        return [
            s for s in self._data
            if q in s.get("ipc_code", "").lower()
            or q in s.get("bns_code", "").lower()
            or q in s.get("title", "").lower()
        ]

mapping_service = MappingService()
