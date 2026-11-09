"""Download the recorded public model revisions, with no paid API or remote code."""

import argparse
import json
from pathlib import Path

from huggingface_hub import snapshot_download

from qrag.config import ExperimentConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true")
    args = parser.parse_args()
    config = ExperimentConfig()
    models = {
        config.embedding_model: config.embedding_revision,
        config.generator_model: config.generator_revision,
    }
    if not args.core_only:
        models.update(json.loads(Path("configs/model_revisions.json").read_text()))
    for model, revision in models.items():
        print("Downloading public immutable snapshot", model, revision, flush=True)
        snapshot_download(model, revision=revision)


if __name__ == "__main__":
    main()
