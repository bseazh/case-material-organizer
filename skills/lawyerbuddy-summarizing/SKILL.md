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
4. 对照原材料复核 `reading_coverage`：全部材料、PDF 页面、可见工作表、图片和长文分段必须覆盖；不能只复用旧摘要。
5. 复核 `fact_inventory`、`fact_disposition` 和 `legal_fact_map`，完成完整提取、跨材料核对和法律事实复核三轮记录。
6. 三项覆盖率均为 100% 后，使用相邻 `lawyerbuddy-sorting/scripts/build_report.py` 生成报告。脚本门禁失败时列出未读范围，不得绕过或手工填写百分比。
7. 文件名和文档标题必须使用归档方案中已确认的主要案由。
8. 不重新分类、移动或覆盖原始材料；输入不足时列出待确认项。

默认输出：`整理结果/{确认案由}案件梳理报告.docx`。
