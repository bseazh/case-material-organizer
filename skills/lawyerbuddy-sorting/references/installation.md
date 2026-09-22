# 安装、更新与网络规则

本文件用于 Skill 已安装后的环境修复、更新或重装。首次下载前应读取仓库根目录 `INSTALL.md`。

## 固定顺序

1. 首次安装或版本变化时，只审查一次同一标签或提交下的 `package.json` 与 `bin/cli.js`；审查对象必须与安装对象一致。
2. 执行 `npx github:` 时，Agent 累计等待至少 300 秒；单次上限不足时保留会话并轮询，不主动终止。
3. 接近等待上限后出现 `137`、`SIGTERM` 或超时，检查 `SKILL.md`、`requirements.txt`、本文件和 `scripts/doctor.js` 是否齐全；原子安装未形成正式目录时只重试一次，异常正式目录存在时报告用户，不自动删除。
4. 先运行 `doctor`，只补它报告缺少的能力。
5. Python 包先用默认 PyPI；持续失败且未被代理拦截时，再选择一个国内镜像重试一次。
6. 安装结束后运行本地 `scripts/doctor.js`，用命令退出码和一次最终检查验收，不截断关键输出，不重复执行无必要的 `pip list`。

## 网络与镜像判断

- Python 包默认使用 PyPI；偶发 TLS、连接重置或超时只重试一次。
- 默认源持续不可达且无代理拦截时，可选清华 `https://pypi.tuna.tsinghua.edu.cn/simple` 或中科大 `https://pypi.mirrors.ustc.edu.cn/simple`，只尝试其中一个。
- Homebrew bottle/API 首选中科大：`https://mirrors.ustc.edu.cn/homebrew-bottles`。
- Homebrew bottle/API 备用清华：`https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles`。
- 镜像出现 `502`、`403`、TLS 或代理错误时停止使用镜像，回到默认源检查代理。
- 不关闭 TLS 校验，不添加 `--trusted-host` 规避证书。

## 更新与重装

若目标 Skill 已存在，不直接覆盖。先说明当前版本和目标版本，再由用户选择备份后更新或保留现状。不得为了处理一次超时而删除已安装目录。

## 可选大组件

Poppler、Tesseract 中文语言包和浏览器组件只在相应任务需要时安装，`doctor` 只检查和提示，不自动下载：

- 普通文本型 PDF 需要深度提取时，只安装 Poppler；
- 图片、聊天截图或扫描 PDF 需要 OCR 时，安装 Poppler、Tesseract 和中文语言包；
- DOCX、XLSX、TXT、CSV、JSON 或已有文字稿不触发这些安装。

macOS 命令使用单次生效的国内镜像变量，避免修改用户的永久 shell 配置：

```bash
# 普通文本型 PDF
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_API_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles/api HOMEBREW_BOTTLE_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles brew install poppler

# 图片或扫描 PDF OCR
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_API_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles/api HOMEBREW_BOTTLE_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles brew install poppler tesseract tesseract-lang
```

缺失时标记对应文件或导出格式暂不可用，其他材料继续处理。镜像仍使用 Homebrew 的 SHA256 校验；不要为了绕过 `ghcr.io` 而关闭校验。
