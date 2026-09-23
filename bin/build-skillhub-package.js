#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const version = pkg.version;
const dist = path.join(root, "dist");
const bundle = path.join(dist, `lawyerbuddy-skillhub-v${version}`);
const archive = `${bundle}.zip`;
const maxFiles = 200;
const supportedExtensions = new Set([
  ".md", ".py", ".js", ".json", ".txt", ".html", ".css", ".svg", ".png", ".jpg", ".jpeg"
]);

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { cwd: root, encoding: "utf8", ...options });
  if (result.error || result.status !== 0) {
    throw new Error(result.error?.message || result.stderr || `${command} 执行失败`);
  }
  return result.stdout;
}

function include(relative) {
  const value = relative.split(path.sep).join("/");
  return value === "SKILL.md"
    || value === "README.md"
    || value === "INSTALL.md"
    || value === "LICENSE"
    || value.startsWith("docs/")
    || value.startsWith("skills/")
    || value.startsWith("runtime/routing/")
    || value.startsWith("runtime/references/")
    || value.startsWith("runtime/contracts/")
    || value.startsWith("runtime/capabilities/legal-skills-chinese/skills/")
    || value === "runtime/capabilities/legal-skills-chinese/NOTICE.md"
    || value === "runtime/capabilities/legal-skills-chinese/SOURCE.json";
}

function collectFiles(directory, prefix = "") {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const relative = path.posix.join(prefix, entry.name);
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) return collectFiles(absolute, relative);
    return entry.isFile() ? [relative] : [];
  });
}

try {
  fs.mkdirSync(dist, { recursive: true });
  fs.rmSync(bundle, { recursive: true, force: true });
  fs.rmSync(archive, { force: true });
  fs.mkdirSync(bundle, { recursive: true });

  const listed = run("git", ["ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    .split("\0")
    .filter(Boolean)
    .filter(include);

  for (const relative of listed) {
    const extension = path.extname(relative).toLowerCase();
    if ([".xlsx", ".xls", ".xlsm", ".pyc", ".pyo"].includes(extension)) continue;
    if (!supportedExtensions.has(extension) && path.basename(relative) !== "LICENSE") {
      throw new Error(`SkillHub 包含未允许的文件类型：${relative}`);
    }
    const source = path.join(root, relative);
    const destination = path.join(bundle, relative);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(source, destination);
  }

  const rootSkill = path.join(bundle, "SKILL.md");
  if (!fs.existsSync(rootSkill)) throw new Error("SkillHub 包根目录缺少 SKILL.md");
  const skillText = fs.readFileSync(rootSkill, "utf8");
  if (!skillText.startsWith("---\n") || !/^name:\s*lawyerbuddy\s*$/m.test(skillText)
      || !/^description:\s*.+$/m.test(skillText)) {
    throw new Error("根 SKILL.md 缺少有效的 YAML name/description");
  }

  const files = collectFiles(bundle);
  if (files.length > maxFiles) throw new Error(`文件数超出 SkillHub 上限：${files.length}/${maxFiles}`);
  const disallowed = files.filter((file) => !supportedExtensions.has(path.extname(file).toLowerCase())
    && path.basename(file) !== "LICENSE");
  if (disallowed.length) throw new Error(`发现不支持的文件：${disallowed.join("、")}`);

  run("zip", ["-qr", archive, "."], { cwd: bundle });
  const zipEntries = run("unzip", ["-Z1", archive]).split(/\r?\n/).filter(Boolean);
  if (!zipEntries.includes("SKILL.md")) throw new Error("ZIP 顶层缺少 SKILL.md");

  console.log(JSON.stringify({
    folder: bundle,
    zip: archive,
    files: files.length,
    limit: maxFiles,
    unsupported_files: 0,
    root_skill: "SKILL.md",
    cause_catalog: "skills/lawyerbuddy-sorting/assets/民事案件案由参考表_2025.json",
  }, null, 2));
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
