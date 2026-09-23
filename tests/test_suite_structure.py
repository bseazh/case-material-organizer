from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SuiteStructureTest(unittest.TestCase):
    def test_workbuddy_root_skill_has_yaml_frontmatter(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        self.assertIn("\nname: lawyerbuddy\n", skill)
        self.assertIn("\ndescription: ", skill)
        self.assertIn("skills/lawyerbuddy-sorting/SKILL.md", skill)

    def test_workbuddy_pack_script_and_package_include_root_skill(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["scripts"]["pack:workbuddy"], "node ./bin/build-workbuddy-package.js")
        self.assertIn("SKILL.md", package["files"])
        self.assertTrue((ROOT / "bin" / "build-workbuddy-package.js").is_file())

    def test_skillhub_package_passes_upload_limits(self) -> None:
        import subprocess

        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        result = subprocess.run(
            ["node", str(ROOT / "bin" / "build-skillhub-package.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(result.stdout)
        self.assertLessEqual(report["files"], 200)
        self.assertEqual(report["root_skill"], "SKILL.md")
        self.assertEqual(report["unsupported_files"], 0)
        self.assertIn("pack:skillhub", package["scripts"])

    def test_user_guide_covers_document_drafting_and_is_linked(self) -> None:
        guide = (ROOT / "docs" / "使用指南.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## 文书起草", guide)
        self.assertIn("民事起诉状", guide)
        self.assertIn("待确认", guide)
        self.assertIn("docs/使用指南.md", readme)

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

    def test_installation_uses_domestic_mirrors_for_optional_components(self) -> None:
        cli = (ROOT / "bin" / "cli.js").read_text(encoding="utf-8")
        install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        for text in (cli, install):
            self.assertIn("pypi.tuna.tsinghua.edu.cn/simple", text)
            self.assertIn("pypi.mirrors.ustc.edu.cn/simple", text)
            self.assertIn("HOMEBREW_NO_AUTO_UPDATE=1", text)
            self.assertIn("mirrors.ustc.edu.cn/homebrew-bottles", text)
            self.assertIn("brew install poppler", text)
            self.assertIn("brew install poppler tesseract tesseract-lang", text)
        self.assertIn(
            "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r",
            cli,
        )
        self.assertIn(
            "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r",
            install,
        )
        self.assertIn("OCR/PDF 是按需能力", cli)
        self.assertIn("首次安装不要安装 Poppler、Tesseract 或浏览器", install)


if __name__ == "__main__":
    unittest.main()
