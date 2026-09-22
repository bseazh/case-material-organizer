# LawyerBuddy 模块交接规则

1. 上游模块只传递材料中有来源的信息，不把推测写成事实。
2. 已确认案由、主体标准名称和最终事件由下游模块直接复用；需要改变时返回上游重新确认。
3. 报告与时间轴以同一份 `归档方案_已执行.json` 为当前统一数据源。
4. 缺少字段时标记“待确认”，不得为了满足下游格式补造内容。
5. 每次交接记录输入文件绝对路径、生成时间和模块名称；普通律师成果不展示机器字段。
6. `case-data.schema.json` 是未来统一数据契约；在现有归档方案完成迁移前，不替代当前生产输入。
7. `workflow_handoff` 记录跨会话进度：`completed_skill`、`recommended_next_skill`、`case_root`、`plan_path`、`report_path`、`timeline_path`。路径必须来自实际生成结果，不得猜测。
8. 推荐链路为 `lawyerbuddy-sorting` → `lawyerbuddy-summarizing` → `lawyerbuddy-timeline`。推荐不等于授权；每次进入下一 Skill 前取得用户确认。
