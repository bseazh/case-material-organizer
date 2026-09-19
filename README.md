# case-material-organizer

用于法律案件材料整理的 AI Skill。它将用户提供的现成文件夹进行只读清点，形成分类与改名预览，经用户确认后复制归档，并生成案件链路总览、Excel 时间轴、文件索引及可选的 HTML 时间轴。

## 主要能力

- 读取 PDF、Word、Excel、图片、TXT、CSV、JSON 等案件材料；
- 区分事件时间、材料形成时间和文件修改时间；
- 建立主体标准名称、别名和角色映射；
- 识别完全重复、疑似重复、不同格式副本和独立版本；
- 将多份证据合并到同一事件，避免“一份证据等于一个事件”；
- 按 `001` 至 `005` 五类目录复制归档并规范命名；
- 归档前后生成 Markdown 目录树，并在交互中直接展示改名结果供用户确认；
- 生成 `案件材料汇总.xlsx`、`index.txt` 和 `002 基础资料/index.md`；
- 根据已确认事件生成确定性 HTML 时间轴。

音频和视频在当前版本中只登记和归档，不播放、不转写、不参与事实提取。

## 使用 npx 安装

在需要使用 Skill 的项目目录中运行：

```bash
npx github:bseazh/case-material-organizer install
```

安装到另一个项目目录：

```bash
npx github:bseazh/case-material-organizer install --target /path/to/project
```

安装后目录为：

```text
.agents/skills/case-material-organizer/
```

建议在正式使用时锁定发布标签：

```bash
npx github:bseazh/case-material-organizer#v0.2.0 install
```

## 环境检查

```bash
npx github:bseazh/case-material-organizer doctor
```

必需环境：Node.js 18 或更高版本、Python 3、openpyxl。LibreOffice、Poppler 和 Playwright 属于文档预览或可视化导出的可选依赖。

## 安全边界

- 原材料文件夹只读，不删除、不覆盖、不直接改名；
- 未经用户确认，不执行复制归档；
- 不补造日期、主体、金额或案件事实；
- 重复件和不同版本均保留；
- 时间轴事件必须能够回溯到材料编号和原文位置。

## 仓库结构

```text
bin/       npx 安装与环境检查命令
skill/     可安装的 Skill 本体
  assets/  Excel 标准模板
  references/ 渐进式披露规则
  scripts/ 清点、预览、目录树确认、归档、索引和时间轴脚本
```

## 许可证

MIT
