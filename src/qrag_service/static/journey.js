"use strict";
/* All explanatory HTML is rendered at build time from allowlisted repository files.
   User search terms and artifact values are always inserted as text, never markup. */
(() => {
  const $ = (id) => document.getElementById(id);
  const el = (tag, text, cls) => {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = text;
    if (cls) n.className = cls;
    return n;
  };
  const button = (text, action) => {
    const b = el("button", text);
    b.type = "button";
    if (action) b.addEventListener("click", action);
    return b;
  };
  const svg = (tag, attrs = {}, text) => {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const fmt = (n, d = 4) => (Number.isFinite(n) ? n.toFixed(d) : "—");
  const reduceMotion = () =>
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const scroll = (n) =>
    n?.scrollIntoView?.({
      block: "start",
      behavior: reduceMotion() ? "instant" : "smooth",
    });
  const trustedHTML = (n, html) => {
    n.innerHTML = html;
    for (const table of n.querySelectorAll("table")) {
      const wrap = el("div", undefined, "table-scroll");
      table.replaceWith(wrap);
      wrap.append(table);
    }
  };
  const state = {
    data: null,
    index: 0,
    phase: "baseline",
    deep: false,
    visited: new Set(),
    reader: null,
    timer: null,
  };
  const pairs = (n) => (n * (n - 1)) / 2;
  const choose = (n, k) => {
    k = Math.min(k, n - k);
    let m = 1;
    for (let i = 1; i <= k; i++) m = (m * (n - k + i)) / i;
    return Math.round(m);
  };
  const coverage = (n, k, shots) => {
    const m = choose(n, k);
    return m === 1 ? 1 : -Math.expm1(shots * Math.log1p(-1 / m));
  };
  const energy = (x, a, edges) =>
    x.reduce((sum, b, i) => sum + b * a[i], 0) +
    edges.reduce((sum, [i, j, b]) => sum + b * x[i] * x[j], 0);
  const probabilities = (gamma, beta, prepared) => {
    const theta = prepared ? Math.PI / 4 : 0,
      c = Math.cos(beta),
      s = Math.sin(beta),
      u = Math.cos(theta),
      v = Math.sin(theta);
    // E10=-1, E01=-0.5; amplitudes after exp(-i beta X) in the one-excitation subspace.
    const a = [u * Math.cos(gamma), u * Math.sin(gamma)],
      b = [v * Math.cos(gamma / 2), v * Math.sin(gamma / 2)];
    const z0 = [c * a[0] + s * b[1], c * a[1] - s * b[0]],
      z1 = [c * b[0] + s * a[1], c * b[1] - s * a[0]];
    return [z0[0] ** 2 + z0[1] ** 2, z1[0] ** 2 + z1[1] ** 2];
  };
  // Exposed pure calculations support numerical regression checks, not a research API.
  window.QragJourneyMath = Object.freeze({
    choose,
    coverage,
    energy,
    probabilities,
  });
  function widget(title, measured = false) {
    const box = el("section", undefined, "widget");
    const label = el(
      "span",
      measured
        ? "RECORDED RESEARCH · SAVED ARTIFACTS"
        : "ILLUSTRATIVE EXAMPLE · LOCAL CALCULATION",
      `widget-label${measured ? " measured" : ""}`,
    );
    box.append(label, el("h3", title));
    return box;
  }
  function output(box) {
    const n = el("div", undefined, "widget-output");
    n.setAttribute("role", "status");
    n.setAttribute("aria-live", "polite");
    box.append(n);
    return n;
  }
  function controls(box) {
    const c = el("div", undefined, "widget-controls");
    box.append(c);
    return c;
  }
  function range(parent, label, min, max, value, step = 1) {
    const l = el("label"),
      name = el("span", label),
      v = el("output"),
      input = el("input");
    input.type = "range";
    input.min = min;
    input.max = max;
    input.step = step;
    input.value = value;
    input.setAttribute("aria-label", label);
    name.append(" ", v);
    l.append(name, input);
    parent.append(l);
    const sync = () => (v.value = String(Number(input.value)));
    input.addEventListener("input", sync);
    sync();
    return input;
  }
  function select(parent, label, options, value) {
    const l = el("label", label),
      s = el("select");
    s.setAttribute("aria-label", label);
    for (const [v, t] of options) {
      const o = el("option", t);
      o.value = v;
      s.append(o);
    }
    s.value = value;
    l.append(s);
    parent.append(l);
    return s;
  }
  function disclaimer(box, text) {
    box.append(el("p", text, "disclaimer"));
  }
  const widgets = {};
  widgets.pipeline = () => {
    const box = widget("One question. Nine connected operations.");
    const steps = [
      [
        "01",
        "Question & boundaries",
        "Ask where the director was born. Separate usable question/source text from reference answers and supporting labels.",
      ],
      [
        "02",
        "Traceable chunks",
        "Split candidate documents within the embedding token limit. Keep original character offsets and sentence identities.",
      ],
      [
        "03",
        "Vectors & relevance",
        "Use frozen MiniLM, normalized chunk aggregation and cached vectors. Similarity estimates relatedness, not truth.",
      ],
      [
        "04",
        "Potential bridges",
        "Shared names/titles and query anchors form an entity-link proxy. Film A and Maya Rao may connect; the relationship is not semantically certified.",
      ],
      [
        "05",
        "Common objective",
        "Balance relevance, redundancy and possible complementarity, subject to a count or separate classical token budget.",
      ],
      [
        "06",
        "Select a subset",
        "Use ranking, a classical optimizer or simulated QAOA. Only selected sources reach the generator.",
      ],
      [
        "07",
        "Generate an answer",
        "Apply the shared prompt and frozen generator. The fictional evidence chain supports India; this animation does not call a model.",
      ],
      [
        "08",
        "Evaluate separately",
        "After generation, use reference annotations for answer EM/F1 and supporting-document metrics. The live demo does not automatically have these labels.",
      ],
      [
        "09",
        "Record & inspect",
        "Save identities, selections, predictions, failures and resources. Rebuild statistics before interpreting the claim.",
      ],
    ];
    const track = el("div", undefined, "pipeline-track"),
      detail = el("div", undefined, "flow-description"),
      row = el("div", undefined, "flow-controls");
    let active = 0;
    const buttons = steps.map(([num, title], i) => {
      const b = button("", () => show(i));
      b.append(el("small", num), el("span", title));
      track.append(b);
      return b;
    });
    function show(i) {
      active = i;
      buttons.forEach((b, j) => {
        b.classList.toggle("active", i === j);
        b.setAttribute("aria-pressed", String(i === j));
      });
      detail.replaceChildren(el("h4", steps[i][1]), el("p", steps[i][2]));
    }
    const play = button("Play the flow", () => {
      if (state.timer) {
        clearInterval(state.timer);
        state.timer = null;
        play.textContent = "Play the flow";
        return;
      }
      if (reduceMotion()) {
        show((active + 1) % steps.length);
        return;
      }
      play.textContent = "Pause";
      state.timer = setInterval(() => show((active + 1) % steps.length), 2000);
    });
    row.append(
      play,
      button("Next operation →", () => show((active + 1) % steps.length)),
    );
    box.append(track, detail, row);
    show(0);
    disclaimer(
      box,
      "This is a teaching trace. No new retrieval, model inference or quantum job is launched.",
    );
    return box;
  };
  widgets.objective = () => {
    const box = widget("Choose a set, then inspect its energy."),
      c = controls(box),
      beta = range(c, "Redundancy weight β", 0, 1, 0.5, 0.05),
      gamma = range(c, "Toy evidence weight γ", 0, 1, 0, 0.05);
    const sources = el("div", undefined, "toy-passages"),
      checks = [];
    for (const [i, title, text] of [
      [0, "A · Relevant passage", "r = 0.8 · vector (0.8, 0.6)"],
      [1, "B · Near duplicate", "r = 0.6 · vector (0.6, 0.8)"],
      [2, "C · Different direction", "r = 0.6 · vector (0.6, −0.8)"],
    ]) {
      const label = el("label"),
        check = el("input");
      check.type = "checkbox";
      check.checked = i < 2;
      check.setAttribute("aria-label", "Select toy passage " + title[0]);
      checks.push(check);
      label.append(check, el("strong", title), el("span", text));
      sources.append(label);
    }
    box.append(sources);
    const table = el("table", undefined, "data-table"),
      out = output(box);
    box.insertBefore(table, out);
    function update() {
      const b = +beta.value,
        g = +gamma.value;
      const candidates = [
          [0, 1],
          [0, 2],
          [1, 2],
        ],
        r = [0.8, 0.6, 0.6],
        similarity = [0.96, 0, 0],
        comp = [0, 0.8, 0.2];
      const rows = candidates.map(([i, j], k) => ({
        name: "ABC"[i] + " + " + "ABC"[j],
        relevance: -r[i] - r[j],
        redundancy: b * similarity[k],
        evidence: -g * comp[k],
        indices: [i, j],
      }));
      rows.forEach((x) => (x.total = x.relevance + x.redundancy + x.evidence));
      const best = rows.reduce((a, b) => (a.total <= b.total ? a : b));
      table.replaceChildren();
      const head = el("tr");
      for (const t of [
        "Subset",
        "− Relevance",
        "+ Redundancy",
        "− Evidence",
        "Energy",
      ])
        head.append(el("th", t));
      table.append(head);
      const chosen = checks
        .map((v, i) => (v.checked ? i : -1))
        .filter((i) => i >= 0);
      for (const row of rows) {
        const tr = el("tr");
        if (row.indices.every((i) => chosen.includes(i)) && chosen.length === 2)
          tr.className = "chosen";
        for (const v of [
          row.name,
          fmt(row.relevance, 2),
          fmt(row.redundancy, 2),
          fmt(row.evidence, 2),
          fmt(row.total, 2),
        ])
          tr.append(el("td", v));
        table.append(tr);
      }
      out.textContent = `Count constraint: ${chosen.length} selected / 2 required.\n${chosen.length === 2 ? "Selected energy: " + fmt(rows.find((x) => x.indices.every((i) => chosen.includes(i))).total, 2) : "This selection is infeasible; choose exactly two."}\nExact toy optimum: ${best.name} · ${fmt(best.total, 2)}. Stable relevance chooses A + B.\nThe best toy energy is not a measured answer-quality result.`;
    }
    for (const n of [beta, gamma, ...checks])
      n.addEventListener("input", update);
    update();
    disclaimer(
      box,
      "Vectors and C values are illustrative. The three feasible pairs are enumerated in your browser; this does not execute MILP, QAOA or an LLM. Default γ=0 reproduces the worked relevance/redundancy example.",
    );
    return box;
  };
  widgets.milp = () => {
    const box = widget("Why a continuous y can equal a binary product."),
      c = controls(box),
      opts = [
        ["0", "0"],
        ["0.5", "0.5 · relaxation only"],
        ["1", "1"],
      ],
      a = select(c, "xᵢ", opts, "0"),
      b = select(c, "xⱼ", opts, "1"),
      out = output(box);
    function update() {
      const x = +a.value,
        z = +b.value,
        lo = Math.max(0, x + z - 1),
        hi = Math.min(x, z);
      out.textContent = `0 ≤ y ≤ 1\ny ≤ ${x}, y ≤ ${z}, y ≥ ${x + z - 1}\nAllowed y: [${lo}, ${hi}]\n${lo === hi ? "Forced product y = " + lo + " = xᵢxⱼ." : "Fractional x: the relaxation does not force y = xᵢxⱼ (" + fmt(x * z, 2) + ")."}\nBinary x values force y to 0 or 1 without an integer declaration for y.`;
    }
    a.addEventListener("change", update);
    b.addEventListener("change", update);
    update();
    disclaimer(
      box,
      "All four binary cases are exact. Choosing 0.5 explicitly switches to a linear-relaxation illustration; it is not an allowed final binary decision.",
    );
    return box;
  };
  function graphSvg(n, edges, color = "#3553ed") {
    const canvas = svg("svg", {
        viewBox: "0 0 320 240",
        role: "img",
        "aria-label": `${n} nodes and ${edges.length} illustrative interactions`,
        class: "graph-example",
      }),
      pos = Array.from({ length: n }, (_, i) => [
        160 + 90 * Math.cos(-Math.PI / 2 + (2 * Math.PI * i) / n),
        115 + 90 * Math.sin(-Math.PI / 2 + (2 * Math.PI * i) / n),
      ]);
    for (const [i, j] of edges)
      canvas.append(
        svg("line", {
          x1: pos[i][0],
          y1: pos[i][1],
          x2: pos[j][0],
          y2: pos[j][1],
          stroke: color,
          "stroke-width": 1.3,
          opacity: 0.55,
        }),
      );
    for (const [i, [x, y]] of pos.entries()) {
      canvas.append(
        svg("circle", {
          cx: x,
          cy: y,
          r: 9,
          fill: "#f8f7f1",
          stroke: color,
          "stroke-width": 1.5,
        }),
        svg(
          "text",
          { x, y: y + 3, "text-anchor": "middle", fill: color, "font-size": 8 },
          String(i + 1),
        ),
      );
    }
    return canvas;
  }
  widgets.quantum = () => {
    const wrapper = el("div");
    const ising = widget("The same decision, in two mathematical languages."),
      c = controls(ising),
      x1 = select(
        c,
        "Bit x₀",
        [
          ["0", "0"],
          ["1", "1"],
        ],
        "0",
      ),
      x2 = select(
        c,
        "Bit x₁",
        [
          ["0", "0"],
          ["1", "1"],
        ],
        "0",
      ),
      o = output(ising);
    const update = () => {
      let x = +x1.value,
        y = +x2.value,
        z0 = 1 - 2 * x,
        z1 = 1 - 2 * y,
        e = -x - 0.5 * y + 0.2 * x * y,
        h = -0.7 + 0.45 * z0 + 0.2 * z1 + 0.05 * z0 * z1;
      o.textContent = `a = (−1, −0.5), b₀₁ = 0.2\nc = −0.7, h = (0.45, 0.2), J₀₁ = 0.05\nZ eigenvalues: (${z0}, ${z1})\nBinary E(x) = ${fmt(e, 4)} · Ising H(z) = ${fmt(h, 4)}\nThe energies agree. Qubit 0 is the least significant bit.`;
    };
    x1.addEventListener("change", update);
    x2.addEventListener("change", update);
    update();
    disclaimer(
      ising,
      "A two-variable algebra check. The Ising constant matters for energy comparisons but produces only a global phase in evolution.",
    );
    wrapper.append(ising);
    const enc = widget("A sparse objective can become dense again."),
      ec = controls(enc),
      n = range(ec, "Candidate variables n", 4, 16, 10),
      f = range(ec, "Retained fraction", 0.1, 1, 0.5, 0.05),
      graphs = el("div", undefined, "two-col"),
      eo = output(enc);
    enc.insertBefore(graphs, eo);
    const draw = () => {
      const count = +n.value,
        all = [];
      for (let i = 0; i < count; i++)
        for (let j = i + 1; j < count; j++) all.push([i, j]);
      const retained = all.slice(0, Math.floor(+f.value * all.length));
      graphs.replaceChildren();
      for (const [title, edges, color] of [
        ["Semantic pair graph", retained, "#3553ed"],
        ["After squared count penalty", all, "#8a6552"],
      ]) {
        const panel = el("div");
        panel.append(el("p", title), graphSvg(count, edges, color));
        graphs.append(panel);
      }
      eo.textContent = `${retained.length} semantic interactions retained of ${all.length} possible pairs.\nλ(Σxᵢ−k)² adds 2λ to every unordered pair: ${all.length} encoded pairs in this generic case.\nThis is an interaction count, not a measured compiled gate count. XY avoids this penalty but adds mixer/preparation work.`;
    };
    n.addEventListener("input", draw);
    f.addEventListener("input", draw);
    draw();
    disclaimer(
      enc,
      "The coefficient pattern is illustrative, not a measured graph. Routing, gate cancellation and compiler choices determine complete circuit cost.",
    );
    wrapper.append(enc);
    const phase = widget(
        "Does changing the cost angle change the probabilities?",
      ),
      pc = controls(phase),
      kind = select(
        pc,
        "Initial state",
        [
          ["basis", "One basis state |10⟩"],
          ["prepared", "Prepared (|10⟩ + |01⟩) / √2"],
        ],
        "basis",
      ),
      g = range(pc, "Cost angle γ", 0, 6.28, 0.1, 0.02),
      b = range(pc, "Mixer angle β", 0, 1.57, 0.61, 0.01),
      orbits = el("div", undefined, "phase-orbits"),
      bars = el("div"),
      po = output(phase);
    phase.insertBefore(orbits, po);
    phase.insertBefore(bars, po);
    function phaseUpdate() {
      const prepared = kind.value === "prepared",
        p = probabilities(+g.value, +b.value, prepared),
        initial = probabilities(0, +b.value, prepared);
      bars.replaceChildren();
      orbits.replaceChildren();
      for (let i = 0; i < 2; i++) {
        const row = el("div", undefined, "prob-row"),
          track = el("div", undefined, "prob-track"),
          fill = el("div", undefined, "prob-fill");
        fill.style.width = 100 * p[i] + "%";
        track.append(fill);
        row.append(
          el("span", i ? "|01⟩" : "|10⟩"),
          track,
          el("span", (100 * p[i]).toFixed(1) + "%"),
        );
        bars.append(row);
        const cv = svg("svg", {
          viewBox: "0 0 100 115",
          role: "img",
          "aria-label": `${i ? "01" : "10"} cost-phase illustration`,
        });
        cv.append(
          svg("circle", {
            cx: 50,
            cy: 50,
            r: 35,
            fill: "none",
            stroke: "#c5c9b8",
          }),
        );
        const line = svg("line", {
          x1: 50,
          y1: 50,
          x2: 82,
          y2: 50,
          stroke: i && !prepared ? "#c5c9b8" : "#3553ed",
          "stroke-width": 3,
          class: "phase-arrow",
        });
        line.style.transform = `rotate(${(-+g.value * (i ? 0.5 : 1) * 180) / Math.PI}deg)`;
        cv.append(
          line,
          svg(
            "text",
            { x: 50, y: 110, "text-anchor": "middle" },
            i && !prepared
              ? "zero amplitude"
              : i
                ? "phase of |01⟩"
                : "phase of |10⟩",
          ),
        );
        orbits.append(cv);
      }
      po.textContent = `One-excitation toy: E₁₀ = −1, E₀₁ = −0.5; mixer = exp(−iβX).\nChange from γ=0: ${fmt(Math.max(...p.map((v, i) => Math.abs(v - initial[i]))), 6)}.\n${prepared ? "Relative phases can interfere after mixing. Probabilities can depend on γ." : "Only one amplitude is initially nonzero. Its phase is global: probabilities do not depend on γ."}\nTotal selected count remains one in this ideal example.`;
    }
    for (const input of [kind, g, b])
      input.addEventListener(input === kind ? "change" : "input", phaseUpdate);
    phaseUpdate();
    disclaimer(
      phase,
      "Exact two-state teaching calculation, not a Qiskit run or the full experimental ring ansatz. The prepared toy is uniform over two states; the research preparation is generally nonuniform.",
    );
    wrapper.append(phase);
    return wrapper;
  };
  widgets.sparsify = () => {
    const box = widget("Remove edges; keep track of what changed."),
      c = controls(box),
      fraction = range(c, "Retained fraction", 0.25, 1, 0.5, 0.25),
      rule = select(
        c,
        "Retention rule",
        [
          ["absolute", "Absolute magnitude"],
          ["evidence", "Evidence-guided"],
          ["degree", "Endpoint degree rank"],
          ["random", "Fixed seeded-style order"],
        ],
        "absolute",
      ),
      eps = range(c, "Sparse suboptimality allowance ε", 0, 1, 0, 0.05),
      drawing = el("div"),
      out = output(box);
    box.insertBefore(drawing, out);
    const a = [-0.8, -0.6, -0.5, -0.7, -0.4, -0.3],
      edges = [
        [0, 1, 0.4, 0],
        [0, 2, -0.3, 0.8],
        [0, 3, 0.2, 0],
        [1, 2, 0.35, 0],
        [1, 4, -0.18, 0.6],
        [2, 3, -0.12, 0.5],
        [2, 5, 0.09, 0],
        [3, 4, 0.25, 0],
        [4, 5, -0.15, 0.4],
      ];
    const bitsets = Array.from({ length: 64 }, (_, s) =>
      Array.from({ length: 6 }, (_, i) => (s >> i) & 1),
    ).filter((x) => x.reduce((a, b) => a + b, 0) === 3);
    function update() {
      const budget = Math.floor(+fraction.value * edges.length),
        rank = edges
          .map((_, i) => i)
          .sort(
            (i, j) => Math.abs(edges[j][2]) - Math.abs(edges[i][2]) || i - j,
          );
      let chosen;
      if (rule.value === "evidence") {
        const protect = rank
          .filter((i) => edges[i][3] > 0)
          .sort(
            (i, j) =>
              edges[j][3] * Math.sqrt(Math.abs(edges[j][2])) -
                edges[i][3] * Math.sqrt(Math.abs(edges[i][2])) || i - j,
          )
          .slice(0, Math.ceil(budget / 2));
        chosen = [
          ...protect,
          ...rank.filter((i) => !protect.includes(i)),
        ].slice(0, budget);
      } else if (rule.value === "random")
        chosen = [3, 0, 7, 2, 5, 1, 8, 4, 6].slice(0, budget);
      else if (rule.value === "degree") {
        const incident = Array.from({ length: 6 }, (_, v) =>
          rank.filter((i) => edges[i][0] === v || edges[i][1] === v),
        );
        chosen = [...rank]
          .sort(
            (i, j) =>
              Math.min(
                ...edges[i].slice(0, 2).map((v) => incident[v].indexOf(i)),
              ) -
                Math.min(
                  ...edges[j].slice(0, 2).map((v) => incident[v].indexOf(j)),
                ) || rank.indexOf(i) - rank.indexOf(j),
          )
          .slice(0, budget);
      } else chosen = rank.slice(0, budget);
      const sparse = chosen.map((i) => edges[i]),
        delta = edges.reduce(
          (s, e, i) => s + (chosen.includes(i) ? 0 : Math.abs(e[2])),
          0,
        ),
        fullMin = Math.min(...bitsets.map((x) => energy(x, a, edges))),
        sparseMin = Math.min(...bitsets.map((x) => energy(x, a, sparse))),
        allowed = bitsets.filter(
          (x) => energy(x, a, sparse) <= sparseMin + +eps.value + 1e-10,
        ),
        x = allowed.reduce((best, z) =>
          energy(z, a, sparse) > energy(best, a, sparse) + 1e-10 ? z : best,
        ),
        gap = energy(x, a, edges) - fullMin;
      drawing.replaceChildren(graphSvg(6, sparse));
      out.textContent = `Retained ${budget} / ${edges.length} interactions. Removed |coefficient| mass δ = ${fmt(delta, 3)}.\nSelected bits: ${x.join("")} (source order 1…6); exactly three selected.\nFull optimum: ${fmt(fullMin, 3)}; returned full energy: ${fmt(energy(x, a, edges), 3)}.\nObserved full-objective gap ${fmt(gap, 3)} ≤ 2δ + ε = ${fmt(2 * delta + +eps.value, 3)}.\nSparse gap: ${fmt(energy(x, a, sparse) - sparseMin, 3)}. No answer-quality guarantee follows.`;
    }
    fraction.addEventListener("input", update);
    rule.addEventListener("change", update);
    eps.addEventListener("input", update);
    update();
    disclaimer(
      box,
      "Six-variable signed toy, k=3. The browser enumerates its 20 feasible subsets and chooses a deterministic ε-eligible selection. The research random rule uses its recorded RNG seed; this toy uses a fixed reproducible order.",
    );
    return box;
  };
  widgets.sampling = () => {
    const box = widget("When repeated random draws are already strong."),
      c = controls(box),
      n = range(c, "Candidates n", 6, 24, 10),
      k = range(c, "Select k", 1, 9, 5),
      l = el("label", "Independent feasible draws S"),
      shots = el("input");
    shots.type = "number";
    shots.min = 1;
    shots.max = 100000;
    shots.value = 1024;
    shots.setAttribute("aria-label", "Independent feasible draws S");
    l.append(shots);
    c.append(l);
    const big = el("div", undefined, "large-number"),
      track = el("div", undefined, "coverage-track"),
      fill = el("div"),
      out = output(box);
    track.append(fill);
    box.insertBefore(big, out);
    box.insertBefore(track, out);
    function update() {
      k.max = String(+n.value - 1);
      if (+k.value > +k.max) {
        k.value = k.max;
        k.dispatchEvent(new Event("input"));
        return;
      }
      const s = Number(shots.value);
      if (!Number.isInteger(s) || s < 1 || s > 100000) {
        out.textContent = "Enter a whole draw count between 1 and 100,000.";
        return;
      }
      const m = choose(+n.value, +k.value),
        p = coverage(+n.value, +k.value, s);
      big.textContent = (100 * p).toFixed(2) + "%";
      fill.style.width = p * 100 + "%";
      out.textContent = `C(${n.value}, ${k.value}) = ${m.toLocaleString()} feasible subsets.\nP(seen one fixed optimum) = 1 − (1 − 1/${m})^${s}.\nAt n=10, k=5, S=1,024: about 98.3%. At n=16, k=5: about 20.9%.\nThis is optimum coverage, not answer accuracy or a QAOA distribution.`;
    }
    n.addEventListener("input", update);
    k.addEventListener("input", update);
    shots.addEventListener("input", update);
    update();
    disclaimer(
      box,
      "Assumptions: uniform, independent feasible draws with replacement and one designated optimum. Equal final draws do not equal total compute: QAOA also trains its angles.",
    );
    return box;
  };
  const methodNames = {
    top_k: "Relevance ranking",
    bm25: "BM25",
    hybrid: "Hybrid retrieval",
    reranker: "Cross-encoder",
    coverage: "Lexical coverage",
    mmr: "MMR",
    greedy: "Greedy energy",
    milp_base: "MILP · base",
    milp_full: "MILP · full",
    random_full: "Uniform feasible samples",
    annealing_full: "Simulated annealing",
  };
  widgets.results = () => {
    const box = widget("Explore the saved answer-quality comparisons.", true),
      c = controls(box),
      dataset = select(
        c,
        "Dataset",
        [
          ["hotpotqa", "HotpotQA"],
          ["musique", "MuSiQue"],
        ],
        "hotpotqa",
      ),
      condition = select(
        c,
        "Condition",
        [
          ["qwen15_count", "Classical count · Qwen 1.5B"],
          ["qwen3_count", "Classical count · Qwen 3B"],
          ["qwen15_tokens", "Classical token cap · Qwen 1.5B"],
          ["qwen3_tokens", "Classical token cap · Qwen 3B"],
          ["quantum", "Quantum · original circuit"],
          ["prepared", "Quantum · prepared control"],
          ["corpus25", "Bounded corpus · 25 candidates"],
          ["corpus50", "Bounded corpus · 50 candidates"],
          ["corpus100", "Bounded corpus · 100 candidates"],
          ["gatecap", "Secondary complete-gate cap"],
        ],
        "qwen15_count",
      ),
      chart = el("div", undefined, "result-chart"),
      info = el("p", undefined, "result-finding"),
      source = el("div", undefined, "chart-source"),
      tableWrap = el("div", undefined, "table-scroll"),
      table = el("table", undefined, "data-table"),
      ci = el("div");
    tableWrap.append(table);
    box.append(
      info,
      chart,
      el("div", "Answer F1 · 0 → 1 scale", "axis-note"),
      source,
      tableWrap,
      ci,
    );
    function update() {
      const file = `final_${dataset.value}_${condition.value}_analysis`,
        analysis = state.data.results[file];
      chart.replaceChildren();
      table.replaceChildren();
      source.replaceChildren();
      ci.replaceChildren();
      if (!analysis) {
        info.textContent =
          "This condition is not available in the frozen matrix.";
        return;
      }
      const rows = Object.entries(analysis.table),
        questions = rows[0]?.[1].questions;
      info.textContent = `${questions} questions in this condition. F1 averages include failed records as zero. ${["quantum", "prepared", "gatecap"].includes(condition.value) ? "Solver repeats are averaged within question. All quantum execution is simulated. " : ""}${condition.value === "prepared" ? "Prepared results are a post-freeze exploratory control. " : ""}${condition.value.startsWith("corpus") ? "Closed benchmark-passage union; larger MILPs have a one-second limit. " : ""}Compare methods within this condition; populations differ across conditions.`;
      const tr = el("tr");
      for (const h of [
        "Method",
        "N",
        "Answer F1",
        "EM",
        "Failed records",
        "Context tokens¹",
        "Line 2Q²",
      ])
        tr.append(el("th", h));
      table.append(tr);
      for (const [name, row] of rows) {
        const label = methodNames[name] || name,
          bar = el("div", undefined, "result-bar"),
          track = el("div", undefined, "bar-track"),
          fill = el("div", undefined, "bar-fill");
        fill.style.width = Math.max(0, Math.min(1, row.answer_f1)) * 100 + "%";
        track.append(fill);
        bar.append(
          el("span", label),
          track,
          el("span", fmt(row.answer_f1), "bar-value"),
        );
        chart.append(bar);
        const r = el("tr");
        for (const value of [
          label,
          row.questions,
          fmt(row.answer_f1),
          fmt(row.answer_em),
          row.failures,
          fmt(row.context_tokens_successful_only, 1),
          fmt(row.line_two_qubit_gates_all_completed_circuits, 1),
        ])
          r.append(el("td", String(value ?? "—")));
        table.append(r);
      }
      source.append(
        el("span", `Source: paper/results/${file}.json`),
        button("Inspect exact artifact", () =>
          openArtifactByPath(`paper/results/${file}.json`),
        ),
        button("Full table & paired intervals", () =>
          openReader("table-" + file),
        ),
      );
      const interval =
        condition.value === "prepared"
          ? analysis.prepared_evidence_minus_absolute_f1
          : analysis.principal_evidence_minus_absolute_f1;
      if (interval) {
        const h = el(
            "h3",
            condition.value === "prepared"
              ? "Exploratory guidance minus magnitude"
              : "Principal guidance minus magnitude",
          ),
          canvas = svg("svg", {
            viewBox: "0 0 620 130",
            role: "img",
            "aria-label": `F1 difference ${interval.mean_difference.toFixed(4)}, paired 95 percent interval ${interval.ci95.map((x) => x.toFixed(4)).join(" to ")}`,
            class: "ci-chart",
          }),
          map = (x) => 310 + x * 1800;
        canvas.append(
          svg("line", { x1: 40, y1: 60, x2: 580, y2: 60, stroke: "#c1c5b7" }),
          svg("line", {
            x1: 310,
            y1: 15,
            x2: 310,
            y2: 90,
            stroke: "#8a8e7f",
            "stroke-dasharray": "4 4",
          }),
          svg("line", {
            x1: map(interval.ci95[0]),
            y1: 60,
            x2: map(interval.ci95[1]),
            y2: 60,
            stroke: "#3553ed",
            "stroke-width": 4,
          }),
          svg("circle", {
            cx: map(interval.mean_difference),
            cy: 60,
            r: 6,
            fill: "#3553ed",
          }),
          svg(
            "text",
            { x: map(interval.ci95[0]), y: 105, "text-anchor": "middle" },
            fmt(interval.ci95[0]),
          ),
          svg(
            "text",
            { x: map(interval.ci95[1]), y: 105, "text-anchor": "middle" },
            fmt(interval.ci95[1]),
          ),
          svg(
            "text",
            { x: 310, y: 125, "text-anchor": "middle" },
            "0 = no mean difference",
          ),
        );
        ci.append(
          h,
          canvas,
          el(
            "p",
            `Mean difference ${fmt(interval.mean_difference)}; 95% paired interval [${interval.ci95.map((v) => fmt(v)).join(", ")}]. An interval spanning zero establishes neither a guidance benefit nor equality.`,
          ),
        );
      }
    }
    dataset.addEventListener("change", update);
    condition.addEventListener("change", update);
    update();
    disclaimer(
      box,
      "¹ Context tokens summarize successful records only. ² Line gates include all completed measured circuits, where available; absent values are not zero. Synthetic compilation is not physical hardware. Fewer gates alone do not establish preserved answer quality. All saved analysis tables are available in the reference library.",
    );
    return box;
  };
  widgets.artifacts = () => {
    const box = widget("Inspect the records behind a claim.", true),
      c = controls(box),
      filter = select(
        c,
        "Evidence group",
        [
          ["core", "Protocol, inputs & audits"],
          ["results", "Numerical analysis artifacts"],
        ],
        "core",
      ),
      list = el("div", undefined, "evidence-browser");
    box.append(list);
    function draw() {
      list.replaceChildren();
      for (const a of state.data.artifacts.filter((a) =>
        filter.value === "results"
          ? a.path.startsWith("paper/results/")
          : !a.path.startsWith("paper/results/"),
      ))
        list.append(button(a.path, () => openArtifact(a.id)));
    }
    filter.addEventListener("change", draw);
    draw();
    disclaimer(
      box,
      "These are bundled public JSON artifacts with SHA-256 identities. They exclude private notes, credentials, model weights and raw dataset corpora. The already-public annotation worksheet includes short source excerpts and remains unjudged. The in-site reader contains the corresponding analysis tables and explanations.",
    );
    return box;
  };
  function openDialog(id) {
    const d = $(id);
    if (!d.open) d.showModal();
  }
  function openReader(id = "readme", section = "") {
    const d = state.data.documents.find((d) => d.id === id);
    if (!d) return;
    state.reader = id;
    $("reader-title").textContent = d.title;
    $("reader-provenance").textContent =
      `${d.path} · source SHA-256 ${d.sha256} · bundled edition ${state.data.edition}. Historical dates and statuses remain labelled in the text.`;
    trustedHTML($("reader-content"), d.html);
    const nav = $("reader-nav");
    nav.replaceChildren();
    for (const doc of state.data.documents) {
      const b = button(doc.title, () => openReader(doc.id));
      b.setAttribute("aria-current", String(doc.id === id));
      nav.append(b);
    }
    const outline = $("reader-outline");
    outline.replaceChildren();
    for (const h of d.headings.filter((h) => h.level === 2))
      outline.append(
        button(h.title, () =>
          scroll(
            $("reader-content").querySelector(
              '[id="' + CSS.escape(h.slug) + '"]',
            ),
          ),
        ),
      );
    openDialog("reader-dialog");
    $("reader-scroll").scrollTop = 0;
    if (section) {
      const target = $("reader-content").querySelector(
        '[id="' + CSS.escape(section) + '"]',
      );
      if (target) {
        target.tabIndex = -1;
        target.focus({ preventScroll: true });
        scroll(target);
      }
    }
  }
  function openArtifactByPath(path) {
    const a = state.data.artifacts.find((a) => a.path === path);
    if (a) openArtifact(a.id);
  }
  function openArtifact(id) {
    const a = state.data.artifacts.find((a) => a.id === id);
    if (!a) return;
    $("evidence-title").textContent = a.path.split("/").at(-1);
    $("evidence-provenance").textContent =
      `${a.path}\nSHA-256 ${a.sha256}\nRecorded artifact; JSON displayed as text, not executed.`;
    $("evidence-content").textContent = JSON.stringify(a.data, null, 2);
    openDialog("evidence-dialog");
  }
  function deepSection(refs) {
    const section = el("section", undefined, "deep-section");
    section.append(
      el(
        "p",
        "OPTIONAL DEPTH · COMPLETE EXPLANATIONS STAY INSIDE THIS SITE",
        "widget-label",
      ),
      el("h3", "Open the reasoning."),
      el(
        "p",
        "Expand a topic for the full derivation or recorded account. Deep exploration opens these sections automatically; the complete reference reader is always available.",
      ),
    );
    refs.forEach((r) => {
      const details = el("details", undefined, "deep-reading");
      details.open = state.deep;
      details.append(el("summary", r.label));
      const line = el("p", undefined, "source-line");
      line.append(
        el("span", r.path),
        button("Open complete reference ↗", () =>
          openReader(r.doc, r.section),
        ),
      );
      const body = el("div", undefined, "prose");
      trustedHTML(body, r.html);
      details.append(line, body);
      section.append(details);
    });
    return section;
  }
  function review(items) {
    if (!items?.length) return null;
    const s = el("section", undefined, "review-section");
    s.append(
      el("p", "CHECK YOUR REASONING", "widget-label"),
      el("h3", "Explain it before revealing the answer."),
    );
    for (const [q, a] of items) {
      const d = el("details");
      d.append(el("summary", q), el("p", a));
      s.append(d);
    }
    return s;
  }
  function renderPhase(parent) {
    const nav = el("div", undefined, "phase-nav");
    nav.setAttribute("role", "tablist");
    nav.setAttribute("aria-label", "Development phase");
    for (const p of state.data.phases) {
      const b = button(
        p.id === "baseline" ? "Baseline" : p.id.toUpperCase(),
        () => setPhase(p.id),
      );
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", String(p.id === state.phase));
      b.setAttribute("aria-controls", "phase-panel");
      b.id = "phase-tab-" + p.id;
      b.tabIndex = p.id === state.phase ? 0 : -1;
      b.addEventListener("keydown", (e) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
        e.preventDefault();
        const i = state.data.phases.findIndex((p) => p.id === state.phase);
        const next =
          e.key === "Home"
            ? 0
            : e.key === "End"
              ? state.data.phases.length - 1
              : (i +
                  (e.key === "ArrowRight" ? 1 : -1) +
                  state.data.phases.length) %
                state.data.phases.length;
        setPhase(state.data.phases[next].id);
        $("phase-tab-" + state.phase).focus();
      });
      nav.append(b);
    }
    parent.append(nav);
    const p =
        state.data.phases.find((p) => p.id === state.phase) ||
        state.data.phases[0],
      panel = el("section", undefined, "phase-card");
    panel.id = "phase-panel";
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", "phase-tab-" + p.id);
    panel.append(el("p", p.tag, "widget-label"), el("h2", p.title));
    const dl = el("dl");
    for (const [label, text] of [
      ["WHY", p.why],
      ["BUILT", p.how],
      ["MATHEMATICS", p.math],
      ["OBSERVED", p.result],
    ]) {
      const row = el("div", undefined, "phase-anatomy");
      row.append(el("dt", label), el("dd", text));
      dl.append(row);
    }
    panel.append(dl);
    const boundary = el("div", undefined, "phase-boundary");
    boundary.append(
      el("strong", "BOUNDARY / REMAINING WORK"),
      el("span", p.boundary),
    );
    panel.append(boundary);
    if (p.widget) panel.append(widgets[p.widget]());
    panel.append(deepSection(p.deep));
    const row = el("div", undefined, "phase-controls"),
      i = state.data.phases.indexOf(p),
      prev = button("← Previous phase", () =>
        setPhase(state.data.phases[i - 1].id),
      ),
      next = button("Next phase →", () =>
        setPhase(state.data.phases[i + 1].id),
      );
    prev.disabled = i === 0;
    next.disabled = i === state.data.phases.length - 1;
    row.append(prev, next);
    panel.append(row);
    parent.append(panel);
  }
  function setPhase(id) {
    state.phase = id;
    history.pushState(
      null,
      "",
      "#" + new URLSearchParams({ chapter: "implementation", phase: id }),
    );
    renderChapter(false);
    $("phase-tab-" + id).focus({ preventScroll: true });
    scroll($("phase-panel"));
  }
  function renderChapter(focus = false) {
    if (!state.data) return;
    if (state.timer) {
      clearInterval(state.timer);
      state.timer = null;
    }
    const c = state.data.chapters[state.index];
    state.visited.add(c.id);
    const article = $("chapter");
    article.replaceChildren();
    article.classList.remove("chapter-enter");
    const header = el("header", undefined, "chapter-heading"),
      counter = el("div", undefined, "chapter-counter");
    counter.append(
      el("span", c.eyebrow),
      el("span", `${String(state.index + 1).padStart(2, "0")} / 10`),
    );
    const title = el("h1", c.subtitle);
    title.id = "chapter-title";
    header.append(counter, title, el("p", c.lead, "chapter-lead"));
    article.append(header);
    if (c.id === "implementation") renderPhase(article);
    else {
      const body = el("div", undefined, "chapter-body");
      trustedHTML(body, c.html);
      const earlyWidget = ["overview", "results"].includes(c.id);
      if (earlyWidget && c.widget) article.append(widgets[c.widget]());
      article.append(body);
      if (!earlyWidget && c.widget) article.append(widgets[c.widget]());
      if (c.deep.length) article.append(deepSection(c.deep));
      const r = review(c.questions);
      if (r) article.append(r);
    }
    const nav = $("chapter-nav");
    nav.replaceChildren();
    for (const [i, ch] of state.data.chapters.entries()) {
      const a = el("a");
      a.href = "#chapter=" + ch.id;
      a.append(
        el("span", String(i + 1).padStart(2, "0")),
        el("strong", ch.title),
      );
      if (i === state.index) a.setAttribute("aria-current", "step");
      nav.append(a);
    }
    $("visit-progress").textContent =
      `${state.visited.size} / 10 chapters visited`;
    $("visit-bar").style.width = state.visited.size * 10 + "%";
    $("previous-chapter").disabled = state.index === 0;
    $("next-chapter").disabled = state.index === 9;
    $("previous-chapter").textContent = state.index
      ? "← " + state.data.chapters[state.index - 1].title
      : "Start of journey";
    $("next-chapter").textContent =
      state.index < 9
        ? state.data.chapters[state.index + 1].title + " →"
        : "End of journey";
    $("chapter-position").textContent = `CHAPTER ${state.index + 1} / 10`;
    article.classList.add("chapter-enter");
    if (focus) {
      article.focus({ preventScroll: true });
      scroll(article);
    }
  }
  function navigate(delta) {
    const i = state.index + delta;
    if (i >= 0 && i < state.data.chapters.length)
      location.hash = "chapter=" + state.data.chapters[i].id;
  }
  function handleHash() {
    if (!state.data) return;
    const params = new URLSearchParams(location.hash.slice(1));
    if (params.has("read")) {
      openReader(params.get("read"), params.get("section") || "");
      return;
    }
    if (params.has("artifact")) {
      openArtifact(params.get("artifact"));
      return;
    }
    const i = state.data.chapters.findIndex(
      (c) => c.id === params.get("chapter"),
    );
    state.index = i < 0 ? 0 : i;
    const p = params.get("phase");
    if (p && state.data.phases.some((x) => x.id === p)) state.phase = p;
    renderChapter(Boolean(params.get("chapter")));
  }
  function glossary() {
    const query = $("glossary-search").value.toLowerCase().trim();
    $("glossary-list").replaceChildren();
    for (const [term, definition] of Object.entries(state.data.glossary).sort(
      ([a], [b]) => a.localeCompare(b),
    ))
      if ((term + " " + definition).toLowerCase().includes(query))
        $("glossary-list").append(el("dt", term), el("dd", definition));
    if (!$("glossary-list").children.length)
      $("glossary-list").append(
        el("p", "No matching terms. Try searching the complete project."),
      );
  }
  function search() {
    const query = $("journey-search").value.toLowerCase().trim(),
      list = $("search-results");
    list.replaceChildren();
    list.hidden = query.length < 2;
    $("journey-search").setAttribute("aria-expanded", String(!list.hidden));
    if (list.hidden) return;
    let hits = 0;
    for (const doc of state.data.documents) {
      for (const section of doc.sections) {
        const index = (section.title + " " + section.text)
          .toLowerCase()
          .indexOf(query);
        if (index < 0) continue;
        const b = button("", () => {
          openReader(doc.id, section.slug);
          list.hidden = true;
          $("journey-search").setAttribute("aria-expanded", "false");
        });
        b.append(
          el("strong", section.title),
          el("small", doc.title),
          el(
            "small",
            section.text
              .slice(Math.max(0, index - 40), index + 120)
              .replace(/\n/g, " "),
          ),
        );
        list.append(b);
        if (++hits >= 12) break;
      }
      if (hits >= 12) break;
    }
    if (!hits)
      list.append(
        el("p", "No reference matches. Try another term or open the glossary."),
      );
    else
      list.prepend(
        el(
          "p",
          `${hits === 12 ? "First 12" : hits} matching reference sections`,
        ),
      );
  }
  $("previous-chapter").addEventListener("click", () => navigate(-1));
  $("next-chapter").addEventListener("click", () => navigate(1));
  for (const [id, deep] of [
    ["mode-guided", false],
    ["mode-deep", true],
  ])
    $(id).addEventListener("click", () => {
      state.deep = deep;
      $("mode-guided").setAttribute("aria-pressed", String(!deep));
      $("mode-deep").setAttribute("aria-pressed", String(deep));
      for (const d of document.querySelectorAll("#chapter .deep-reading"))
        d.open = deep;
    });
  $("focus-toggle").addEventListener("click", () => {
    const on = document.body.classList.toggle("focus-view");
    $("focus-toggle").setAttribute("aria-pressed", String(on));
    $("focus-toggle").textContent = on ? "Exit focus ⤢" : "Focus view ⤢";
  });
  $("print-journey").addEventListener("click", () => window.print());
  $("open-library").addEventListener(
    "click",
    () => state.data && openReader(state.reader || "readme"),
  );
  $("open-glossary").addEventListener("click", () => {
    if (!state.data) return;
    glossary();
    openDialog("glossary-dialog");
    $("glossary-search").focus();
  });
  $("glossary-search").addEventListener(
    "input",
    () => state.data && glossary(),
  );
  $("journey-search").addEventListener("input", () => state.data && search());
  for (const b of document.querySelectorAll("[data-close]"))
    b.addEventListener("click", () => $(b.dataset.close).close());
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-reader],a[data-artifact]");
    if (!a || !state.data) return;
    e.preventDefault();
    if (a.dataset.reader) openReader(a.dataset.reader, a.dataset.section || "");
    else openArtifact(a.dataset.artifact);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      $("search-results").hidden = true;
      $("journey-search").setAttribute("aria-expanded", "false");
    }
    if (
      !state.data ||
      document.querySelector("dialog[open]") ||
      e.ctrlKey ||
      e.metaKey ||
      e.altKey ||
      e.shiftKey ||
      e.target.closest(
        "input,textarea,select,button,[contenteditable=true],[role=tablist]",
      )
    )
      return;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      navigate(e.key === "ArrowRight" ? 1 : -1);
    }
  });
  window.addEventListener("hashchange", handleHash);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.timer) {
      clearInterval(state.timer);
      state.timer = null;
      const play = document.querySelector(".flow-controls button");
      if (play) play.textContent = "Play the flow";
    }
  });
  async function boot() {
    try {
      const response = await fetch("/assets/journey/content.json");
      if (!response.ok)
        throw Error("Content request returned " + response.status);
      const data = await response.json();
      if (
        data.schema_version !== 1 ||
        data.chapters.length !== 10 ||
        data.phases.length !== 10
      )
        throw Error("Unsupported project-content bundle");
      state.data = data;
      $("edition-note").textContent =
        `Website edition ${data.edition} · scientific results ${data.scientific_results_date}. Saved measurements and teaching examples are distinct.`;
      renderChapter(false);
      handleHash();
    } catch (error) {
      const article = $("chapter");
      article.replaceChildren(
        el("p", "PROJECT CONTENT UNAVAILABLE", "eyebrow"),
        el("h1", "Let’s restore the reading path."),
        el(
          "p",
          "The static content could not load. No model or scientific job was started. " +
            error.message,
        ),
        button("Retry loading", boot),
      );
    }
  }
  boot();
})();
