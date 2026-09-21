---
name: lawyerbuddy-similar-case-retrieval
description: LawyerBuddy 类案检索入口。用户要求查找相似案例、裁判规则、同类判决或司法实践趋势时使用；提炼争议焦点和检索要素，调用内部案例检索、规范效力检查、类比推理和归纳推理能力，并要求真实检索来源。
---

# 类案检索

## 执行流程

1. 读取 `.agents/lawyerbuddy/routing/pipelines.json` 中本产品的阶段定义。
2. 先用 `dispute-issue-identification` 和 `legal-concept-comprehension` 提炼案由、争点、事实特征和关键词。
3. 使用 `case-retrieval` 设计并执行检索；引用法律规范时用 `legal-norm-validity-check` 核验。
4. 使用 `analogical-reasoning` 比较本案与候选案例的关键相同点和差异点；需要归纳趋势时再读取 `inductive-reasoning`。
5. 输出案例来源、案号、法院、日期、裁判要旨、相似点、差异点和适用限制。

如环境没有案例库、MCP、检索 API 或可访问的权威来源，只输出检索式与人工检索方案，所有具体案例标记“待检索”。严禁用模型记忆补造案例。
