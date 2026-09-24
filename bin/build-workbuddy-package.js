#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const ref = process.argv[2] || "HEAD";
const outputDirectory = path.join(root, "dist");
const folder = path.join(outputDirectory, `lawyerbuddy-workbuddy-v${pkg.version}`);
const archive = `${folder}.zip`;
const packagePaths = ["SKILL.md", "README.md", "INSTALL.md", "bin", "package.json", "skills", "runtime", "manifests", "docs"];

fs.mkdirSync(outputDirectory, { recursive: true });
fs.rmSync(folder, { recursive: true, force: true });
fs.rmSync(archive, { force: true });

const zipResult = spawnSync("git", ["archive", "--format=zip", `--output=${archive}`, ref, ...packagePaths], {
  cwd: root,
  encoding: "utf8",
});
if (zipResult.status !== 0) {
  console.error(zipResult.stderr || zipResult.stdout || "无法生成 Workbuddy ZIP");
  process.exit(zipResult.status || 1);
}

const tarResult = spawnSync("git", ["archive", "--format=tar", ref, ...packagePaths], {
  cwd: root,
  maxBuffer: 128 * 1024 * 1024,
});
if (tarResult.status !== 0) {
  console.error(tarResult.stderr?.toString("utf8") || "无法读取 Workbuddy 上传文件夹内容");
  process.exit(tarResult.status || 1);
}

fs.mkdirSync(folder, { recursive: true });
const extract = spawnSync("tar", ["-xf", "-", "-C", folder], {
  cwd: root,
  input: tarResult.stdout,
  encoding: "utf8",
});
if (extract.status !== 0) {
  console.error(extract.stderr || "无法生成 Workbuddy 上传文件夹");
  process.exit(extract.status || 1);
}

const skillPath = path.join(folder, "SKILL.md");
if (!fs.existsSync(skillPath)) {
  console.error("打包失败：上传文件夹根目录缺少 SKILL.md");
  process.exit(1);
}
const skillText = fs.readFileSync(skillPath, "utf8");
if (!skillText.startsWith("---\n") || !/^name:\s*lawyerbuddy\s*$/m.test(skillText)
    || !/^description:\s*.+$/m.test(skillText)) {
  console.error("打包失败：根 SKILL.md 缺少有效的 YAML name/description");
  process.exit(1);
}

const verify = spawnSync("unzip", ["-Z1", archive], { encoding: "utf8" });
if (verify.status !== 0) {
  console.error(verify.stderr || "无法检查 Workbuddy ZIP");
  process.exit(verify.status || 1);
}
const entries = verify.stdout.split(/\r?\n/).filter(Boolean);
if (!entries.includes("SKILL.md")) {
  console.error("打包失败：ZIP 顶层缺少 SKILL.md");
  process.exit(1);
}
if (entries.some((entry) => path.basename(entry).toUpperCase() === "LICENSE")) {
  console.error("打包失败：ZIP 中发现不允许上传的 LICENSE 文件");
  process.exit(1);
}
console.log(JSON.stringify({
  folder,
  zip: archive,
  version: pkg.version,
  source_ref: ref,
  root_skill: "SKILL.md",
  excluded: ["examples/", "tests/"],
  entries: entries.length,
  size: fs.statSync(archive).size,
}, null, 2));
