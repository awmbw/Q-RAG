const fs = require("node:fs");
const assert = require("node:assert/strict");
const { JSDOM, VirtualConsole } = require("jsdom");
const root = require("node:path").resolve(__dirname, "..");
const html = fs.readFileSync(
  root + "/src/qrag_service/static/index.html",
  "utf8",
);
const js = fs.readFileSync(
  root + "/src/qrag_service/static/dashboard.js",
  "utf8",
);
const checks = [];
const pause = () => new Promise((resolve) => setTimeout(resolve, 5));
function fixture(options = {}) {
  const row = {
    requested_method: "relevance",
    actual_method: "relevance",
    fallback: null,
    answer: "India",
    supplied_sources: [
      { id: "s1", title: "Film A" },
      { id: "s2", title: "Maya Rao" },
    ],
    context_tokens: 40,
    input_tokens: 70,
    selection_seconds: 0.001,
    generation_seconds: 0.1,
    generation_reused: false,
    full_energy: -1.2,
    solver_status: "ranking",
    optimal: false,
    quantum_resources: null,
  };
  const quantum = {
    ...row,
    requested_method: "qaoa",
    actual_method: "qaoa",
    solver_status: "sampled",
    quantum_resources: {
      feasible_shots: 1024,
      shots: 1024,
      line: { two_qubit_gates: 42, depth: 25 },
    },
  };
  if (options.fallback)
    Object.assign(quantum, {
      actual_method: "milp",
      quantum_resources: null,
      optimal: true,
      fallback: {
        used: true,
        reason: "Synthetic solver failure for this unit test",
      },
    });
  if (options.untrusted) row.answer = "<img src=x onerror=alert(1)>";
  return {
    candidate_policy: "Common candidate pool",
    source_note: "Context is not a citation guarantee.",
    results: [row, quantum],
    graph: {
      mentions: { s1: [], s2: [], s3: [], s4: [] },
      edges: [{ source: "s1", target: "s2", entities: ["Maya Rao"] }],
    },
    wall_seconds: 0.2,
    backend: { generator: "synthetic-test-model" },
  };
}
function setup(options = {}) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (error) => errors.push(error.message));
  const dom = new JSDOM(html, {
    url: "http://localhost:8766",
    runScripts: "outside-only",
    virtualConsole: vc,
  });
  const w = dom.window,
    calls = [];
  w.setTimeout = (callback) => {
    queueMicrotask(callback);
    return 1;
  };
  let polls = 0;
  const reply = (data, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  });
  w.fetch = async (url, init) => {
    calls.push({ url, init });
    if (url === "/ready")
      return reply({ ready: !options.cold }, options.cold ? 503 : 200);
    if (url === "/jobs") {
      if (options.httpError)
        return reply(
          {
            detail: [
              { loc: ["body", "sources"], msg: "Synthetic validation failure" },
            ],
          },
          422,
        );
      return reply({ id: "unit-test", status_url: "/jobs/unit-test" }, 202);
    }
    polls++;
    if (polls === 1) return reply({ status: "queued" });
    if (options.failure)
      return reply({
        status: "timed_out",
        error: { message: "Synthetic deadline exceeded" },
      });
    return reply({ status: "completed", result: fixture(options) });
  };
  w.eval(js);
  const id = (value) => w.document.getElementById(value);
  const click = (value) => id(value).click();
  const input = (value, text) => {
    id(value).value = text;
    id(value).dispatchEvent(new w.Event("input", { bubbles: true }));
  };
  const submit = async () => {
    id("experiment-form").dispatchEvent(
      new w.Event("submit", { bubbles: true, cancelable: true }),
    );
    for (let i = 0; i < 100; i++) {
      await pause();
      if (id("results-panel").getAttribute("aria-busy") === "false") break;
    }
    assert.equal(id("results-panel").getAttribute("aria-busy"), "false");
    assert.deepEqual(errors, []);
  };
  return { w, dom, id, click, input, submit, calls };
}
async function test(name, run) {
  await run();
  checks.push(name);
}
(async () => {
  await test("Initial source cards, JSON and count agree; ready/cold readiness is truthful", async () => {
    for (const cold of [false, true]) {
      const t = setup({ cold });
      await pause();
      assert.equal(t.w.document.querySelectorAll(".source-card").length, 4);
      assert.equal(JSON.parse(t.id("sources").value).length, 4);
      assert.equal(t.id("source-count").textContent, "4");
      assert.equal(t.id("ready").dataset.state, cold ? "cold" : "ready");
      await pause();
      t.dom.window.close();
    }
  });
  await test("Card edits survive a JSON round trip; source removal clamps k", async () => {
    const t = setup();
    const field = t.w.document.querySelector(".source-card input");
    field.value = "Edited title";
    field.dispatchEvent(new t.w.Event("input", { bubbles: true }));
    t.click("json-tab");
    assert.equal(JSON.parse(t.id("sources").value)[0].title, "Edited title");
    t.click("cards-tab");
    assert.equal(
      t.w.document.querySelector(".source-card input").value,
      "Edited title",
    );
    t.id("k").value = "4";
    t.w.document.querySelector(".remove-source").click();
    assert.equal(t.id("k").value, "3");
    assert.equal(t.id("source-count").textContent, "3");
    await pause();
    t.dom.window.close();
  });
  await test("Add/remove sources, stepper and reset preserve a valid example", async () => {
    const t = setup();
    t.click("add-source");
    assert.equal(t.id("source-count").textContent, "5");
    assert.equal(t.w.document.querySelectorAll(".source-card").length, 5);
    t.click("increase-k");
    assert.equal(t.id("k").value, "3");
    t.click("decrease-k");
    assert.equal(t.id("k").value, "2");
    t.click("reset-example");
    assert.equal(t.id("source-count").textContent, "4");
    assert.equal(t.id("k").value, "2");
    await pause();
    t.dom.window.close();
  });
  await test("Invalid JSON blocks submission and keeps JSON editor available", async () => {
    const t = setup();
    t.click("json-tab");
    t.input("sources", "{bad");
    t.click("cards-tab");
    assert.equal(t.id("json-editor").hidden, false);
    await t.submit();
    assert.match(t.id("status").textContent, /valid JSON/);
    assert.equal(t.calls.filter((c) => c.url === "/jobs").length, 0);
    assert.equal(t.id("run").disabled, false);
    await pause();
    t.dom.window.close();
  });
  await test("Duplicate IDs, reference fields and missing methods fail before a request", async () => {
    for (const kind of ["duplicate", "gold", "methods"]) {
      const t = setup();
      const sources = JSON.parse(t.id("sources").value);
      if (kind === "duplicate") sources[1].id = sources[0].id;
      if (kind === "gold") sources[0].is_relevant = true;
      if (kind === "methods")
        t.w.document
          .querySelectorAll(".choices input")
          .forEach((i) => (i.checked = false));
      t.input("sources", JSON.stringify(sources));
      await t.submit();
      assert.equal(t.id("run-state").dataset.state, "error");
      assert.equal(t.calls.filter((c) => c.url === "/jobs").length, 0);
      await pause();
      t.dom.window.close();
    }
  });
  await test("Completion renders actual answers, context text, costs, graph and accessible links", async () => {
    const t = setup();
    await t.submit();
    assert.equal(t.id("run-state").textContent, "COMPLETED");
    assert.equal(t.w.document.querySelectorAll(".result-card").length, 2);
    assert.equal(t.w.document.querySelector(".answer").textContent, "India");
    assert.match(
      t.w.document.querySelector(".source-detail").textContent,
      /directed by Maya Rao/,
    );
    assert.equal(t.w.document.querySelectorAll("#graph circle").length, 4);
    assert.match(t.id("graph-edge-details").textContent, /Maya Rao/);
    assert.match(
      t.w.document.querySelector(".circuit-stats").textContent,
      /42/,
    );
    const body = JSON.parse(t.calls.find((c) => c.url === "/jobs").init.body);
    assert.deepEqual(body.methods, ["relevance", "milp", "qaoa"]);
    assert.equal(body.k, 2);
    assert.equal(t.id("run").disabled, false);
    t.input("question", "Changed?");
    assert.equal(t.id("run-state").textContent, "INPUTS CHANGED");
    await pause();
    t.dom.window.close();
  });
  await test("Fallback displays the actual classical method; untrusted answer is text, never markup", async () => {
    const t = setup({ fallback: true, untrusted: true });
    await t.submit();
    assert.equal(t.w.document.querySelectorAll(".result-card img").length, 0);
    assert.match(t.w.document.querySelector(".answer").textContent, /<img/);
    assert.match(t.id("results").textContent, /CLASSICAL FALLBACK/);
    assert.match(t.id("results").textContent, /Actual method: MILP/);
    await pause();
    t.dom.window.close();
  });
  await test("Backend validation and terminal failure re-enable controls and report real errors", async () => {
    for (const options of [{ httpError: true }, { failure: true }]) {
      const t = setup(options);
      await t.submit();
      assert.equal(t.id("run-state").dataset.state, "error");
      assert.match(t.id("status").textContent, /Synthetic/);
      assert.equal(t.id("run").disabled, false);
      assert.equal(t.id("question").disabled, false);
      await pause();
      t.dom.window.close();
    }
  });
  await test("Arrow-key tab navigation preserves selection and focus", async () => {
    const t = setup();
    t.id("cards-tab").dispatchEvent(
      new t.w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
    );
    assert.equal(t.id("json-tab").getAttribute("aria-selected"), "true");
    assert.equal(t.w.document.activeElement.id, "json-tab");
    await pause();
    t.dom.window.close();
  });
  const receipt = {
    scope:
      "jsdom DOM behavior checks with explicitly synthetic API fixtures; not a browser layout or real-model test",
    checks,
    passed: checks.length,
  };
  fs.mkdirSync(root + "/results/dashboard_redesign_qa", { recursive: true });
  fs.writeFileSync(
    root + "/results/dashboard_redesign_qa/dom_checks.json",
    JSON.stringify(receipt, null, 2) + "\n",
  );
  console.log(JSON.stringify(receipt, null, 2));
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
