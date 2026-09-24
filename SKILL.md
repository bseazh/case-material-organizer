---
name: lawyerbuddy
description: 面向律师的法律工作总入口。用于案件材料分类归档、案件总结、关键时间轴、类案检索、起诉状及其他法律文书起草、合同起草和合同审查，并按任务路由到对应的 LawyerBuddy 子技能。
---

# LawyerBuddy

这是 Workbuddy 直接导入整个文件夹或 ZIP 时使用的总入口。按需读取子技能，不要一次加载全部规则或内部能力。

## 路由

1. 散乱案件材料的清点、OCR、分类、改名和归档：读取 `skills/lawyerbuddy-sorting/SKILL.md`。
2. 根据已执行归档方案生成或更新 Word 案件报告：读取 `skills/lawyerbuddy-summarizing/SKILL.md`。
3. 根据 Word 报告生成或更新可视化时间轴：读取 `skills/lawyerbuddy-timeline/SKILL.md`。
4. 类案、裁判规则或相似判决检索：读取 `skills/lawyerbuddy-similar-case-retrieval/SKILL.md`。
5. 民事起诉状起草或实质修改：读取 `skills/lawyerbuddy-complaint-draft/SKILL.md`；答辩状、代理词、律师函、法律意见书等其他法律文书：读取 `skills/lawyerbuddy-document-drafting/SKILL.md`。
6. 合同或协议起草、改写：读取 `skills/lawyerbuddy-contract-draft/SKILL.md`；合同条款、履约、交易或争议风险审查：读取 `skills/lawyerbuddy-contract-review/SKILL.md`。

## 执行原则

- 每次只加载当前任务需要的子技能；存在上下游依赖时按顺序执行。
- 案件材料工作流默认按 Sorting → Summarizing → Timeline 执行快速初稿，再按律师指定问题专项核对。
- 原始案件材料只读；复制、改名和归档前必须取得用户确认。
- 发现录音但缺少逐字稿时，允许快速归档原件，但暂停案件分析并提供 `https://tingwu.aliyun.com/home`。
- 不编造案件事实、法条、案号或裁判结论；不确定内容统一标记“待确认”或“待检索”。
- 子技能需要内部法律能力时，读取 `runtime/routing/capability-index.json`，再按索引加载 `runtime/capabilities/legal-skills-chinese/skills/{能力ID}/SKILL.md`。
- 脚本、参考规则和模板均以本文件所在目录为根目录解析。

详细介绍和使用示例见 `README.md`。
