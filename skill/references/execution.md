# 执行脚本说明

脚本用于机械执行，不代替内容判断。AI 必须在 `plan.json` 中补充和复核分类、名称、主体、事件、冲突及案件链路摘要，再向用户展示预览。

## 标准顺序

先运行 `doctor`。下列 `<PYTHON>` 必须使用 `doctor` 确认通过的解释器；显示“项目环境”时，macOS/Linux 使用 `.case-material-env/bin/python`，Windows 使用 `.\.case-material-env\Scripts\python.exe`。一次整理中的所有脚本必须使用同一解释器。

```bash
<PYTHON> scripts/inventory.py <原材料文件夹> --out <工作目录>/inventory.json
<PYTHON> scripts/check_media.py <工作目录>/inventory.json --out <工作目录>/media-check.json
```

`check_media.py` 返回 `ready_for_case_analysis=false` 时必须停止内容分析，按 `media.md` 展示缺失录音清单和阿里云听悟链接，等待用户补充逐字稿。用户补充后重新运行 `inventory.py` 和 `check_media.py`。只有返回 `true` 才继续：

```bash
<PYTHON> scripts/extract_content.py <工作目录>/inventory.json --out-dir <工作目录>/content
<PYTHON> scripts/build_plan.py <工作目录>/inventory.json --media-check <工作目录>/media-check.json \
  --directory-mode default --out <工作目录>/plan.json
```

读取 `content/extractions.json` 和完整逐字稿提取文本。存在逐字稿时先填写 `transcript_mainline_review`，再以全部其他材料反向核对并补充 `entities`、`events`、`issues` 和 `case_summary`。

上例用于用户选择默认目录。用户选择自定义目录时，逐个传入已确认的一级目录，例如：

```bash
<PYTHON> scripts/build_plan.py <工作目录>/inventory.json --media-check <工作目录>/media-check.json --directory-mode custom \
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
<PYTHON> scripts/build_report.py <结果目录>/整理结果/技术资料/归档方案_已执行.json \
  --out <结果目录>/整理结果/案件梳理报告.docx
<PYTHON> scripts/build_timeline.py <结果目录>/整理结果/技术资料/归档方案_已执行.json \
  --out <结果目录>/整理结果/案件关键时间轴.html
```

需要单独重建确认 Markdown 时可运行：

```bash
<PYTHON> scripts/build_tree.py <结果目录>/整理结果/技术资料/归档方案_已执行.json --stage result --out <结果目录>/整理结果/技术资料/归档结果目录.md
```

AI 必须读取该文件，把执行后的实际目录树和下一步 A/B/C 选项直接显示在对话中。

完成归档成果后，在系统文件管理器中定位案件根文件夹：

```bash
<PYTHON> scripts/reveal_result.py <结果目录>
```

根据脚本返回的 `opened` 如实说明是否已定位，并在回复中显示 `absolute_path`。绝对路径必须裸露、单独成行，不放入代码块或 Markdown 链接；不得只发送技术资料路径。

默认到 HTML 为止。只有用户明确要求图片或 PDF 时，才按当前 Agent 的浏览器能力导出对应格式；缺少浏览器组件时保留 HTML 并说明影响，不得安装大体积组件后才继续交付 Word 报告。

## plan.json 扩展字段

- `case_summary`：起因、过程、争议、现状、缺口及对应依据；
- `entities`：按 entity-resolution.md 的字段填写；
- `events`：按 event-model.md 合并后的事件；
- `issues`：冲突、缺口及建议核验动作；
- `directory_mode`：`default` 或 `custom`；
- `directory_structure`：用户确认的一级材料目录；
- `directory_subfolders`：各一级目录下已确认的二级目录；
- `items`：逐文件分类、二级分类、命名、重复组、版本组和解析状态。
- `media_check`：录音、逐字稿对应关系和案件分析是否可继续；
- `transcript_mainline_review`：逐字稿候选主线、书面材料印证、冲突、遗漏和缺口的内部核对记录。存在录音时至少记录：候选事件、逐字稿位置、印证材料、冲突材料、仅见逐字稿事项、仅见书面材料事项和待补材料；该字段为空时不得执行完整归档、报告或时间轴。

`build_plan.py` 产生的是机器预览，不得未经内容审查直接执行。`apply_plan.py` 没有 `--confirmed` 时必须拒绝运行。
