# Remaining external work after the local execution

The laptop implementation, declared experiments, artifact checks, manuscript draft and local service are complete within their documented scope. No research computation is left pending. This file lists decisions or validations that cannot be represented as completed by autonomous implementation.

| Item | Current state | Required next action |
| --- | --- | --- |
| Scientific review and publication decision | Comparative/negative findings; no demonstrated guidance gain or quantum advantage | Independently examine the methods, sources, predictions and contribution. Decide whether the current diagnostic study is substantial enough for the chosen venue or needs further research. |
| Authorship and institutional details | Not invented in the manuscript | Confirm actual authors/order, affiliations, corresponding author, contributions, funding and competing interests. All authors approve the final content. |
| Code, artifact and manuscript licensing | No project-wide grant assigned | Rights holders choose appropriate licenses and check upstream terms before a formal archival release/submission. The 3B generator uses different terms from the 1.5B model. |
| Independent graph validation | Forty source-grounded edges prepared, all unjudged | Use [the worksheet](research_report/annotation_sample.json) and restored full documents to annotate entity identity and useful question bridges. Do not describe the current graph as semantically verified. |
| Browser visual review | HTTP/static/API checks and real inference passed; no enabled browser surface was available | Open the local dashboard, review its layout and exercise the controls interactively. This is separate from the completed manuscript PDF visual inspection. |
| Venue formatting and actual submission | Generic editable Markdown and a reviewed PDF exist; no submission performed | Choose a venue, apply its current Word/LaTeX/template and citation requirements, complete declarations/disclosures and submit through the official portal. Retain the substantive AI-assistance disclosure. |
| Independent closest-method reproduction | Related methods and estimator differences documented | If needed for the final claim, obtain/run the original reference implementations and model settings. Current local coverage is an explicitly different comparator, not an exact SetR/QUBO-paper reproduction. |

The current local demonstration runs in the `qrag-release-demo` CPU container at `http://127.0.0.1:8766`. It uses the persistent `qrag-verification-state` volume and a read-only local model-cache mount. The [service guide](SERVICE_GUIDE.md) describes restarting it or running a new instance. Old verification containers are stopped. No unrelated user containers or services were changed.

Physical quantum execution was unavailable and remains optional future work; no hardware result is implied. Typed factual relation extraction, quantum token-budget encoding, large-scale production deployment and continuously batched generation were not added. The [implementation decisions](DEVELOPMENT_SEQUENCE.md) and [limitations](../paper/manuscript.md#9-limitations-and-threats-to-validity) explain the bounded study and local engineering scope. They are extensions, not hidden completed features.

No cloud allocation, paid inference, quantum allocation, email, manuscript submission or payment was used. GitHub contains the phase commits and versioned research artifact. The three main documents retain detailed mathematics, measured outcomes and implementation history. A research artifact release or preprint is not peer-reviewed acceptance.
