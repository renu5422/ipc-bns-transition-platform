import hashlib
import json
from typing import Any

from backend.services.mapping_service import MappingService


class DiagnosticsService:
    def __init__(self, mapping_service: MappingService) -> None:
        self.mappings = mapping_service

    def project_summary(self) -> dict[str, Any]:
        loaded = len(self.mappings._records) > 0
        schema_valid = self.mappings.validate_schema() if loaded else False
        return {
            "status": "healthy" if loaded and schema_valid else "degraded",
            "checks": {
                "mapping_data_loaded": loaded,
                "schema_valid": schema_valid,
            },
            "mapping_count": len(self.mappings._records),
        }

    def service_health_checks(self) -> dict[str, Any]:
        try:
            self.mappings.search("IPC 302", limit=1)
            retrieval_ok = True
        except Exception:
            retrieval_ok = False

        try:
            r1 = self.mappings.search("murder", limit=5)
            r2 = self.mappings.search("murder", limit=5)
            ranking_det = [x["id"] for x in r1] == [x["id"] for x in r2]
        except Exception:
            ranking_det = False

        try:
            self.mappings.detect_contradictions()
            contradiction_ok = True
        except Exception:
            contradiction_ok = False

        try:
            self.mappings.analyze_impact()
            impact_ok = True
        except Exception:
            impact_ok = False

        top = self.mappings.search("IPC 302", limit=1)
        grounding_source = "mapping_search_top_result" if top else "none"

        return {
            "retrieval_workflow": {"status": "ok" if retrieval_ok else "error"},
            "search_ranking": {"status": "ok" if ranking_det else "error", "deterministic": ranking_det},
            "contradiction_detection": {"status": "ok" if contradiction_ok else "error"},
            "impact_analysis": {"status": "ok" if impact_ok else "error"},
            "chatbot_workflow": {
                "mode": "retrieval_grounded_stub",
                "grounding_source": grounding_source,
            },
        }

    def verify_configuration(self) -> dict[str, Any]:
        contradictions = self.mappings.detect_contradictions()
        dup_ipc = [c["code"] for c in contradictions if c["type"] == "duplicate_ipc"]
        dup_bns = [c["code"] for c in contradictions if c["type"] == "duplicate_bns"]
        return {
            "ok": len(contradictions) == 0,
            "data_fingerprint": self._data_fingerprint(),
            "duplicate_ipc_codes": dup_ipc,
            "duplicate_bns_codes": dup_bns,
        }

    def _data_fingerprint(self) -> str:
        serialized = json.dumps(self.mappings._records, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def verify_repeated_run_stability(self, runs: int = 5) -> dict[str, Any]:
        runs = max(1, runs)
        query = "IPC 302"
        signatures = [self._result_signature(self.mappings.search(query)) for _ in range(runs)]
        stable = len(set(signatures)) == 1
        return {
            "ok": stable,
            "runs": runs,
            "signature": signatures[0] if signatures else "",
            "query": query,
        }

    def _result_signature(self, results: list[dict]) -> str:
        serialized = json.dumps(
            [{"id": r["id"], "score": r["score"]} for r in results], sort_keys=True
        )
        return hashlib.md5(serialized.encode()).hexdigest()


diagnostics_service = DiagnosticsService(MappingService())
