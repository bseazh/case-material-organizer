# 执行脚本说明

脚本用于机械执行，不代替内容判断。AI 必须在 `plan.json` 中补充和复核分类、名称、主体、事件、冲突及案件链路摘要，再向用户展示预览。

## 标准顺序

先运行 `doctor`。下列 `<PYTHON>` 必须使用 `doctor` 确认通过的解释器；显示“项目环境”时，macOS/Linux 使用 `.case-material-env/bin/python`，Windows 使用 `.\.case-material-env\Scripts\python.exe`。一次整理中的所有脚本必须使用同一解释器。

```bash
<PYTHON> scripts/inventory.py <原材料文件夹> --out <工作目录>/inventory.json
<PYTHON> scripts/build_plan.py <工作目录>/inventory.json --directory-mode default --out <工作目录>/plan.json
```

上例用于用户选择默认目录。用户选择自定义目录时，逐个传入已确认的一级目录，例如：

```bash
<PYTHON> scripts/build_plan.py <工作目录>/inventory.json --directory-mode custom \
  --custom-folder "01 案件合同" --custom-folder "02 履约材料" --custom-folder "03 往来款项" \
  --out <工作目录>/plan.json
```

此时停止。AI 按 extraction、entity-resolution、dedup-version、event-model 规则补充 `plan.json`，并根据 `classification.md` 复核 `directory_structure`、`directory_subfolders`、`target_category` 和 `target_subcategory`，再展示用户确认。自定义模式下，脚本无法可靠判断的材料会暂留未分类，必须完成内容复核后才能生成预览。

同时填写 `case_folder.sequence`、`plaintiff_short_name`、`defendant_short_name`、`cause_of_action`，并把规范名称写入 `case_folder_name`。预览和执行均会机械校验 `序号-原告简称VS被告简称-案由`；信息不足时先询问用户。

内容复核完成后，先生成执行前目录树：

```bash
<PYTHON> scripts/build_tree.py <工作目录>/plan.json --stage preview --out <工作目录>/归档目录预览.md
```

AI 必须读取 `归档目录预览.md`，把其中目录树和 A/B/C 选项直接显示在对话中。不得只发送文件路径，也不得在用户选择 A 前执行归档。

确认后：

```bash
<PYTHON> scripts/apply_plan.py <工作目录>/plan.json <结果目录> --confirmed
<PYTHON> scripts/build_index.py <结果目录>/整理结果/技术资料/归档方案_已执行.json
```

`build_index.py` 会自动生成 `<结果目录>/整理结果/案件材料汇总.xlsx`、`材料统计与目录.txt` 和技术资料中的确认 Markdown。需要单独重建确认 Markdown 时可运行：

```bash
<PYTHON> scripts/build_tree.py <结果目录>/整理结果/技术资料/归档方案_已执行.json --stage result --out <结果目录>/整理结果/技术资料/归档结果目录.md
```

AI 必须读取该文件，把执行后的实际目录树和下一步 A/B/C 选项直接显示在对话中。

完成归档成果后，在系统文件管理器中定位案件根文件夹：

```bash
<PYTHON> scripts/reveal_result.py <结果目录>
```

根据脚本返回的 `opened` 如实说明是否已定位，并在回复中显示 `absolute_path`。绝对路径必须裸露、单独成行，不放入代码块或 Markdown 链接；不得只发送技术资料路径。

用户选择生成时间轴后：

```bash
<PYTHON> scripts/build_timeline.py <结果目录>/整理结果/案件材料汇总.xlsx --out <结果目录>/整理结果/案件材料时间轴.html
```

生成 PNG/PDF 后再次运行 `build_index.py`，让 `材料统计与目录.txt` 与确认 Markdown 收录最终成果文件。

## plan.json 扩展字段

- `case_summary`：起因、过程、争议、现状、缺口及对应依据；
- `entities`：按 entity-resolution.md 的字段填写；
- `events`：按 event-model.md 合并后的事件；
- `issues`：冲突、缺口及建议核验动作；
- `directory_mode`：`default` 或 `custom`；
- `directory_structure`：用户确认的一级材料目录；
- `directory_subfolders`：各一级目录下已确认的二级目录；
- `items`：逐文件分类、二级分类、命名、重复组、版本组和解析状态。

`build_plan.py` 产生的是机器预览，不得未经内容审查直接执行。`apply_plan.py` 没有 `--confirmed` 时必须拒绝运行。
