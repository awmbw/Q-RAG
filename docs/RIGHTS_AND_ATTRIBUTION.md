# Artifact rights and upstream attribution

Checked November 10, 2026. This file records upstream metadata and release boundaries; it does not replace the actual license texts. No new project-wide software or manuscript license has been chosen on behalf of the rights holders. Repository availability alone should not be described as a permissive license. License choice remains an owner/author decision before a formal archival or scholarly release.

| Resource | Primary source and declared terms | Use in this artifact |
| --- | --- | --- |
| HotpotQA | [Dataset card](https://huggingface.co/datasets/hotpotqa/hotpot_qa), CC BY-SA 4.0; Yang et al., EMNLP 2018 | Downloaded locally; frozen IDs/hashes and derived outcomes released. Full source documents/processed splits are restored from upstream rather than bundled. |
| MuSiQue | [Author repository](https://github.com/StonyBrookNLP/musique), CC BY 4.0; Trivedi et al., TACL 2022 | Official answerable data archive downloaded locally; IDs/hashes, aliases handling and derived outcomes documented. |
| MiniLM-L6-v2 | [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), Apache 2.0 | Immutable snapshot for embeddings; weights excluded from Git and container images. |
| Qwen2.5-1.5B-Instruct | [Model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), Apache 2.0 | Main local generator and demonstration model; weights excluded. |
| Qwen2.5-3B-Instruct | [Frozen license](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/aa8e72537993ba99e69dfaafa59ed015b17504d1/LICENSE), Qwen Research License | Research comparison model; its terms differ from the 1.5B model. No commercial-use grant is inferred from the model family name. Weights excluded. |
| MS MARCO MiniLM cross-encoder | [Model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2), Apache 2.0 | Fixed reranking baseline; weights excluded. |

Exact model revisions are in [model_revisions.json](../configs/model_revisions.json) and run configurations. Dataset revisions/archive hashes are in [the split manifest](../configs/splits/research_v1.json). The corpus manifest lists deduplicated candidate IDs and source input identities. Changes to representation or provenance are part of this project's processing, not changes asserted about the original dataset authors' annotations.

Published compact predictions include generated answers, selected source identifiers, metrics and resource measurements. They omit full dataset passages, complete prompts and model weights. Public restoration scripts reconstruct frozen inputs from the original hosts, subject to their terms. The large local experiment bundles preserve prompts and input IDs for inspection; they are not automatically part of a public release.

The software uses NumPy/SciPy, PyTorch/Transformers/Sentence Transformers, FAISS, Qiskit/Aer, FastAPI/Pydantic/Uvicorn, OpenTelemetry and the remaining packages identified in environment snapshots. Their licenses continue to apply to their distributions. Project code implementing score semantics is independently checked against the official HotpotQA/MuSiQue evaluators; no copied evaluator implementation is attributed to this project as an original invention.

Before formal submission or archival publication, confirm author/rights-holder permission for the chosen code, results and manuscript licenses and retain required upstream notices. Do not label a GitHub artifact as peer-reviewed, independently validated, or awarded a reproducibility badge unless that process has actually occurred.
