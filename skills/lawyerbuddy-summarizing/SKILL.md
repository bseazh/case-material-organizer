---
name: lawyerbuddy-summarizing
description: LawyerBuddy 案件总结入口。用户已有经过确认并执行的案件归档方案，需要单独生成或更新包含案件主体、案件总结、关键时间轴表格和文件清单的 Word 案件梳理报告时使用。
---

# 案件总结

本 Skill 复用 `lawyerbuddy-sorting` 已验证的报告规则和脚本，不重新识别或改写案件事实。

## 执行要求

1. 定位用户指定案件下的 `整理结果/技术资料/归档方案_已执行.json`。
2. 确认方案中 `confirmed` 为 `true`；存在录音时还须确认逐字稿检查与反向核查已经完成。
3. 读取相邻 `lawyerbuddy-sorting/references/report.md`、`output-schema.md`、`lawyer-writing.md` 和 `qa.md`。
4. 使用相邻 `lawyerbuddy-sorting/scripts/build_report.py` 生成报告。
5. 文件名和文档标题必须使用归档方案中已确认的主要案由。
6. 不重新分类、移动或覆盖原始材料；输入不足时列出待确认项。

默认输出：`整理结果/{确认案由}案件梳理报告.docx`。
