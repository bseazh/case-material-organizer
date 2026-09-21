---
name: lawyerbuddy-document-drafting
description: LawyerBuddy 法律文书起草入口。用户要求起草起诉状、答辩状、代理词、律师函、法律意见书或裁判文书时使用；根据文书类型调用事实提取、争议识别、证据论证、法条检索、论证链、格式和术语能力。
---

# 法律文书起草

## 执行流程

1. 确认文书类型、用户立场、程序阶段、目标读者和交付格式；关键信息缺失时先列出缺失清单。
2. 按 `.agents/lawyerbuddy/routing/pipelines.json` 分阶段读取内部能力，每阶段最多三个。
3. 先提取事实、争议焦点和证据链，再检索并核验法律依据，最后构建论证和格式化正文。
4. `legal-document-formatting` 和 `judgment-document-generation` 主要面向裁判文书；起诉状、答辩状、代理词、律师函和法律意见书不得机械套用判决书结构。
5. 完稿前使用 `legal-terminology` 和 `argument-strength-evaluation` 检查术语、逻辑、依据与不确定性。

不得补造事实、证据、案号或法律依据。未经真实检索核验的法条与案例标记“待检索”；所有成果均为律师审阅稿。
