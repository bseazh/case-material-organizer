---
name: lawyerbuddy
description: LawyerBuddy 总路由。用户提出案件材料分类、案件总结、关键时间轴、类案检索、法律文书起草或合同审查时，先判断任务类型，再转交对应的 LawyerBuddy 产品 Skill；复杂任务按依赖顺序串联，避免同时加载无关能力。
---

# LawyerBuddy 总路由

本 Skill 只负责识别任务、检查前置成果和选择产品 Skill，不重复执行具体法律工作。

## 路由规则

1. 材料清点、OCR、分类、改名、归档或完整案件整理：读取 `lawyerbuddy-sorting`。
2. 已有归档方案，需要生成或更新案件梳理 Word 报告：读取 `lawyerbuddy-summarizing`。
3. 已有归档方案，需要生成或更新可视化关键时间轴：读取 `lawyerbuddy-timeline`。
4. 类案、裁判规则或相似判决检索：读取 `lawyerbuddy-similar-case-retrieval`。
5. 起诉状、答辩状、代理词、律师函或法律意见书起草：读取 `lawyerbuddy-document-drafting`。
6. 合同条款、履约、交易或争议风险审查：读取 `lawyerbuddy-contract-review`。

## 编排原则

- 每次只确定一个主 Skill；确有上下游依赖时再顺序调用其他 Skill。
- 完整案件整理默认由 `lawyerbuddy-sorting` 执行原有端到端流程，避免迁移后功能倒退。
- 报告与时间轴必须读取同一份已确认、已执行的 `归档方案_已执行.json`。
- 类案检索、文书起草和合同审查当前只建立产品入口；能力库接入前不得声称已经完成真实检索或专项法律分析。
- 不编造案件事实、法条、案号、裁判要旨或效力状态；不确定内容标记“待确认”或“待检索”。

安装后的模块状态见 `.agents/lawyerbuddy/skills.json`。只有状态为 `ready` 的模块可以直接执行。
