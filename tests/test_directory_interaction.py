from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SORTING = ROOT / "skills" / "lawyerbuddy-sorting"


class DirectoryInteractionTest(unittest.TestCase):
    def test_interaction_expands_default_tree(self) -> None:
        text = (SORTING / "references" / "interaction.md").read_text(encoding="utf-8")
        for folder in (
            "001 主体信息/",
            "002 基础资料/",
            "003 委托材料/",
            "004 类案及法律检索/",
            "005 法律文书/",
        ):
            self.assertIn(folder, text)
        self.assertIn("不得用“001—005”", text)

    def test_interaction_provides_custom_fill_in_template(self) -> None:
        text = (SORTING / "references" / "interaction.md").read_text(encoding="utf-8")
        self.assertIn("B. 自定义一级、二级目录", text)
        self.assertIn("一级目录1：", text)
        self.assertIn("- 二级目录：", text)
        self.assertIn("也可以只填写一级目录", text)
        self.assertIn("必须再次展示并确认", text)

    def test_readme_shows_the_same_lawyer_facing_choices(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("A. 使用默认目录", text)
        self.assertIn("001 主体信息/", text)
        self.assertIn("005 法律文书/", text)
        self.assertIn("B. 自定义一级、二级目录", text)

    def test_completed_archive_exposes_the_real_absolute_path(self) -> None:
        interaction = (SORTING / "references" / "interaction.md").read_text(encoding="utf-8")
        build_tree = (SORTING / "scripts" / "build_tree.py").read_text(encoding="utf-8")
        self.assertIn("绝对路径属于必交付信息", interaction)
        self.assertIn("实际 `result_folder`", interaction)
        self.assertIn("确认该目录真实存在", interaction)
        self.assertIn("不得只显示 Word 报告、时间轴", interaction)
        self.assertIn("A. 打开整理好的案件文件夹", interaction)
        self.assertIn("A. 打开整理好的案件文件夹", build_tree)

    def test_completed_sorting_recommends_summary_then_timeline(self) -> None:
        interaction = (SORTING / "references" / "interaction.md").read_text(encoding="utf-8")
        router = (ROOT / "skills" / "lawyerbuddy" / "SKILL.md").read_text(encoding="utf-8")
        report_skill = (ROOT / "skills" / "lawyerbuddy-summarizing" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("lawyerbuddy-summarizing` → `lawyerbuddy-timeline", interaction)
        self.assertIn("A. 生成快速初稿（推荐）", interaction)
        self.assertIn("B. 补充核对金额与付款情况", interaction)
        self.assertIn("lawyerbuddy-summarizing` → `lawyerbuddy-timeline", router)
        self.assertIn("recommended_next_skill", router)
        self.assertIn("lawyerbuddy-timeline` 生成时间轴（推荐）", report_skill)


if __name__ == "__main__":
    unittest.main()
