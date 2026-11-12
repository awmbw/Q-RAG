/* Build the self-contained educational site from an explicit public-file allowlist.
   npm ci --prefix tools/journey --ignore-scripts
   node scripts/build_journey.cjs
   No models, inference, private files or scientific source are changed. */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const loadTool = require("node:module").createRequire(
  path.join(root, "tools/journey/package.json"),
);
const MarkdownIt = loadTool("markdown-it");
const katex = loadTool("katex");
const out = path.join(root, "src/qrag_service/static/journey");
const content = require("../docs/journey/content.cjs");
const documents = [
  ["readme", "Project overview", "README.md"],
  ["report", "Research progress report", "docs/RESEARCH_PROGRESS_REPORT.md"],
  ["foundations", "Technical foundations", "docs/TECHNICAL_FOUNDATIONS.md"],
  ["sequence", "Development sequence", "docs/DEVELOPMENT_SEQUENCE.md"],
  ["plan", "Original implementation plan", "docs/IMPLEMENTATION_PLAN.md"],
  ["literature", "Literature comparison", "docs/LITERATURE_REVIEW.md"],
  ["protocol", "Frozen experiment protocol", "docs/EXPERIMENT_PROTOCOL.md"],
  ["reproducibility", "Reproduction guide", "docs/REPRODUCIBILITY.md"],
  ["claims", "Claim-to-evidence map", "docs/CLAIM_EVIDENCE_MAP.md"],
  ["service", "Service and laboratory", "docs/SERVICE_GUIDE.md"],
  ["manuscript", "Complete manuscript", "paper/manuscript.md"],
  ["handoff", "Remaining external work", "docs/HUMAN_HANDOFF.md"],
  ["rights", "Rights and attribution", "docs/RIGHTS_AND_ATTRIBUTION.md"],
  [
    "publication",
    "Publication preparation · dated snapshot",
    "docs/PUBLICATION_GUIDE.md",
  ],
  ["baseline", "Historical baseline execution", "docs/BASELINE_GUIDE.md"],
  ["main-results", "Main result tables", "paper/results/main_results.md"],
  [
    "sampling-results",
    "Sampling mechanism study",
    "paper/results/sampling_coverage.md",
  ],
  [
    "error-analysis",
    "Error signatures and examples",
    "paper/results/error_analysis.md",
  ],
];
// Every generated analysis table is available inside the site, not only headline rows.
for (const name of fs.readdirSync(path.join(root, "paper/results")).sort()) {
  if (name.endsWith("_analysis.md"))
    documents.push([
      "table-" + name.slice(0, -3),
      name.replaceAll("_", " ").replace(".md", ""),
      "paper/results/" + name,
    ]);
}
const byPath = new Map(documents.map(([id, , p]) => [p, id]));
const hash = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
function slug(text) {
  return text
    .toLowerCase()
    .replace(/[`*]/g, "")
    .replace(/[^\p{L}\p{N}_\s-]/gu, "")
    .trim()
    .replace(/\s/g, "-");
}
const md = new MarkdownIt({ html: false, linkify: true, typographer: false });
md.block.ruler.before(
  "fence",
  "math_block",
  (state, start, end, silent) => {
    const line = state.src
      .slice(state.bMarks[start] + state.tShift[start], state.eMarks[start])
      .trim();
    if (!line.startsWith("$$")) return false;
    if (silent) return true;
    let tex = line.slice(2),
      next = start + 1;
    if (tex.endsWith("$$") && tex.length >= 2) tex = tex.slice(0, -2);
    else {
      const lines = [tex];
      let closed = false;
      for (; next < end; next++) {
        const row = state.src.slice(
          state.bMarks[next] + state.tShift[next],
          state.eMarks[next],
        );
        if (row.trim().endsWith("$$")) {
          lines.push(row.slice(0, row.lastIndexOf("$$")));
          next++;
          closed = true;
          break;
        }
        lines.push(row);
      }
      if (!closed) throw new Error("Unclosed display equation");
      tex = lines.join("\n");
    }
    const token = state.push("math_block", "", 0);
    token.content = tex.trim();
    token.map = [start, next];
    state.line = next;
    return true;
  },
  { alt: ["paragraph", "reference", "blockquote", "list"] },
);
md.inline.ruler.before("escape", "math_inline", (state, silent) => {
  const start = state.pos;
  if (state.src[start] !== "$" || state.src[start + 1] === "$") return false;
  const end = state.src.indexOf("$", start + 1);
  if (end < 0) return false;
  if (!silent) {
    const token = state.push("math_inline", "", 0);
    token.content = state.src.slice(start + 1, end);
  }
  state.pos = end + 1;
  return true;
});
let equations = 0;
const renderMath = (tex, displayMode) => {
  equations++;
  return katex.renderToString(tex, {
    displayMode,
    throwOnError: true,
    trust: false,
    strict: "warn",
    output: "htmlAndMathml",
  });
};
md.renderer.rules.math_block = (tokens, i) =>
  '<div class="equation">' + renderMath(tokens[i].content, true) + "</div>\n";
md.renderer.rules.math_inline = (tokens, i) =>
  renderMath(tokens[i].content, false);
md.renderer.rules.heading_open = (tokens, i, options, env, self) => {
  const title = tokens[i + 1].content;
  const base = slug(title);
  const count = env.headingCounts.get(base) || 0;
  env.headingCounts.set(base, count + 1);
  const id = base + (count ? "-" + count : "");
  tokens[i].attrSet("id", id);
  env.headings.push({ title, slug: id, level: Number(tokens[i].tag.slice(1)) });
  return self.renderToken(tokens, i, options);
};
const originalLink =
  md.renderer.rules.link_open ||
  ((tokens, i, options, env, self) => self.renderToken(tokens, i, options));
md.renderer.rules.link_open = (tokens, i, options, env, self) => {
  const href = tokens[i].attrGet("href");
  if (href && !/^https?:|^mailto:/i.test(href)) {
    const [target, fragment = ""] = href.split("#");
    const resolved = target
      ? path.posix.normalize(
          path.posix.join(path.posix.dirname(env.source), decodeURI(target)),
        )
      : env.source;
    const docId = byPath.get(resolved);
    if (docId) {
      tokens[i].attrSet(
        "href",
        `#read=${encodeURIComponent(docId)}${fragment ? "&section=" + encodeURIComponent(fragment) : ""}`,
      );
      tokens[i].attrSet("data-reader", docId);
      if (fragment) tokens[i].attrSet("data-section", fragment);
    } else {
      const artifactId = artifactByPath.get(resolved);
      if (artifactId) {
        tokens[i].attrSet(
          "href",
          "#artifact=" + encodeURIComponent(artifactId),
        );
        tokens[i].attrSet("data-artifact", artifactId);
      } else
        tokens[i].attrSet(
          "href",
          "https://github.com/awmbw/Q-RAG/" +
            (resolved.endsWith("/") ? "tree" : "blob") +
            "/main/" +
            resolved +
            (fragment ? "#" + fragment : ""),
        );
    }
  }
  if (/^https?:/.test(tokens[i].attrGet("href") || "")) {
    tokens[i].attrSet("target", "_blank");
    tokens[i].attrSet("rel", "noopener noreferrer");
  }
  return originalLink(tokens, i, options, env, self);
};
md.renderer.rules.image = (tokens, i) => {
  const src = tokens[i].attrGet("src");
  const alt = md.utils.escapeHtml(tokens[i].content);
  const name = path.basename(src);
  const source = "paper/figures/" + name;
  if (
    ![
      "architecture.png",
      "quality_resources.png",
      "sampling_coverage.png",
    ].includes(name)
  )
    return `<p class="note">Figure available in the original document: ${alt}</p>`;
  fs.copyFileSync(path.join(root, source), path.join(out, "figures", name));
  return `<img loading="lazy" class="research-figure" src="/assets/journey/figures/${name}" alt="${alt}">`;
};
const artifactPaths = [
  "docs/research_report/evidence/final_audit.json",
  "docs/research_report/evidence/baseline_dev_001.json",
  "docs/research_report/evidence/embedding_batch_profile.json",
  "docs/research_report/evidence/quantum_reproduction_smokes.json",
  "configs/development_decision.json",
  "configs/final_matrix.json",
  "configs/preparation_control.json",
  "configs/splits/research_v1.json",
  "configs/splits/corpus_v1.json",
  "docs/research_report/annotation_sample.json",
  ...fs
    .readdirSync(path.join(root, "paper/results"))
    .filter((n) => n.endsWith(".json"))
    .sort()
    .map((n) => "paper/results/" + n),
];
const artifactByPath = new Map(
  artifactPaths.map((p, i) => [p, "evidence-" + i]),
);
function render(text, source = "docs/journey/content.cjs") {
  const env = { source, headings: [], headingCounts: new Map() };
  const html = md.render(text.replace(/<!--[\s\S]*?-->/g, ""), env);
  return { html, headings: env.headings };
}
function sections(source) {
  const lines = source.replace(/<!--[\s\S]*?-->/g, "").split("\n");
  const parts = [];
  let current = { title: "Introduction", slug: "", lines: [] };
  let counts = new Map();
  for (const line of lines) {
    const match = /^(#{1,3})\s+(.+)$/.exec(line);
    if (match) {
      if (current.lines.length) parts.push(current);
      const base = slug(match[2]);
      const count = counts.get(base) || 0;
      counts.set(base, count + 1);
      current = {
        title: match[2],
        slug: base + (count ? "-" + count : ""),
        lines: [line],
      };
    } else current.lines.push(line);
  }
  if (current.lines.length) parts.push(current);
  return parts.map((p) => ({
    ...p,
    text: p.lines
      .join("\n")
      .replace(/[`*$#]/g, "")
      .slice(0, 20000),
  }));
}
fs.mkdirSync(path.join(out, "figures"), { recursive: true });
const provenance = [];
for (const p of [
  "docs/journey/content.cjs",
  "scripts/build_journey.cjs",
  "tools/journey/package.json",
  "tools/journey/package-lock.json",
]) {
  provenance.push({
    path: p,
    sha256: hash(fs.readFileSync(path.join(root, p))),
  });
}
const docs = documents.map(([id, title, p]) => {
  const bytes = fs.readFileSync(path.join(root, p));
  provenance.push({ path: p, sha256: hash(bytes) });
  const text = bytes.toString();
  return {
    id,
    title,
    path: p,
    sha256: hash(bytes),
    ...render(text, p),
    sections: sections(text).map(({ lines, ...s }) => s),
  };
});
const docMap = new Map(docs.map((d) => [d.id, d]));
function deep(ref, unique) {
  const d = docMap.get(ref.doc);
  if (!d) throw Error("Unknown document " + ref.doc);
  let html = d.html;
  if (ref.section) {
    const heading = d.headings.find((h) => h.slug === ref.section);
    if (!heading) throw Error(`Missing section ${ref.doc}#${ref.section}`);
    const start = html.indexOf(`<h${heading.level} id="${heading.slug}"`);
    const after = html.slice(start + 1);
    const re = new RegExp(`<h[1-${heading.level}] id="`);
    const end = after.search(re);
    html = html.slice(start, end < 0 ? undefined : start + 1 + end);
  }
  // Source links open the complete in-site reader. Prefix headings to avoid duplicate DOM ids.
  html = html.replace(/ id="([^"]+)"/g, (_, id) => ` id="${unique}-${id}"`);
  return { ...ref, html, path: d.path, sha256: d.sha256 };
}
const chapters = content.chapters.map((c) => ({
  ...c,
  ...render(c.body),
  deep: c.deep.map((r, i) => deep(r, c.id + "-" + i)),
}));
const phases = content.phases.map((p) => ({
  ...p,
  deep: p.deep.map((r, i) => deep(r, "phase-" + p.id + "-" + i)),
}));
const artifacts = artifactPaths.map((p) => {
  const bytes = fs.readFileSync(path.join(root, p));
  provenance.push({ path: p, sha256: hash(bytes) });
  return {
    id: artifactByPath.get(p),
    path: p,
    sha256: hash(bytes),
    data: JSON.parse(bytes),
  };
});
const results = {};
for (const a of artifacts)
  if (a.path.startsWith("paper/results/"))
    results[path.basename(a.path, ".json")] = a.data;
const katexRoot = path.dirname(loadTool.resolve("katex/package.json"));
fs.copyFileSync(
  path.join(katexRoot, "dist/katex.min.css"),
  path.join(out, "katex.min.css"),
);
fs.copyFileSync(
  path.join(katexRoot, "LICENSE"),
  path.join(out, "KATEX-LICENSE.txt"),
);
fs.mkdirSync(path.join(out, "fonts"), { recursive: true });
for (const name of fs.readdirSync(path.join(katexRoot, "dist/fonts")))
  if (name.endsWith(".woff2"))
    fs.copyFileSync(
      path.join(katexRoot, "dist/fonts", name),
      path.join(out, "fonts", name),
    );
// Keep only the packaged woff2 sources; no external font request or unnecessary ttf/woff.
let css = fs.readFileSync(path.join(out, "katex.min.css"), "utf8");
css = css
  .replace(/,url\([^)]*\.woff\) format\("woff"\)/g, "")
  .replace(/,url\([^)]*\.ttf\) format\("truetype"\)/g, "");
fs.writeFileSync(path.join(out, "katex.min.css"), css);
const payload = {
  schema_version: 1,
  edition: "2026-11-12",
  scientific_results_date: "2026-11-10",
  chapters,
  phases,
  documents: docs,
  glossary: content.glossary,
  artifacts,
  results,
  provenance,
};
fs.writeFileSync(path.join(out, "content.json"), JSON.stringify(payload));
const receipt = {
  schema_version: 1,
  edition: payload.edition,
  chapters: chapters.length,
  phases: phases.length,
  documents: docs.length,
  glossary_terms: Object.keys(content.glossary).length,
  artifacts: artifacts.length,
  rendered_equations: equations,
  sources: provenance,
  content_sha256: hash(fs.readFileSync(path.join(out, "content.json"))),
  tools: {
    "markdown-it": loadTool("markdown-it/package.json").version,
    katex: loadTool("katex/package.json").version,
  },
  scope:
    "Presentation build only. No model inference, new scientific runs or altered scientific results.",
};
fs.writeFileSync(
  path.join(out, "manifest.json"),
  JSON.stringify(receipt, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    chapters: chapters.length,
    phases: phases.length,
    documents: docs.length,
    equations,
    bytes: fs.statSync(path.join(out, "content.json")).size,
  }),
);
