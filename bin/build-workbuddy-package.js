#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const ref = process.argv[2] || "HEAD";
const outputDirectory = path.join(root, "dist");
const output = path.join(outputDirectory, `lawyerbuddy-workbuddy-v${pkg.version}.zip`);

fs.mkdirSync(outputDirectory, { recursive: true });
if (fs.existsSync(output)) fs.rmSync(output);

const result = spawnSync("git", ["archive", "--format=zip", `--output=${output}`, ref], {
  cwd: root,
  encoding: "utf8",
});
if (result.status !== 0) {
  console.error(result.stderr || result.stdout || "无法生成 Workbuddy ZIP");
  process.exit(result.status || 1);
}

const verify = spawnSync("unzip", ["-Z1", output], { encoding: "utf8" });
if (verify.status !== 0) {
  console.error(verify.stderr || "无法检查 Workbuddy ZIP");
  process.exit(verify.status || 1);
}
const entries = verify.stdout.split(/\r?\n/).filter(Boolean);
if (!entries.includes("SKILL.md")) {
  console.error("打包失败：ZIP 顶层缺少 SKILL.md");
  process.exit(1);
}

console.log(JSON.stringify({
  output,
  version: pkg.version,
  source_ref: ref,
  root_skill: "SKILL.md",
  entries: entries.length,
  size: fs.statSync(output).size,
}, null, 2));
