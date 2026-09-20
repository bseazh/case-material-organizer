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

## 什么时候使用

当一个案件文件夹里同时存在合同、聊天截图、银行流水、工资表、扫描件等材料，而且文件名、日期和目录比较散乱时，可以使用本 Skill。它适合在能够访问本地项目文件的代码级 Agent 中运行，例如 Codex、Claude Code、WorkBuddy，以及其他支持 Agent Skills 或本地工作区的工具。

普通网页聊天如果不能访问电脑上的完整文件夹，就无法直接完成分类和复制。请先在所用 Agent 中打开项目目录，或者通过该平台的“添加文件夹”“Open Folder”“Add Folder to Workspace”等功能，把案件材料文件夹加入当前工作区。

## 三步快速向导

### 第一步：安装 Skill

安装前需要 Node.js 18 或更高版本以及 Git；`npx` 随 Node.js/npm 提供。

最简单的方式，是把下面这句话原样发给 Agent：

```text
请安装 case-material-organizer Skill：

1. 先读取并遵守安装指引：
   https://github.com/bseazh/case-material-organizer/blob/v0.5.1/INSTALL.md
2. 首次或版本变化时，只对安装器做一次安全检查：审查 package.json 和 bin/cli.js。
3. 审查和安装都使用 v0.5.1，不要审查 main 后安装不同内容。
4. 执行远程 npx 命令时，累计等待至少 300 秒；单次等待不足时保留会话并轮询，不要主动终止。
5. Python 依赖先使用默认 PyPI。只有默认源失败并确认网络条件适合时，才考虑镜像；不要关闭 TLS 校验。
6. 不要用 tail 截断安装结果。以退出码和最终 doctor 检查为准。
7. 不要自动安装 Poppler、Tesseract 或浏览器等大体积可选组件。

npx --yes github:bseazh/case-material-organizer#v0.5.1 install
node .agents/skills/case-material-organizer/scripts/doctor.js doctor
```

熟悉终端的用户，也可以直接在项目目录中运行：

```bash
npx --yes github:bseazh/case-material-organizer#v0.5.1 install
node .agents/skills/case-material-organizer/scripts/doctor.js doctor
```

安装后 Skill 位于：

```text
.agents/skills/case-material-organizer/
```

### 第二步：把案件材料文件夹交给 Agent

可以使用以下任一方式：

1. 在 Agent 中使用“添加文件夹”“Open Folder”或“Add Folder to Workspace”，直接把案件材料文件夹加入当前项目。
2. 复制案件材料文件夹的绝对路径，并粘贴到对话中。

macOS 复制绝对路径：

1. 在 Finder 中选中案件材料文件夹。
2. 按 `Option + Command + C`。
3. 回到 Agent 对话框，按 `Command + V` 粘贴。

Windows 复制绝对路径：

1. 在文件资源管理器中打开案件材料文件夹。
2. 按 `Alt + D` 选中地址栏路径。
3. 按 `Ctrl + C` 复制，再到 Agent 对话框按 `Ctrl + V` 粘贴。

Windows 也可以按住 `Shift` 后右键点击文件夹，选择“复制文件地址”或“复制为路径”。路径两侧带引号也可以直接使用。

### 第三步：@ Skill 并发送路径

如果 Agent 支持 `@` 调用 Skill，输入 `@case-material-organizer`；如果没有 `@` 功能，直接在话术中写出 Skill 名称即可。

把下面的话复制给 Agent，并将示例路径替换为自己的案件材料文件夹路径：

```text
@case-material-organizer

请使用 case-material-organizer 整理下面的案件材料文件夹：
/Users/你的名字/Documents/案件材料

先只读取和分析原材料，展示拟分类目录树、改名结果和待确认事项。未经我确认，不要复制、移动、覆盖或删除任何原文件。
```

Windows 示例：

```text
@case-material-organizer

请使用 case-material-organizer 整理下面的案件材料文件夹：
C:\Users\你的名字\Documents\案件材料

先只读取和分析原材料，展示拟分类目录树、改名结果和待确认事项。未经我确认，不要复制、移动、覆盖或删除任何原文件。
```

Agent 完成预览后会给出 A/B/C 选项。选择 `A` 才会执行分类、复制和重命名；整理完成后，再选择是否生成 HTML、PNG、PDF 时间轴。

整理结果的最外层文件夹统一命名为：

```text
序号-原告简称VS被告简称-案由
```

例如：`1-张三VS李四-买卖合同纠纷`。四项信息会在复制归档前让用户确认。完成后，Agent 会在 macOS 访达或 Windows 文件资源管理器中定位该文件夹，并在回复中单独显示可点击的绝对路径。

## 效果预览

### 先确认目录与改名，再执行归档

![归档前目录树确认](./examples/demo-labor-dispute/screenshots/01-directory-tree-preview.png)

### 生成面向律师的案件概览与时间轴

![Excel 案件链路与时间轴](./examples/demo-labor-dispute/screenshots/02-workbook-timeline.png)

### 输出清晰的 HTML 时间轴

![HTML 时间轴](./examples/demo-labor-dispute/screenshots/03-html-timeline.png)

[查看完整的 12 份材料精简劳动争议示例](./examples/demo-labor-dispute/README.md)

## 安装与环境说明

完整的安装前审查、超时重试、代理和换源规则见 [INSTALL.md](./INSTALL.md)。Skill 尚未安装时，应让 Agent 先读取该文件；安装后遇到问题则读取 Skill 内的 `references/installation.md`。

在需要使用 Skill 的项目目录中运行：

```bash
npx --yes github:bseazh/case-material-organizer#v0.5.1 install
```

安装到指定项目：

```bash
npx --yes github:bseazh/case-material-organizer#v0.5.1 install --target /path/to/project
```

锁定版本：

```bash
npx --yes github:bseazh/case-material-organizer#v0.5.1 install
```

安装位置：

```text
.agents/skills/case-material-organizer/
```

首次使用先运行 `doctor`。它只检查环境，不会自动下载或修改系统：

```bash
node .agents/skills/case-material-organizer/scripts/doctor.js doctor
```

完整的 Python 依赖只有 `openpyxl`、`python-docx` 和 `Pillow`。其中 `openpyxl` 用于生成 Excel，是核心依赖；另外两个只影响 Word 和图片材料。为避免系统 Python 权限、版本或包冲突，建议在已安装 Skill 的项目目录中使用独立环境：

```bash
python3 -m venv .case-material-env
.case-material-env/bin/python -m pip install -r .agents/skills/case-material-organizer/requirements.txt
```

Windows PowerShell 使用：

```bash
py -3 -m venv .case-material-env
.\.case-material-env\Scripts\python.exe -m pip install -r .agents\skills\case-material-organizer\requirements.txt
```

先使用默认 PyPI。只有默认源持续不可达、并确认当前代理不会拦截镜像时，才考虑清华镜像：

```bash
.case-material-env/bin/python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r .agents/skills/case-material-organizer/requirements.txt
```

Windows 将命令开头替换为 `.\.case-material-env\Scripts\python.exe`。

`doctor` 会根据电脑实际可用的 `python3`、`python` 或 Windows `py -3` 输出对应命令。如果是在仓库源码目录开发，把依赖路径改为 `skill/requirements.txt`。

安装完成后再次运行 `doctor`；它会优先检查项目中的 `.case-material-env`。后续整理脚本也必须使用这个项目环境，避免出现“已经安装但仍提示缺少”。

这三个包通常只占几十 MB，具体取决于系统、Python 版本和缓存。Poppler、Tesseract 中文语言包以及浏览器组件体积更大，因此不自动安装，只在需要 PDF 文字提取、扫描件/图片 OCR 或时间轴 PNG/PDF 时按 `doctor` 提示安装。缺少可选组件时，相关文件会标记为“需人工查看”，其他材料仍继续整理。Windows 用户可以先完成普通材料整理，需要 OCR 时再安装相应工具并加入 `PATH`。

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
1-张三VS李四-买卖合同纠纷/
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
