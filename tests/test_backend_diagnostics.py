from backend.services.diagnostics_service import DiagnosticsService
from backend.services.mapping_service import MappingService


def test_project_health_verification():
    service = DiagnosticsService(MappingService())

    summary = service.project_summary()

    assert summary["status"] == "healthy"
    assert summary["checks"]["mapping_data_loaded"] is True
    assert summary["checks"]["schema_valid"] is True
    assert summary["mapping_count"] >= 2


def test_service_diagnostics_verification():
    service = DiagnosticsService(MappingService())

    health = service.service_health_checks()

    assert health["retrieval_workflow"]["status"] == "ok"
    assert health["search_ranking"]["status"] == "ok"
    assert health["contradiction_detection"]["status"] == "ok"
    assert health["impact_analysis"]["status"] == "ok"
    assert health["chatbot_workflow"]["mode"] == "retrieval_grounded_stub"


def test_deterministic_consistency_verification():
    service = DiagnosticsService(MappingService())

    first = service.verify_configuration()
    second = service.verify_configuration()
    murder_results = service.mappings.search("IPC 302")

    assert first["ok"] is True
    assert first["data_fingerprint"] == second["data_fingerprint"]
    assert murder_results[0]["id"] == "1"
    assert murder_results[0]["score"] == service.mappings.search("IPC-302")[0]["score"]


def test_repeated_run_stability_verification():
    service = DiagnosticsService(MappingService())

    stability = service.verify_repeated_run_stability(runs=5)

    assert stability["ok"] is True
    assert stability["runs"] == 5
    assert stability["signature"] == service._result_signature(service.mappings.search(stability["query"]))


def test_search_helpers_handle_empty_queries_and_limits():
    service = MappingService()

    assert service.search("") == []
    assert service.search("IPC 302", limit=0) == []
    assert service.search("IPC 302", limit=-1) == []


def test_validation_flags_empty_critical_lists(tmp_path):
    data_path = tmp_path / "ipc_bns_mapping.json"
    data_path.write_text(
        """
        [
          {
            "id": "sample",
            "ipc_code": "IPC-1",
            "ipc_title": "Sample",
            "bns_code": "BNS-1",
            "bns_title": "Sample",
            "description": "Sample mapping.",
            "chapter": "Sample Chapter",
            "keywords": [],
            "ai_summary": "Sample summary.",
            "validation_rules": []
          }
        ]
        """,
        encoding="utf-8",
    )

    issues = MappingService(data_path).validate_records()

    assert issues == [
        {
            "index": 0,
            "id": "sample",
            "missing_fields": ["keywords", "validation_rules"],
        }
    ]


def test_configuration_flags_duplicate_section_codes(tmp_path):
    data_path = tmp_path / "ipc_bns_mapping.json"
    data_path.write_text(
        """
        [
          {
            "id": "1",
            "ipc_code": "IPC-302",
            "ipc_title": "Murder",
            "bns_code": "BNS-103",
            "bns_title": "Murder",
            "description": "First duplicate mapping.",
            "chapter": "Offences",
            "keywords": ["murder"],
            "ai_summary": "First mapping.",
            "validation_rules": ["Check intent"]
          },
          {
            "id": "2",
            "ipc_code": "IPC 302",
            "ipc_title": "Murder duplicate",
            "bns_code": "BNS 103",
            "bns_title": "Murder duplicate",
            "description": "Second duplicate mapping.",
            "chapter": "Offences",
            "keywords": ["murder"],
            "ai_summary": "Second mapping.",
            "validation_rules": ["Check intent"]
          }
        ]
        """,
        encoding="utf-8",
    )

    config = DiagnosticsService(MappingService(data_path)).verify_configuration()

    assert config["ok"] is False
    assert config["duplicate_ipc_codes"] == ["ipc302"]
    assert config["duplicate_bns_codes"] == ["bns103"]


def test_impact_analysis_ignores_invalid_validation_rule_scalars(tmp_path):
    data_path = tmp_path / "ipc_bns_mapping.json"
    data_path.write_text(
        """
        [
          {
            "id": "sample",
            "ipc_code": "IPC-1",
            "ipc_title": "Sample",
            "bns_code": "BNS-1",
            "bns_title": "Sample",
            "description": "Sample mapping.",
            "chapter": "Sample Chapter",
            "keywords": ["sample"],
            "ai_summary": "Sample summary.",
            "validation_rules": "not-a-list"
          }
        ]
        """,
        encoding="utf-8",
    )

    service = MappingService(data_path)

    assert service.analyze_impact()["validation_rules"] == []
    assert service.validate_records()[0]["invalid_field"] == "validation_rules"


def test_service_health_reports_deterministic_ranking_and_chatbot_grounding():
    health = DiagnosticsService(MappingService()).service_health_checks()

    assert health["search_ranking"]["deterministic"] is True
    assert health["chatbot_workflow"]["grounding_source"] == "mapping_search_top_result"


def test_repeated_run_stability_normalizes_non_positive_runs():
    stability = DiagnosticsService(MappingService()).verify_repeated_run_stability(runs=0)

    assert stability["ok"] is True
    assert stability["runs"] == 1
    assert stability["signature"]
