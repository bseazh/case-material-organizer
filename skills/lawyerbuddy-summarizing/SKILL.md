---
name: lawyerbuddy-summarizing
description: LawyerBuddy 案件总结入口。用户已有经过确认并执行的案件归档方案，需要单独生成或更新包含案件主体、案件总结、关键时间轴表格和文件清单的 Word 案件梳理报告时使用。
---

# 案件总结

本 Skill 复用 `lawyerbuddy-sorting` 的报告规则和脚本。不得无条件信任既有摘要或执行 JSON；生成或更新报告前必须重新核验完整阅读记录、事实台账、事实去向和法律事实映射。核验是检查来源覆盖和遗漏，不得擅自改写材料事实。

## 执行要求

1. 定位用户指定案件下的 `整理结果/技术资料/归档方案_已执行.json`。
2. 确认方案中 `confirmed` 为 `true`；存在录音时还须确认逐字稿检查与反向核查已经完成。
3. 读取相邻 `lawyerbuddy-sorting/references/completeness.md`、`extraction.md`、`event-model.md`、`report.md`、`output-schema.md`、`lawyer-writing.md` 和 `qa.md`。
4. 将 `processing_mode` 设为 `report`；确定并记录 `analysis_scope`，完整核对决定主体、金额、履行、责任和程序状态的关键材料。普通材料先机器检索，发现冲突或新增关键事实时升级核对。
5. 复核 `fact_inventory`、`fact_disposition` 和 `legal_fact_map`；报告中的每项关键事实必须引用已核对材料并提供原文定位。
6. 关键材料与事实追溯门禁通过后，使用相邻 `lawyerbuddy-sorting/scripts/build_report.py` 生成报告。只有用户明确要求全量复核时，才要求全部材料和阅读单元覆盖率达到 100%。
7. 文件名和文档标题必须使用归档方案中已确认的主要案由。
8. 不重新分类、移动或覆盖原始材料；输入不足时列出待确认项。
9. 报告完成后更新 `workflow_handoff`，记录报告绝对路径，并推荐下一步使用 `lawyerbuddy-timeline` 根据同一 JSON 生成可视化时间轴。未经用户确认不自动执行下一 Skill。

默认输出：`整理结果/{确认案由}案件梳理报告.docx`。

完成后询问：

> Word 案件梳理报告已经生成。建议继续生成可视化关键时间轴：
>
> A. 继续使用 `lawyerbuddy-timeline` 生成时间轴（推荐）；
> B. 先打开 Word 报告；
> C. 暂时结束。
