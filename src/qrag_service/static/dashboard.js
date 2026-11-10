"use strict";

const byId = (id) => document.getElementById(id);
const example = [
  {
    id: "s1",
    title: "Film A",
    text: "Film A was directed by Maya Rao in 1995.",
  },
  {
    id: "s2",
    title: "Maya Rao",
    text: "Maya Rao was born in India and later worked in Britain.",
  },
  {
    id: "s3",
    title: "Film B",
    text: "Film B was directed by Alex Sen in 2001.",
  },
  {
    id: "s4",
    title: "Film A release",
    text: "Film A premiered in Mumbai in 1995.",
  },
];
const names = {
  relevance: "Relevance ranking",
  milp: "MILP selection",
  qaoa: "QAOA simulation",
  mmr: "MMR selection",
};
const form = byId("experiment-form");
const initialEmpty = byId("results").firstElementChild.cloneNode(true);
let hasResults = false;
let running = false;
let editorMode = "cards";

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function setStatus(message, state = "idle") {
  byId("status").textContent = message;
  byId("status").dataset.state = state;
  byId("run-state").dataset.state = state;
  byId("run-state").textContent = {
    idle: "NO RUN YET",
    running: "IN PROGRESS",
    completed: "COMPLETED",
    error: "CHECK INPUT / SERVICE",
    changed: "INPUTS CHANGED",
  }[state];
}

async function readiness() {
  try {
    const response = await fetch("/ready");
    const state = await response.json();
    if (!response.ok && response.status !== 503)
      throw new Error("Readiness unavailable");
    if (typeof state.ready !== "boolean")
      throw new Error("Invalid readiness response");
    byId("ready").dataset.state = state.ready ? "ready" : "cold";
    byId("ready-label").textContent = state.ready
      ? "Models ready · local"
      : "Local service · model cold";
  } catch {
    byId("ready").dataset.state = "offline";
    byId("ready-label").textContent = "Service unavailable";
  }
}

function parseSources() {
  let sources;
  try {
    sources = JSON.parse(byId("sources").value);
  } catch {
    throw new Error(
      "Sources must be valid JSON. Check commas, quotes and brackets.",
    );
  }
  if (!Array.isArray(sources) || !sources.length || sources.length > 100)
    throw new Error("Supply between 1 and 100 sources.");
  const ids = new Set();
  for (const [index, source] of sources.entries()) {
    if (!source || typeof source !== "object" || Array.isArray(source))
      throw new Error(
        `Source ${index + 1} must be an object with id, title and text.`,
      );
    if (
      Object.keys(source).some((key) => !["id", "title", "text"].includes(key))
    )
      throw new Error(
        `Source ${index + 1} accepts only id, title and text. Reference annotations are not inference inputs.`,
      );
    for (const [field, limit] of [
      ["id", 64],
      ["title", 256],
      ["text", 12000],
    ]) {
      if (
        typeof source[field] !== "string" ||
        !source[field].trim() ||
        source[field].trim().length > limit
      )
        throw new Error(
          `Source ${index + 1}: ${field} must contain 1–${limit.toLocaleString()} characters.`,
        );
    }
    const id = source.id.trim();
    if (ids.has(id))
      throw new Error(`Source IDs must be unique: “${id}” is repeated.`);
    ids.add(id);
  }
  if (
    sources.reduce((total, source) => total + source.text.trim().length, 0) >
    100000
  )
    throw new Error("Combined source text must not exceed 100,000 characters.");
  return sources;
}

function updateCount(count) {
  byId("source-count").textContent = String(count);
  byId("k").max = String(Math.min(10, count));
  byId("add-source").disabled = count >= 100 || running;
}

function writeSources(sources) {
  byId("sources").value = JSON.stringify(sources, null, 2);
  updateCount(sources.length);
}

function inputsChanged() {
  if (hasResults && !running)
    setStatus(
      "Inputs changed. The displayed answers belong to the previous comparison.",
      "changed",
    );
}

function renderSourceCards(sources) {
  byId("source-cards").replaceChildren();
  sources.forEach((source, index) => {
    const card = node("article", undefined, "source-card");
    const heading = node("div", undefined, "source-card-head");
    heading.append(
      node(
        "span",
        `SOURCE ${String(index + 1).padStart(2, "0")} / ${source.id}`,
        "source-id",
      ),
    );
    const remove = node("button", "×", "remove-source");
    remove.type = "button";
    remove.setAttribute(
      "aria-label",
      `Remove source ${index + 1}: ${source.title || source.id}`,
    );
    remove.disabled = sources.length === 1;
    remove.addEventListener("click", () => {
      sources.splice(index, 1);
      writeSources(sources);
      byId("k").value = String(
        Math.min(Number(byId("k").value) || 1, sources.length),
      );
      renderSourceCards(sources);
      inputsChanged();
    });
    heading.append(remove);
    const title = node("input");
    title.type = "text";
    title.value = source.title;
    title.maxLength = 256;
    title.setAttribute("aria-label", `Source ${index + 1} title`);
    const text = node("textarea");
    text.value = source.text;
    text.rows = 3;
    text.maxLength = 12000;
    text.setAttribute("aria-label", `Source ${index + 1} text`);
    title.addEventListener("input", () => {
      source.title = title.value;
      writeSources(sources);
    });
    text.addEventListener("input", () => {
      source.text = text.value;
      writeSources(sources);
    });
    card.append(heading, title, text);
    byId("source-cards").append(card);
  });
}

function setEditor(mode) {
  if (mode === "cards") {
    try {
      renderSourceCards(parseSources());
    } catch (error) {
      setStatus(error.message, "error");
      byId("sources").focus();
      return;
    }
  }
  editorMode = mode;
  for (const name of ["cards", "json"]) {
    const tab = byId(`${name}-tab`);
    tab.setAttribute("aria-selected", String(name === mode));
    tab.tabIndex = name === mode ? 0 : -1;
  }
  byId("source-cards").hidden = mode !== "cards";
  byId("json-editor").hidden = mode !== "json";
}

for (const mode of ["cards", "json"]) {
  const tab = byId(`${mode}-tab`);
  tab.addEventListener("click", () => setEditor(mode));
  tab.addEventListener("keydown", (event) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const next =
        event.key === "Home"
          ? "cards"
          : event.key === "End"
            ? "json"
            : mode === "cards"
              ? "json"
              : "cards";
      setEditor(next);
      byId(`${editorMode}-tab`).focus();
    }
  });
}

byId("sources").addEventListener("input", () => {
  try {
    updateCount(parseSources().length);
  } catch {
    byId("source-count").textContent = "?";
  }
});
byId("add-source").addEventListener("click", () => {
  try {
    const sources = parseSources();
    if (sources.length >= 100)
      throw new Error("The local comparison accepts at most 100 sources.");
    let number = sources.length + 1;
    while (sources.some((source) => source.id === `s${number}`)) number++;
    sources.push({
      id: `s${number}`,
      title: "New source",
      text: "Add your source text here.",
    });
    writeSources(sources);
    renderSourceCards(sources);
    inputsChanged();
    if (editorMode === "cards")
      byId("source-cards").lastElementChild.querySelector("input").focus();
    else byId("sources").focus();
  } catch (error) {
    setStatus(error.message, "error");
  }
});
for (const [id, delta] of [
  ["decrease-k", -1],
  ["increase-k", 1],
]) {
  byId(id).addEventListener("click", () => {
    byId("k").value = String(
      Math.max(
        1,
        Math.min(Number(byId("k").max), (Number(byId("k").value) || 1) + delta),
      ),
    );
    inputsChanged();
  });
}
form.addEventListener("input", inputsChanged);

function clearInspection() {
  hasResults = false;
  byId("results").replaceChildren(initialEmpty.cloneNode(true));
  byId("graph").replaceChildren();
  byId("graph").hidden = true;
  byId("graph-placeholder").hidden = false;
  byId("graph-edge-details").replaceChildren();
  byId("policy").textContent =
    "Selected sources show what the generator received. They do not prove which facts it used.";
}

byId("reset-example").addEventListener("click", () => {
  byId("question").value = "In which country was the director of Film A born?";
  writeSources(example.map((source) => ({ ...source })));
  byId("k").value = "2";
  document.querySelectorAll(".choices input").forEach((input) => {
    input.checked = input.value !== "mmr";
  });
  setEditor("cards");
  clearInspection();
  setStatus("Ready for an experiment.");
});

function svgNode(tag, attributes, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes))
    element.setAttribute(key, String(value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function graph(data, sources) {
  const svg = byId("graph");
  svg.replaceChildren();
  const allIds = Object.keys(data.mentions || {});
  const ids = (
    allIds.length
      ? allIds
      : [...new Set(data.edges.flatMap((edge) => [edge.source, edge.target]))]
  ).slice(0, 16);
  const titleFor = (id) =>
    sources.find((source) => source.id.trim() === id)?.title || id;
  byId("graph-placeholder").hidden = true;
  svg.hidden = false;
  if (!ids.length) {
    svg.append(
      svgNode(
        "text",
        {
          x: 320,
          y: 125,
          "text-anchor": "middle",
          fill: "#707368",
          "font-size": 13,
        },
        "No extracted entities in this candidate pool.",
      ),
    );
  } else {
    const positions = new Map(
      ids.map((id, index) => [
        id,
        {
          x:
            ids.length === 1
              ? 320
              : 320 +
                235 *
                  Math.cos(-Math.PI / 2 + (index * 2 * Math.PI) / ids.length),
          y:
            ids.length === 1
              ? 130
              : 125 +
                82 *
                  Math.sin(-Math.PI / 2 + (index * 2 * Math.PI) / ids.length),
        },
      ]),
    );
    for (const edge of data.edges) {
      const a = positions.get(edge.source),
        b = positions.get(edge.target);
      if (!a || !b) continue;
      const line = svgNode("line", {
        x1: a.x,
        y1: a.y,
        x2: b.x,
        y2: b.y,
        stroke: "#9ba9df",
        "stroke-width": 1.5,
      });
      line.append(
        svgNode(
          "title",
          {},
          `${titleFor(edge.source)} ↔ ${titleFor(edge.target)}: ${edge.entities.join(", ")}`,
        ),
      );
      svg.append(line);
    }
    for (const [id, position] of positions) {
      const connected = data.edges.some(
        (edge) => edge.source === id || edge.target === id,
      );
      const group = svgNode("g", {});
      group.append(
        svgNode("circle", {
          cx: position.x,
          cy: position.y,
          r: 11,
          fill: connected ? "#3553ed" : "#f0efe7",
          stroke: connected ? "#3553ed" : "#858a7a",
        }),
      );
      group.append(
        svgNode(
          "text",
          {
            x: position.x,
            y: position.y + 29,
            "text-anchor": "middle",
            fill: "#55584f",
            "font-size": 11,
            "font-family": "JetBrains Mono, monospace",
          },
          titleFor(id).length > 22
            ? titleFor(id).slice(0, 21) + "…"
            : titleFor(id),
        ),
      );
      group.append(svgNode("title", {}, `${id}: ${titleFor(id)}`));
      svg.append(group);
    }
  }
  const details = byId("graph-edge-details");
  details.replaceChildren();
  if (allIds.length > 16)
    details.append(
      node(
        "p",
        `Showing 16 of ${allIds.length} source nodes. All extracted links are listed below.`,
      ),
    );
  if (data.edges.length) {
    const disclosure = node("details");
    disclosure.append(
      node(
        "summary",
        `Inspect ${data.edges.length} potential ${data.edges.length === 1 ? "link" : "links"}`,
      ),
    );
    for (const edge of data.edges)
      disclosure.append(
        node(
          "p",
          `${titleFor(edge.source)} ↔ ${titleFor(edge.target)} · ${edge.entities.join(", ")}`,
        ),
      );
    details.append(disclosure);
  } else
    details.append(
      node(
        "p",
        "No shared extracted entities were found between these sources.",
      ),
    );
}

const decimal = (value, digits = 3) =>
  Number.isFinite(value) ? value.toFixed(digits) : "—";

function show(result, sources) {
  byId("results").replaceChildren();
  byId("policy").textContent =
    `${result.candidate_policy}. ${result.source_note}`;
  for (const row of result.results) {
    const card = node("article", undefined, "result-card");
    card.dataset.method = row.requested_method;
    const header = node("div", undefined, "result-card-heading");
    header.append(
      node(
        "span",
        names[row.requested_method] || row.requested_method,
        "result-method",
      ),
    );
    const badge = row.fallback
      ? "CLASSICAL FALLBACK"
      : row.actual_method === "qaoa"
        ? "SIMULATED"
        : row.optimal
          ? "CERTIFIED OPTIMUM"
          : row.solver_status.toUpperCase();
    header.append(
      node(
        "span",
        badge,
        `method-badge${row.actual_method === "qaoa" ? " quantum" : ""}`,
      ),
    );
    card.append(header, node("div", row.answer || "(Empty answer)", "answer"));
    const chips = node("div", undefined, "source-chips");
    for (const source of row.supplied_sources)
      chips.append(node("span", source.title, "source-chip"));
    card.append(chips);
    const stats = node("div", undefined, "stats");
    for (const [label, value] of [
      ["Context tokens", row.context_tokens],
      ["Selection", decimal(row.selection_seconds) + " s"],
      ["Generation", decimal(row.generation_seconds) + " s"],
      ["Objective", decimal(row.full_energy)],
    ]) {
      const box = node("div");
      box.append(node("strong", String(value)), node("span", label));
      stats.append(box);
    }
    card.append(stats);
    if (row.generation_reused)
      card.append(
        node(
          "p",
          "Same ordered context: deterministic answer reused; no extra generation call.",
          "fine-print",
        ),
      );
    if (row.fallback)
      card.append(
        node(
          "p",
          `Actual method: ${names[row.actual_method] || row.actual_method}. ${row.fallback.reason}`,
          "warning",
        ),
      );
    const context = node("details");
    context.append(
      node(
        "summary",
        `Inspect the ${row.supplied_sources.length} supplied sources`,
      ),
    );
    for (const source of row.supplied_sources) {
      const detail = node("div", undefined, "source-detail");
      detail.append(
        node("h5", `${source.id} / ${source.title}`),
        node(
          "p",
          sources.find((item) => item.id.trim() === source.id)?.text ||
            "Source text unavailable.",
        ),
      );
      context.append(detail);
    }
    card.append(context);
    if (row.quantum_resources?.line) {
      const resources = row.quantum_resources;
      const details = node("details");
      details.append(node("summary", "Simulation & complete circuit cost"));
      const costs = node("div", undefined, "circuit-stats");
      for (const [label, value] of [
        ["Feasible shots", `${resources.feasible_shots} / ${resources.shots}`],
        ["Line 2Q gates", resources.line.two_qubit_gates],
        ["Depth", resources.line.depth],
      ])
        costs.append(node("span", `${label}: ${value}`));
      details.append(
        costs,
        node(
          "p",
          "Synthetic line compilation, not physical quantum hardware.",
          "fine-print",
        ),
      );
      card.append(details);
    }
    byId("results").append(card);
  }
  graph(result.graph, sources);
  hasResults = true;
  setStatus(
    `Completed in ${decimal(result.wall_seconds, 2)} s · ${result.backend.generator}`,
    "completed",
  );
}

async function responseJSON(response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail
          .map(
            (item) => `${item.loc?.slice(1).join(".") || "Input"}: ${item.msg}`,
          )
          .join(" · ")
      : detail || `Request failed (${response.status}).`;
    throw new Error(
      typeof message === "string" ? message : JSON.stringify(message),
    );
  }
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (running) return;
  try {
    const sources = parseSources();
    const question = byId("question").value.trim();
    const k = Number(byId("k").value);
    const methods = [
      ...document.querySelectorAll(".choices input:checked"),
    ].map((input) => input.value);
    if (!question)
      throw new Error("Enter a question before comparing methods.");
    if (!Number.isInteger(k) || k < 1 || k > Math.min(10, sources.length))
      throw new Error(
        `Select between 1 and ${Math.min(10, sources.length)} sources per method.`,
      );
    if (!methods.length) throw new Error("Choose at least one selector.");
    running = true;
    clearInspection();
    byId("results-panel").setAttribute("aria-busy", "true");
    form.classList.add("is-running");
    const disabledBefore = new Map(
      [...form.elements].map((element) => [element, element.disabled]),
    );
    disabledBefore.forEach((_, element) => {
      element.disabled = true;
    });
    byId("run-label").textContent = "Comparing methods…";
    byId("run-arrow").textContent = "···";
    byId("results").querySelector("h4").textContent =
      "The selectors are at work.";
    byId("results").querySelector("p").textContent =
      "The first run may take longer while local model weights load.";
    try {
      setStatus("Submitting your local comparison…", "running");
      const job = await responseJSON(
        await fetch("/jobs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, sources, k, methods }),
        }),
      );
      const waitStarted = Date.now();
      for (;;) {
        await new Promise((resolve) => setTimeout(resolve, 700));
        const status = await responseJSON(await fetch(job.status_url));
        if (status.status === "completed") {
          show(status.result, sources);
          break;
        }
        if (["failed", "timed_out", "interrupted"].includes(status.status))
          throw new Error(
            status.error?.message || `The local job ${status.status}.`,
          );
        if (Date.now() - waitStarted > 180000)
          throw new Error(
            `Stopped waiting after three minutes. Job ${job.id} may still be running; inspect it through the API.`,
          );
        setStatus(
          status.status === "queued"
            ? "Waiting for the local inference worker…"
            : "Comparing selectors and generating answers…",
          "running",
        );
      }
    } finally {
      disabledBefore.forEach((disabled, element) => {
        element.disabled = disabled;
      });
      running = false;
      form.classList.remove("is-running");
      byId("results-panel").setAttribute("aria-busy", "false");
      byId("run-label").textContent = "Compare methods";
      byId("run-arrow").textContent = "↗";
      readiness();
    }
  } catch (error) {
    setStatus(
      error.message || "The comparison could not be completed.",
      "error",
    );
    if (!hasResults) {
      byId("results").replaceChildren(initialEmpty.cloneNode(true));
      byId("results").querySelector("h4").textContent =
        "Let’s check the experiment.";
      byId("results").querySelector("p").textContent =
        "Review the message above, adjust the inputs if needed, then try again.";
    }
  }
});

writeSources(example.map((source) => ({ ...source })));
renderSourceCards(parseSources());
readiness();
