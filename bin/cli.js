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
  printStatus(label, ok, optional);
  return ok;
}

function printStatus(label, ok, optional = false) {
  const mark = ok ? "OK" : optional ? "可选-未发现" : "缺少";
  console.log(`${mark.padEnd(9)} ${label}`);
}

function findPython(project) {
  const projectCandidates = [
    path.join(project, ".case-material-env", "bin", "python"),
    path.join(project, ".case-material-env", "Scripts", "python.exe")
  ].filter((executable) => fs.existsSync(executable)).map((executable) => ({
    executable, prefix: [], source: "项目环境"
  }));
  const candidates = [...projectCandidates,
    { executable: "python3", prefix: [] },
    { executable: "python", prefix: [] },
    { executable: "py", prefix: ["-3"] }
  ];
  let unsupported = null;
  for (const candidate of candidates) {
    const result = spawnSync(candidate.executable, [...candidate.prefix, "--version"], { encoding: "utf8" });
    const output = `${result.stdout || ""} ${result.stderr || ""}`;
    const match = output.match(/Python\s+(\d+)\.(\d+)/);
    if (!result.error && result.status === 0 && match) {
      const supported = Number(match[1]) > 3 || (Number(match[1]) === 3 && Number(match[2]) >= 9);
      const found = { ...candidate, supported, version: `${match[1]}.${match[2]}` };
      if (supported) return found;
      unsupported ||= found;
    }
  }
  return unsupported;
}

function pythonArgs(python, args) {
  return [...python.prefix, ...args];
}

function pythonCommand(python) {
  return [python.executable, ...python.prefix].join(" ");
}

function checkPythonPackage(label, moduleName, distribution, minimum, python, optional = false) {
  const minimumTuple = minimum.split(".").map(Number).join(",");
  const code = [
    "import importlib, importlib.metadata as metadata, re",
    `importlib.import_module(${JSON.stringify(moduleName)})`,
    `version = metadata.version(${JSON.stringify(distribution)})`,
    "parts = tuple(int(x) for x in re.findall(r'\\d+', version)[:2])",
    `assert parts >= (${minimumTuple},), version`
  ].join("; ");
  return check(`${label} >= ${minimum}`, python.executable, pythonArgs(python, ["-c", code]), optional);
}

function checkChineseOcr() {
  const result = spawnSync("tesseract", ["--list-langs"], { encoding: "utf8" });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  const ok = !result.error && result.status === 0 && /(^|\s)chi_sim(\s|$)/m.test(output);
  console.log(`${(ok ? "OK" : "可选-未发现").padEnd(9)} Tesseract 简体中文语言包`);
  return ok;
}

function checkBrowser() {
  const commands = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "microsoft-edge", "microsoft-edge-stable"
  ];
  const commandFound = commands.some((name) => {
    const result = spawnSync(name, ["--version"], { encoding: "utf8" });
    return !result.error && result.status === 0;
  });
  const locations = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, "Google", "Chrome", "Application", "chrome.exe"),
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, "Microsoft", "Edge", "Application", "msedge.exe"),
    process.env["PROGRAMFILES(X86)"] && path.join(process.env["PROGRAMFILES(X86)"], "Google", "Chrome", "Application", "chrome.exe"),
    process.env["PROGRAMFILES(X86)"] && path.join(process.env["PROGRAMFILES(X86)"], "Microsoft", "Edge", "Application", "msedge.exe"),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, "Google", "Chrome", "Application", "chrome.exe")
  ].filter(Boolean);
  const locationWorks = locations.some((location) => {
    if (!fs.existsSync(location)) return false;
    const result = spawnSync(location, ["--version"], { encoding: "utf8" });
    return !result.error && result.status === 0;
  });
  const ok = commandFound || locationWorks;
  printStatus("Chrome/Edge/Chromium（PNG/PDF时间轴）", ok, true);
  return ok;
}

function doctor() {
  console.log("case-material-organizer 环境检查\n");
  const project = targetProject();
  const nodeOk = Number(process.versions.node.split(".")[0]) >= 18;
  printStatus("Node.js >= 18", nodeOk);
  const python = findPython(project);
  const pythonOk = Boolean(python && python.supported);
  const pythonSource = python && python.source ? `，${python.source}` : "";
  printStatus(python ? `Python >= 3.9（当前 ${python.version}${pythonSource}）` : "Python >= 3.9", pythonOk);
  const openpyxlOk = pythonOk && checkPythonPackage(
    "openpyxl（Excel核心）", "openpyxl", "openpyxl", "3.1", python
  );

  console.log("\n按需能力");
  const docxOk = pythonOk && checkPythonPackage(
    "python-docx（Word）", "docx", "python-docx", "1.1", python, true
  );
  const pillowOk = pythonOk && checkPythonPackage(
    "Pillow（图片）", "PIL", "Pillow", "10", python, true
  );
  const pdftotextOk = check("Poppler pdftotext（PDF文字）", "pdftotext", ["-v"], true);
  const pdftoppmOk = check("Poppler pdftoppm（扫描PDF）", "pdftoppm", ["-v"], true);
  const tesseractOk = check("Tesseract（图片OCR）", "tesseract", ["--version"], true);
  const chineseOcrOk = tesseractOk && checkChineseOcr();
  const browserOk = checkBrowser();
  check("LibreOffice（Office预览）", "soffice", ["--version"], true);

  const installedRequirements = path.join(
    project, ".agents", "skills", "case-material-organizer", "requirements.txt"
  );
  const bundledRequirements = path.resolve(__dirname, "..", "skill", "requirements.txt");
  const requirements = fs.existsSync(installedRequirements) ? installedRequirements : bundledRequirements;
  if (!pythonOk) {
    console.log("\n请先安装 Python 3.9 或更高版本，再重新运行 doctor：");
    console.log("macOS: brew install python");
    console.log("Ubuntu/Debian: sudo apt install python3 python3-venv");
    console.log("Windows: winget install Python.Python.3.12");
  }
  if (pythonOk && (!openpyxlOk || !docxOk || !pillowOk)) {
    const launcher = pythonCommand(python);
    const pipOk = check("pip（安装Python依赖）", python.executable, pythonArgs(python, ["-m", "pip", "--version"]));
    const environmentPython = process.platform === "win32"
      ? ".\\.case-material-env\\Scripts\\python.exe"
      : ".case-material-env/bin/python";
    console.log("\n缺少 Python 依赖。建议使用当前项目的独立环境，不影响系统 Python：");
    if (python.source !== "项目环境") console.log(`${launcher} -m venv .case-material-env`);
    console.log("先使用默认 PyPI：");
    console.log(`${environmentPython} -m pip install -r "${requirements}"`);
    const proxyConfigured = [
      "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"
    ].some((name) => Boolean(process.env[name]));
    if (proxyConfigured) {
      console.log("检测到代理环境；不要因地区自动切换镜像。默认源失败时先检查代理返回的错误。");
    } else {
      console.log("默认源持续不可达时，再征得用户同意后尝试清华镜像：");
      console.log(`${environmentPython} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r "${requirements}"`);
    }
    if (!pipOk) console.log(`如无法创建环境，先运行：${launcher} -m ensurepip --upgrade`);
    if (process.platform !== "win32") {
      console.log("Ubuntu/Debian 如提示无法创建环境：sudo apt install python3-venv");
    }
  }
  if (!pdftotextOk || !pdftoppmOk || !tesseractOk || !chineseOcrOk) {
    console.log("\nOCR/PDF 组件未齐全时，相关文件会标记为“需人工查看”，其他材料仍继续整理。");
    console.log("macOS: brew install poppler tesseract tesseract-lang");
    console.log("Ubuntu/Debian: sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim");
    console.log("Windows: 可先跳过；需要 OCR 时安装 Poppler 与 Tesseract 中文语言包并加入 PATH。");
  }
  if (!browserOk) {
    console.log("\n仅在需要导出时间轴 PNG/PDF 时安装 Chrome、Edge 或 Chromium；HTML 时间轴不受影响。");
  }
  if (!nodeOk || !pythonOk || !openpyxlOk) process.exit(1);
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
