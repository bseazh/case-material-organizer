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
  return ok || optional;
}

function doctor() {
  console.log("case-material-organizer 环境检查\n");
  const checks = [
    check("Node.js >= 18", process.execPath, ["--version"]),
    check("Python 3", "python3", ["--version"]),
    check("openpyxl", "python3", ["-c", "import openpyxl; print(openpyxl.__version__)"]),
    check("LibreOffice", "soffice", ["--version"], true),
    check("Poppler", "pdftotext", ["-v"], true),
    check("Playwright", "playwright", ["--version"], true)
  ];
  if (!checks.every(Boolean)) process.exit(1);
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
