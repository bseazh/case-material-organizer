from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from case_naming import (  # noqa: E402
    case_folder_name,
    confirmed_cause,
    report_filename,
    timeline_filename,
    timeline_title,
)
from cause_catalog import DEFAULT_CATALOG, load_catalog  # noqa: E402


VALID_PLAN = {
    "case_folder": {
        "sequence": "1",
        "plaintiff_short_name": "张三",
        "defendant_short_name": "李四",
        "cause_of_action": "追索劳动报酬纠纷",
    },
    "cause_of_action_review": {
        "status": "confirmed",
        "primary_cause": "追索劳动报酬纠纷",
        "level": 4,
        "hierarchy": [
            "劳动争议、人事争议、新就业形态用工纠纷",
            "劳动争议",
            "劳动合同纠纷",
            "追索劳动报酬纠纷",
        ],
        "secondary_causes": [],
        "basis": "工资材料",
        "excluded_candidates": [],
        "confirmed_by_user": True,
    },
}


class CaseNamingTest(unittest.TestCase):
    def test_catalog_contains_specific_labor_causes(self) -> None:
        records = load_catalog(DEFAULT_CATALOG)
        children = [record for record in records if "劳动争议" in record["hierarchy"]]
        names = {record["name"] for record in children}
        self.assertIn("追索劳动报酬纠纷", names)
        self.assertIn("工伤保险待遇纠纷", names)

    def test_confirmed_cause_controls_all_names(self) -> None:
        self.assertEqual(confirmed_cause(VALID_PLAN), "追索劳动报酬纠纷")
        self.assertEqual(case_folder_name(VALID_PLAN), "1-张三VS李四-追索劳动报酬纠纷")
        self.assertEqual(report_filename(VALID_PLAN), "追索劳动报酬纠纷案件梳理报告.docx")
        self.assertEqual(timeline_filename(VALID_PLAN), "追索劳动报酬纠纷案件关键时间轴.html")
        self.assertEqual(timeline_title(VALID_PLAN), "追索劳动报酬纠纷｜案件关键时间轴")

    def test_unconfirmed_cause_is_rejected(self) -> None:
        plan = copy.deepcopy(VALID_PLAN)
        plan["cause_of_action_review"]["confirmed_by_user"] = False
        with self.assertRaisesRegex(ValueError, "尚未由用户确认"):
            confirmed_cause(plan)

    def test_invented_hierarchy_is_rejected(self) -> None:
        plan = copy.deepcopy(VALID_PLAN)
        plan["cause_of_action_review"]["hierarchy"][-1] = "工资争议"
        with self.assertRaisesRegex(ValueError, "与内置案由参考表不一致"):
            confirmed_cause(plan)

    def test_folder_cause_must_match_review(self) -> None:
        plan = copy.deepcopy(VALID_PLAN)
        plan["case_folder"]["cause_of_action"] = "劳动争议"
        with self.assertRaisesRegex(ValueError, "与已确认主要案由不一致"):
            confirmed_cause(plan)


if __name__ == "__main__":
    unittest.main()
