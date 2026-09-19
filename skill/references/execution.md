# 执行脚本说明

脚本用于机械执行，不代替内容判断。AI 必须在 `plan.json` 中补充和复核分类、名称、主体、事件、冲突及案件链路摘要，再向用户展示预览。

## 标准顺序

```bash
python scripts/inventory.py <原材料文件夹> --out <工作目录>/inventory.json
python scripts/build_plan.py <工作目录>/inventory.json --out <工作目录>/plan.json
```

此时停止。AI 按 extraction、entity-resolution、dedup-version、event-model 规则补充 `plan.json`，展示用户确认。

内容复核完成后，先生成执行前目录树：

```bash
python scripts/build_tree.py <工作目录>/plan.json --stage preview --out <工作目录>/归档目录预览.md
```

AI 必须读取 `归档目录预览.md`，把其中目录树和 A/B/C 选项直接显示在对话中。不得只发送文件路径，也不得在用户选择 A 前执行归档。

确认后：

```bash
python scripts/apply_plan.py <工作目录>/plan.json <结果目录> --confirmed
python scripts/build_index.py <结果目录>/归档方案_已执行.json
```

`build_index.py` 会自动生成 `<结果目录>/归档结果目录.md`。需要单独重建时可运行：

```bash
python scripts/build_tree.py <结果目录>/归档方案_已执行.json --stage result --out <结果目录>/归档结果目录.md
```

AI 必须读取该文件，把执行后的实际目录树和下一步 A/B/C 选项直接显示在对话中。

用户选择生成时间轴后：

```bash
python scripts/build_timeline.py <结果目录>/案件材料汇总.xlsx --out <结果目录>/时间轴.html
```

## plan.json 扩展字段

- `case_summary`：起因、过程、争议、现状、缺口及对应依据；
- `entities`：按 entity-resolution.md 的字段填写；
- `events`：按 event-model.md 合并后的事件；
- `issues`：冲突、缺口及建议核验动作；
- `items`：逐文件分类、命名、重复组、版本组和解析状态。

`build_plan.py` 产生的是机器预览，不得未经内容审查直接执行。`apply_plan.py` 没有 `--confirmed` 时必须拒绝运行。
