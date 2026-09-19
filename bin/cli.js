#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const command = process.argv[2] || "install";

function targetProject() {
  const index = process.argv.indexOf("--target");
  if (index === -1) return process.cwd();
  if (!process.argv[index + 1]) {
    console.error("--target 后需要提供项目目录路径。");
    process.exit(1);
  }
  return path.resolve(process.argv[index + 1]);
}

function install() {
  const source = path.resolve(__dirname, "..", "skill");
  const project = targetProject();
  const target = path.join(project, ".agents", "skills", "case-material-organizer");
  if (!fs.existsSync(source)) {
    console.error(`安装包中缺少 Skill：${source}`);
    process.exit(1);
  }
  if (fs.existsSync(target)) {
    console.error(`目标已存在，未覆盖：${target}`);
    console.error("请先备份或移走旧版本，再重新执行安装。");
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.cpSync(source, target, { recursive: true, errorOnExist: true });
  console.log("Skill 安装完成：");
  console.log(target);
}

function check(label, executable, args = ["--version"], optional = false) {
  const result = spawnSync(executable, args, { encoding: "utf8" });
  const ok = !result.error && result.status === 0;
  const mark = ok ? "OK" : optional ? "可选-未发现" : "缺少";
  console.log(`${mark.padEnd(9)} ${label}`);
  return ok;
}

function checkPythonModule(label, moduleName) {
  return check(label, "python3", ["-c", `import ${moduleName}`]);
}

function checkChineseOcr() {
  const result = spawnSync("tesseract", ["--list-langs"], { encoding: "utf8" });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  const ok = !result.error && result.status === 0 && /(^|\s)chi_sim(\s|$)/m.test(output);
  console.log(`${(ok ? "OK" : "可选-未发现").padEnd(9)} Tesseract 简体中文语言包`);
  return ok;
}

function doctor() {
  console.log("case-material-organizer 环境检查\n");
  const pythonOk = check("Python 3", "python3", ["--version"]);
  const required = [
    check("Node.js >= 18", process.execPath, ["--version"]),
    pythonOk,
    pythonOk && checkPythonModule("openpyxl（Excel）", "openpyxl"),
    pythonOk && checkPythonModule("python-docx（Word）", "docx"),
    pythonOk && checkPythonModule("Pillow（图片）", "PIL")
  ];

  console.log("\n按需能力");
  const pdftotextOk = check("Poppler pdftotext（PDF文字）", "pdftotext", ["-v"], true);
  const pdftoppmOk = check("Poppler pdftoppm（扫描PDF）", "pdftoppm", ["-v"], true);
  const tesseractOk = check("Tesseract（图片OCR）", "tesseract", ["--version"], true);
  const chineseOcrOk = tesseractOk && checkChineseOcr();
  const playwrightOk = check("Playwright（PNG/PDF时间轴）", "playwright", ["--version"], true);
  check("LibreOffice（Office预览）", "soffice", ["--version"], true);

  const installedRequirements = path.join(
    targetProject(), ".agents", "skills", "case-material-organizer", "requirements.txt"
  );
  const bundledRequirements = path.resolve(__dirname, "..", "skill", "requirements.txt");
  const requirements = fs.existsSync(installedRequirements) ? installedRequirements : bundledRequirements;
  if (!required.every(Boolean)) {
    check("pip（安装Python依赖）", "python3", ["-m", "pip", "--version"]);
    console.log("\n缺少核心依赖。请选择一条命令安装：");
    console.log(`python3 -m pip install -r "${requirements}"`);
    console.log(`python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r "${requirements}"`);
  }
  if (!pdftotextOk || !pdftoppmOk || !tesseractOk || !chineseOcrOk) {
    console.log("\nOCR/PDF 组件未齐全时，相关文件会标记为“需人工查看”，其他材料仍继续整理。");
    console.log("macOS: brew install poppler tesseract tesseract-lang");
    console.log("Ubuntu/Debian: sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim");
  }
  if (!playwrightOk) {
    console.log("\n仅在需要导出时间轴 PNG/PDF 时安装浏览器组件：");
    console.log("npx playwright@latest install chromium");
  }
  if (!required.every(Boolean)) process.exit(1);
  console.log("\n核心整理能力可用。可选组件缺失只影响对应文件或导出格式。");
}

function help() {
  console.log(`用法：
  case-material-organizer install [--target <项目目录>]
  case-material-organizer doctor
  case-material-organizer help`);
}

if (command === "install") install();
else if (command === "doctor") doctor();
else if (command === "help" || command === "--help" || command === "-h") help();
else {
  console.error(`未知命令：${command}`);
  help();
  process.exit(1);
}
