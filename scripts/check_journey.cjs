/* Functional/numerical checks in a DOM, not a rendered-browser layout test. */
const fs = require("node:fs"),
  path = require("node:path"),
  assert = require("node:assert/strict"),
  crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const loadTool = require("node:module").createRequire(
  path.join(root, "tools/journey/package.json"),
);
const { JSDOM, VirtualConsole } = loadTool("jsdom");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const bundle = JSON.parse(read("src/qrag_service/static/journey/content.json"));
const checks = [];
const pause = () => new Promise((r) => setTimeout(r, 3));
function setup(hash = "", broken = false) {
  const errors = [],
    vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push(e.message));
  const dom = new JSDOM(read("src/qrag_service/static/journey.html"), {
      url: "http://localhost:8767/journey" + hash,
      runScripts: "outside-only",
      virtualConsole: vc,
    }),
    w = dom.window,
    calls = [];
  w.matchMedia = () => ({ matches: true });
  w.CSS = {
    escape: (s) => String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => "\\" + c),
  };
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  w.HTMLDialogElement.prototype.close = function () {
    this.removeAttribute("open");
  };
  w.fetch = async (url) => {
    calls.push(url);
    return {
      ok: !broken,
      status: broken ? 503 : 200,
      json: async () => structuredClone(bundle),
    };
  };
  w.eval(read("src/qrag_service/static/journey.js"));
  const doc = w.document,
    id = (s) => doc.getElementById(s);
  return {
    dom,
    w,
    doc,
    id,
    errors,
    calls,
    click: (s) => id(s).click(),
    go: async (name) => {
      w.location.hash = "chapter=" + name;
      await pause();
    },
    input: (node, value, type = "input") => {
      node.value = value;
      node.dispatchEvent(new w.Event(type, { bubbles: true }));
    },
  };
}
async function test(name, fn) {
  await fn();
  checks.push(name);
}
(async () => {
  await test("All bundled references/artifacts match source hashes; no private data paths are allowed", () => {
    const manifest = JSON.parse(
      read("src/qrag_service/static/journey/manifest.json"),
    );
    for (const source of manifest.sources) {
      assert(
        !/(\.private|LEARNING_LOG|midsem|\.env|data\/processed)/.test(
          source.path,
        ),
      );
      assert.equal(
        crypto
          .createHash("sha256")
          .update(fs.readFileSync(path.join(root, source.path)))
          .digest("hex"),
        source.sha256,
        source.path + " needs rebuild",
      );
    }
    assert.equal(
      crypto
        .createHash("sha256")
        .update(read("src/qrag_service/static/journey/content.json"))
        .digest("hex"),
      manifest.content_sha256,
    );
    assert.equal(bundle.documents.length, 43);
    assert.equal(bundle.phases.length, 10);
    assert(manifest.rendered_equations > 60);
    assert(
      bundle.documents
        .find((d) => d.id === "manuscript")
        .html.includes("katex"),
    );
    for (const d of bundle.documents) {
      const targets = [
        ...d.html.matchAll(
          /data-reader="([^"]+)"(?: data-section="([^"]+)")?/g,
        ),
      ];
      for (const [, id, section] of targets) {
        const target = bundle.documents.find((x) => x.id === id);
        assert(target, id);
        if (section)
          assert(
            target.headings.some((h) => h.slug === section),
            id + "#" + section,
          );
      }
    }
  });
  const t = setup();
  await pause();
  await test("Ten chapter navigation, graceful model-free boot and keyboard controls", async () => {
    assert.equal(t.doc.querySelectorAll("#chapter-nav a").length, 10);
    assert.match(t.id("chapter-title").textContent, /defensible answer/);
    assert.deepEqual(t.calls, ["/assets/journey/content.json"]);
    await t.go("state");
    assert.match(t.id("chapter-title").textContent, /bounded scope/);
    t.id("chapter").dispatchEvent(
      new t.w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
    );
    await pause();
    assert.match(t.id("chapter-title").textContent, /hypothesis/);
  });
  await test("Guided/deep modes expose the same full references; focus and review answers work", async () => {
    await t.go("foundations");
    assert(t.doc.querySelectorAll(".deep-reading").length >= 8);
    assert(!t.doc.querySelector(".deep-reading").open);
    t.click("mode-deep");
    assert([...t.doc.querySelectorAll(".deep-reading")].every((x) => x.open));
    t.click("mode-guided");
    assert([...t.doc.querySelectorAll(".deep-reading")].every((x) => !x.open));
    t.click("focus-toggle");
    assert(t.doc.body.classList.contains("focus-view"));
    t.click("focus-toggle");
    assert(!t.doc.body.classList.contains("focus-view"));
    assert.match(
      t.doc.querySelector(".review-section").textContent,
      /exact MILP optimum/,
    );
  });
  await test("Objective toy reproduces checked energies and signed evidence contribution", async () => {
    const table = t.doc.querySelector(".widget table");
    assert.match(table.textContent, /-0.92/);
    assert.match(table.textContent, /-1.40/);
    assert.match(t.doc.querySelector(".widget-output").textContent, /A \+ C/);
    const gamma = t.doc.querySelector('[aria-label="Toy evidence weight γ"]');
    t.input(gamma, 1);
    assert.match(table.textContent, /-2.20/);
  });
  await test("Every phase has its need, math, outcome, boundary and valid in-site deep content", async () => {
    await t.go("implementation");
    for (const p of bundle.phases) {
      t.click("phase-tab-" + p.id);
      assert.equal(
        t.doc.querySelector("[role=tab][aria-selected=true]").id,
        "phase-tab-" + p.id,
      );
      assert.match(t.id("phase-panel").textContent, /MATHEMATICS/);
      assert.match(t.id("phase-panel").textContent, /BOUNDARY/);
      assert(
        t.doc.querySelector(".deep-reading .prose").textContent.length > 100,
      );
    }
  });
  await test("MILP binary truth table and fractional relaxation have different valid bounds", () => {
    t.click("phase-tab-baseline");
    const a = t.doc.querySelector('[aria-label="xᵢ"]'),
      b = t.doc.querySelector('[aria-label="xⱼ"]');
    for (const [x, y, p] of [
      [0, 0, 0],
      [0, 1, 0],
      [1, 0, 0],
      [1, 1, 1],
    ]) {
      t.input(a, x, "change");
      t.input(b, y, "change");
      assert.match(
        t.doc.querySelector(".widget-output").textContent,
        new RegExp("Forced product y = " + p),
      );
    }
    t.input(a, 0.5, "change");
    t.input(b, 0.5, "change");
    assert.match(
      t.doc.querySelector(".widget-output").textContent,
      /\[0, 0.5\]/,
    );
  });
  await test("Ising toy reproduces binary energies; penalty illustration becomes all-pairs", () => {
    t.click("phase-tab-e");
    const a = t.doc.querySelector('[aria-label="Bit x₀"]'),
      b = t.doc.querySelector('[aria-label="Bit x₁"]');
    t.input(a, 1, "change");
    t.input(b, 1, "change");
    assert.match(
      t.doc.querySelector(".widget-output").textContent,
      /Binary E\(x\) = -1.3000 · Ising H\(z\) = -1.3000/,
    );
    assert.match(
      t.doc.querySelectorAll(".widget-output")[1].textContent,
      /22 semantic.*45 possible pairs/s,
    );
    assert.match(
      t.doc.querySelectorAll(".widget-output")[1].textContent,
      /45 encoded pairs/,
    );
  });
  await test("Global phase cannot alter basis-start probabilities; preparation changes sensitivity and preserves norm", () => {
    const math = t.w.QragJourneyMath;
    for (const beta of [0, 0.2, 0.61, 1.2]) {
      const a = math.probabilities(0, beta, false),
        b = math.probabilities(1.7, beta, false);
      assert(Math.abs(a[0] - b[0]) < 1e-12);
      assert(Math.abs(a[0] + a[1] - 1) < 1e-12);
    }
    const a = math.probabilities(0.1, 0.61, true),
      b = math.probabilities(1.7, 0.61, true);
    assert(Math.abs(a[0] - b[0]) > 0.1);
    assert(Math.abs(b[0] + b[1] - 1) < 1e-12);
    const kind = t.doc.querySelector('[aria-label="Initial state"]');
    t.input(kind, "prepared", "change");
    assert.match(
      t.doc.querySelectorAll(".widget-output")[2].textContent,
      /Relative phases/,
    );
  });
  await test("All toy sparsifiers and epsilon settings obey the full-objective bound", () => {
    t.click("phase-tab-f");
    const rule = t.doc.querySelector('[aria-label="Retention rule"]'),
      fraction = t.doc.querySelector('[aria-label="Retained fraction"]'),
      eps = t.doc.querySelector(
        '[aria-label="Sparse suboptimality allowance ε"]',
      );
    for (const r of ["absolute", "evidence", "degree", "random"])
      for (const f of [0.25, 0.5, 0.75, 1])
        for (const e of [0, 0.5, 1]) {
          t.input(rule, r, "change");
          t.input(fraction, f);
          t.input(eps, e);
          const text = t.doc.querySelector(".widget-output").textContent;
          const m = /gap ([\d.]+) ≤ 2δ \+ ε = ([\d.]+)/.exec(text);
          assert(m);
          assert(parseFloat(m[1]) <= parseFloat(m[2]) + 0.001, text);
          assert.match(
            text,
            new RegExp("Retained " + Math.floor(f * 9) + " / 9"),
          );
        }
  });
  await test("Sampling combinatorics and controls reproduce 252 subsets / 98.29% optimum coverage", () => {
    t.click("phase-tab-g");
    const math = t.w.QragJourneyMath;
    assert.equal(math.choose(10, 5), 252);
    assert(Math.abs(math.coverage(10, 5, 1024) - 0.9829) < 0.0001);
    assert(Math.abs(math.coverage(16, 5, 1024) - 0.209) < 0.0001);
    assert.match(t.doc.querySelector(".large-number").textContent, /98.29/);
    const s = t.doc.querySelector(
      '[aria-label="Independent feasible draws S"]',
    );
    t.input(s, 0);
    assert.match(
      t.doc.querySelector(".widget-output").textContent,
      /Enter a whole/,
    );
  });
  await test("All result conditions/datasets use exact recorded values and honest failure/resource denominators", async () => {
    await t.go("results");
    const dataset = t.doc.querySelector("[aria-label=Dataset]"),
      condition = t.doc.querySelector("[aria-label=Condition]");
    for (const d of ["hotpotqa", "musique"])
      for (const c of [
        "qwen15_count",
        "qwen3_count",
        "qwen15_tokens",
        "qwen3_tokens",
        "quantum",
        "prepared",
        "corpus25",
        "corpus50",
        "corpus100",
        "gatecap",
      ]) {
        t.input(dataset, d, "change");
        t.input(condition, c, "change");
        const a = bundle.results[`final_${d}_${c}_analysis`];
        assert(a);
        assert.equal(
          t.doc.querySelectorAll(".result-bar").length,
          Object.keys(a.table).length,
        );
        for (const [i, row] of Object.values(a.table).entries())
          assert.equal(
            t.doc.querySelectorAll(".bar-value")[i].textContent,
            row.answer_f1.toFixed(4),
          );
        assert.match(
          t.doc.querySelector(".result-finding").textContent,
          /failed records as zero/,
        );
      }
    t.input(dataset, "hotpotqa", "change");
    t.input(condition, "quantum", "change");
    assert.match(
      t.doc.querySelector(".ci-chart").getAttribute("aria-label"),
      /-0.0363/,
    );
  });
  await test("All 43 full documents and glossary are readable inside modal dialogs", () => {
    t.click("open-library");
    assert(t.id("reader-dialog").open);
    for (const doc of bundle.documents) {
      const b = [...t.id("reader-nav").querySelectorAll("button")].find(
        (b) => b.textContent === doc.title,
      );
      assert(b);
      b.click();
      assert.equal(t.id("reader-title").textContent, doc.title);
      assert(t.id("reader-content").textContent.length > 100);
    }
    t.doc.querySelector("[data-close=reader-dialog]").click();
    t.click("open-glossary");
    t.input(t.id("glossary-search"), "embedding cache");
    assert.match(t.id("glossary-list").textContent, /Persist already computed/);
    t.doc.querySelector("[data-close=glossary-dialog]").click();
  });
  await test("Search finds full derivations and treats untrusted query text as plain text", () => {
    t.input(t.id("journey-search"), "global phase");
    assert(t.id("search-results").querySelector("button"));
    t.id("search-results").querySelector("button").click();
    assert(t.id("reader-dialog").open);
    assert.match(t.id("reader-content").textContent, /phase/);
    t.doc.querySelector("[data-close=reader-dialog]").click();
    t.input(t.id("journey-search"), "<img src=x onerror=alert(1)>");
    assert.equal(t.id("search-results").querySelector("img"), null);
  });
  await test("Artifact viewer shows bundled hashes and literal JSON without executing values", async () => {
    await t.go("reproduce");
    t.doc.querySelector(".evidence-browser button").click();
    assert(t.id("evidence-dialog").open);
    assert.match(t.id("evidence-provenance").textContent, /SHA-256/);
    assert.match(t.id("evidence-content").textContent, /common_source_sha256/);
    assert.equal(t.id("evidence-content").children.length, 0);
    t.doc.querySelector("[data-close=evidence-dialog]").click();
  });
  await test("Deep links to chapters, phases and references work on first load; missing content has retry", async () => {
    for (const hash of [
      "#chapter=implementation&phase=e",
      "#read=foundations&section=qubo-and-ising-mapping",
    ]) {
      const x = setup(hash);
      await pause();
      if (hash.includes("read=")) {
        assert(x.id("reader-dialog").open);
        assert.match(x.id("chapter-title").textContent, /defensible answer/);
      } else
        assert.match(x.id("phase-panel").textContent, /quantum calculation/);
      assert.deepEqual(x.errors, []);
      x.dom.window.close();
    }
    const bad = setup("", true);
    await pause();
    assert.match(bad.id("chapter").textContent, /Retry loading/);
    bad.dom.window.close();
  });
  assert.deepEqual(t.errors, []);
  assert(t.calls.every((x) => x === "/assets/journey/content.json"));
  t.dom.window.close();
  console.log(
    JSON.stringify(
      {
        scope:
          "DOM and numerical checks; no browser layout or real neural inference claim",
        checks_passed: checks.length,
        checks,
      },
      null,
      2,
    ),
  );
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
