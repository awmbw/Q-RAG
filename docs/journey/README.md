# Interactive project journey

Start the existing FastAPI service and open `/journey`. The live comparison laboratory remains at `/`; both pages share the current paper background, blue accents and locally served fonts. No hosted website account, external JavaScript service or model download is needed to read the journey. The local HTTP service must still be running; this is not a standalone `file://` page or an offline service worker.

## Reading sequence

1. The whole project: problem, pipeline and scope.
2. Where it stands: delivered work, findings and remaining boundaries.
3. The original plan: hypothesis and documented adaptations.
4. Foundations: inputs, labels, embeddings, selection, generation and metrics.
5. Research design: related work, controls, evaluation and fair comparisons.
6. Implementation: historical baseline, then phases A–I, each with its need, implementation, mathematics, observations and limitations.
7. Results: interactive comparisons from saved numerical analyses, uncertainty and failure accounting.
8. Reproduction: artifact inspection, manifests and claim-to-evidence links.
9. The running system: service, persistent jobs, model loading, profiling and reliability.
10. The research argument: manuscript, limitations, future work and external publication tasks.

Guided mode keeps long references collapsed. Deep exploration opens them. Both modes retain the full underlying text in the website. The reference reader contains 43 documents, including the complete three companions, manuscript and saved analysis tables; use its document list and heading outline. Search indexes the full reference text. The glossary contains 46 terms. Focus view reduces navigation clutter, and Print chapter prints the current chapter and currently expanded material. Visited progress records navigation during the current page session, not mastery.

The pipeline can be stepped or played; other examples respond to user controls. Reduced-motion preferences disable decorative motion and turn pipeline playback into a single step. Arrow keys navigate chapters outside interactive controls; phase tabs support arrows, Home and End. Native dialogs support Escape and retain ordinary keyboard behavior. Responsive CSS adapts navigation and tables for smaller screens. These are implemented behaviors, not an accessibility certification or a completed visual review.

## Content and provenance

- [Editorial source](content.cjs): chapter narrative, phase summaries, review questions and glossary.
- [Compiler](../../scripts/build_journey.cjs): explicit allowlist of public documents and JSON artifacts, math rendering, relative-link rewriting and figure/font packaging.
- [Generated bundle](../../src/qrag_service/static/journey/content.json): rendered chapters, full references, search text, exact public artifact values and SHA-256 provenance.
- [Generated manifest](../../src/qrag_service/static/journey/manifest.json): counts, tool versions, source hashes and content hash.
- [Client](../../src/qrag_service/static/journey.js), [page](../../src/qrag_service/static/journey.html) and [styles](../../src/qrag_service/static/journey.css): navigation, local examples and saved-result explorers.

The compiler reads only its allowlist. It does not recursively publish the repository, private model caches, raw dataset corpora, SQLite databases or local inference runs. Public result JSON is bundled unchanged. Scientific source, coefficients, seeds and result tables are not altered. GitHub source links are optional provenance; the complete selected documentation and artifact text are available inside the website. External literature and policy links remain external. Publication information is labelled as a dated snapshot.

Rendered reference links open the in-site reader; allowlisted JSON links open the evidence viewer. Source code links open GitHub. Three existing research figures are packaged locally. KaTeX mathematics uses local CSS/fonts and includes its upstream license. Markdown HTML is disabled, and user search queries and JSON values are inserted as text. No public multiuser security claim is made.

## Rebuild and check

Node is a development dependency only. The compiled website is shipped in the Python wheel and container; normal service startup does not run npm or render Markdown.

```bash
npm ci --prefix tools/journey --ignore-scripts --no-audit --no-fund
node scripts/build_journey.cjs
node scripts/check_journey.cjs
NODE_PATH="$PWD/tools/journey/node_modules" node scripts/check_dashboard.cjs
node --check src/qrag_service/static/journey.js
venv/bin/python -m unittest discover -s tests -v
```

Run these from the repository root. Rebuild after editing any allowlisted document, artifact, editorial source, compiler or tool lock. Commit the updated generated bundle and manifest together with their sources. CI rebuilds and rejects generated-file differences, then runs the journey and laboratory DOM checks. A clean rebuild is deterministic; no wall-clock timestamp is inserted into the content.

The journey checks verify source freshness, all chapter/phase paths, full-reference access, search and dialogs, failure recovery, all result conditions, the MILP truth table, Ising equality, global-phase invariance, the sparsification bound and sampling calculations. They use jsdom and do not paint CSS. The service test checks actual HTTP asset routes with a cold engine and proves that reading starts no model preparation or jobs.

Browser navigation/screenshot calls failed in the available computer-use connection during this implementation. Consequently desktop/mobile visual rendering, real-browser focus behavior and the reduced-motion appearance remain unverified. See the [implementation verification receipt](../research_report/evidence/journey_20261112.json) for checks actually executed. Earlier real-model service measurements remain historical evidence; they are not described as rerun by these presentation checks.

## Changing scientific claims

Change the maintained research documents and claim map first, with supporting experimental artifacts. Then update the narrative and rebuild. Do not edit a generated chart to imply a better finding. Interactive toy outputs are explanatory calculations, not new experiments, QAOA executions or model predictions. The results explorer reads saved analyses and preserves their populations, uncertainty and denominator limitations.
