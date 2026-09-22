from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SuiteStructureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "manifests" / "skills.json").read_text(encoding="utf-8")
        )

    def test_all_manifest_skills_have_matching_frontmatter(self) -> None:
        self.assertEqual(len(self.manifest["skills"]), 7)
        for skill in self.manifest["skills"]:
            skill_file = ROOT / "skills" / skill["name"] / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill["name"])
            text = skill_file.read_text(encoding="utf-8")
            self.assertIn(f"name: {skill['name']}", text)

    def test_ready_product_skills_are_declared(self) -> None:
        statuses = {skill["name"]: skill["status"] for skill in self.manifest["skills"]}
        self.assertEqual(statuses["lawyerbuddy"], "ready")
        self.assertEqual(statuses["lawyerbuddy-sorting"], "ready")
        self.assertEqual(statuses["lawyerbuddy-summarizing"], "ready")
        self.assertEqual(statuses["lawyerbuddy-timeline"], "ready")
        self.assertEqual(statuses["lawyerbuddy-similar-case-retrieval"], "ready")
        self.assertEqual(statuses["lawyerbuddy-document-drafting"], "ready")
        self.assertEqual(statuses["lawyerbuddy-contract-review"], "ready")

    def test_sorting_keeps_existing_runtime(self) -> None:
        sorting = ROOT / "skills" / "lawyerbuddy-sorting"
        required = [
            sorting / "assets" / "民事案件案由参考表_2025.xlsx",
            sorting / "scripts" / "build_plan.py",
            sorting / "scripts" / "build_report.py",
            sorting / "scripts" / "build_timeline.py",
            sorting / "references" / "interaction.md",
            sorting / "references" / "completeness.md",
            sorting / "scripts" / "completeness.py",
            sorting / "requirements.txt",
        ]
        for path in required:
            self.assertTrue(path.is_file(), str(path))

    def test_shared_contract_is_valid_json_schema_document(self) -> None:
        schema = json.loads(
            (ROOT / "runtime" / "contracts" / "case-data.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["type"], "object")
        self.assertIn("events", schema["required"])
        self.assertIn("reading_coverage", schema["required"])
        self.assertIn("fact_inventory", schema["required"])
        self.assertIn("fact_disposition", schema["required"])
        self.assertIn("legal_fact_map", schema["required"])

    def test_internal_capability_library_and_routes_are_complete(self) -> None:
        routing = ROOT / "runtime" / "routing"
        index = json.loads((routing / "capability-index.json").read_text(encoding="utf-8"))
        aliases = json.loads((routing / "aliases.json").read_text(encoding="utf-8"))
        pipelines = json.loads((routing / "pipelines.json").read_text(encoding="utf-8"))
        capability_ids = {capability["id"] for capability in index["capabilities"]}
        self.assertEqual(len(capability_ids), 38)
        base = ROOT / "runtime" / "capabilities" / "legal-skills-chinese" / "skills"
        self.assertEqual({path.name for path in base.iterdir() if path.is_dir()}, capability_ids)
        for capability_id in capability_ids:
            self.assertTrue((base / capability_id / "SKILL.md").is_file())
        self.assertTrue(set(aliases.values()).issubset(capability_ids))
        referenced = set()
        for product in pipelines["products"].values():
            if product.get("primary"):
                referenced.add(product["primary"])
            referenced.update(product.get("optional", []))
            for stage in product.get("stages", []):
                self.assertLessEqual(len(stage), pipelines["rules"]["max_loaded_capabilities_per_stage"])
                referenced.update(stage)
        self.assertTrue(referenced.issubset(capability_ids))


if __name__ == "__main__":
    unittest.main()
