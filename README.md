# case-material-organizer

把用户提供的散乱案件材料文件夹，整理成可确认、可追溯、可视化的标准案件目录。

它会读取文档与图片、统一主体、识别重复件、合并事件、提出待核问题；在用户确认目录树后，再复制、分类和规范命名。原始文件始终保持只读。

所有主要成果按律师阅读习惯组织：先看案件概览和主时间轴，再看当事人、材料清单和待补材料；系统术语与机器数据留在技术资料中。

```text
散乱材料文件夹
  → 读取文档与图片文字
  → 主体统一 / 重复与版本识别
  → 多份材料合并为事件
  → Markdown 目录树确认
  → 001—005 分类、复制和改名
  → 整理结果（Excel / 材料统计与目录 / HTML 时间轴）
```

## 效果预览

### 先确认目录与改名，再执行归档

![归档前目录树确认](./examples/demo-labor-dispute/screenshots/01-directory-tree-preview.png)

### 生成面向律师的案件概览与时间轴

![Excel 案件链路与时间轴](./examples/demo-labor-dispute/screenshots/02-workbook-timeline.png)

### 输出清晰的 HTML 时间轴

![HTML 时间轴](./examples/demo-labor-dispute/screenshots/03-html-timeline.png)

[查看完整的 12 份材料精简劳动争议示例](./examples/demo-labor-dispute/README.md)

## 安装

在需要使用 Skill 的项目目录中运行：

```bash
npx github:bseazh/case-material-organizer install
```

安装到指定项目：

```bash
npx github:bseazh/case-material-organizer install --target /path/to/project
```

锁定版本：

```bash
npx github:bseazh/case-material-organizer#v0.4.1 install
```

安装位置：

```text
.agents/skills/case-material-organizer/
```

环境检查：

```bash
npx github:bseazh/case-material-organizer doctor
```

必需环境为 Node.js 18+、Python 3 和 `openpyxl`。LibreOffice、Poppler 和 Chrome/Playwright 用于部分预览、PDF 或截图输出。

## 核心能力

- 读取 PDF、DOCX、XLSX、图片、TXT、CSV、JSON 等材料；
- 读取图片和扫描 PDF 中的文字，并标记需要核对原件的内容；
- 区分事件发生时间、材料形成时间和文件修改时间；
- 建立主体标准名称、别名、角色和来源材料映射；
- 识别完全重复、疑似重复、格式副本和独立版本；
- 将多份证据合并到同一事件，避免“一份证据等于一条时间轴”；
- 区分案件主线与主体历史背景，避免工商沿革挤占主时间轴；
- 固定使用 `001` 至 `005` 五个材料分类目录，成果统一放入 `整理结果`；
- 归档前后生成 Markdown 目录树，并在对话中直接展示；
- 生成 `整理结果/案件材料汇总.xlsx`、`材料统计与目录.txt`、基础资料索引；
- 按用户选择生成确定性 HTML/PNG/PDF 时间轴。

## 简明 Excel

`案件材料汇总.xlsx` 按律师阅读顺序提供 5 张主要表；存在音视频时，才在最后增加第 6 张表：

```text
案件概览
案件时间轴
当事人信息
材料清单
待补材料
音视频材料（仅存在音视频时显示）
```

表格不显示事件编号、材料编号、SHA-256、重复组、版本组、原文定位或机器路径。这些技术数据只保留在 `整理结果/技术资料/归档方案_已执行.json` 中，律师无需查看。

音频和视频在当前版本中只登记和归档，不播放、不转写、不参与事实提取。用户提供逐字稿时，将逐字稿作为普通文本材料处理。

## 两次确认

第一次发生在复制文件之前：

```text
A. 确认目录与命名，执行归档
B. 调整分类、命名或事件合并方案
C. 只保留预览，不复制文件
```

第二次发生在归档完成之后：

```text
A. 生成案件时间轴 HTML/PNG/PDF
B. 只保留 Excel、TXT 和归档目录
C. 先打开或检查整理结果
```

## 标准输出

```text
案件材料_整理结果/
├── 001 主体信息/
├── 002 基础资料/
│   └── index.md
├── 003 委托材料/
├── 004 类案及法律检索/
├── 005 法律文书/
└── 整理结果/
    ├── 案件材料汇总.xlsx
    ├── 案件材料时间轴.html（可选）
    ├── 案件材料时间轴.png（可选）
    ├── 案件材料时间轴.pdf（可选）
    ├── 材料统计与目录.txt
    └── 技术资料/
        ├── 归档结果目录.md
        └── 归档方案_已执行.json
```

空分类目录仍会保留，并注明“本次未发现相关材料”。`材料统计与目录.txt` 只显示材料总数、已整理材料、需人工查看和目录树，不向律师展示技术映射。

## 安全边界

- 原材料文件夹只读，不删除、不覆盖、不直接改名；
- 未经用户确认，不复制归档或生成最终时间轴；
- 不补造日期、主体、金额、聊天内容或案件事实；
- 重复件和不同版本均保留，详细关系只写入技术资料；
- 时间轴中的每个事件必须能追溯到材料编号和原文位置；
- 冲突信息并列记录，不擅自选择对任何一方有利的版本。

## 仓库结构

```text
bin/          npx 安装与环境检查命令
skill/        可安装的 Skill 本体
  assets/     Excel 与 Markdown 模板
  references/ 渐进式披露规则
  scripts/    清点、提取、目录树、归档、索引和时间轴脚本
examples/     可直接浏览的虚构案例与截图
```

## License

MIT
