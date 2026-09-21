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


if __name__ == "__main__":
    unittest.main()
