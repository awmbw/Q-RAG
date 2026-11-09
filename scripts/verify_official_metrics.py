"""Compare independent scoring code with inspected primary evaluator functions."""

import ast
import collections
import hashlib
import random
import re
import string
from collections import Counter
from pathlib import Path

import httpx

from qrag.data import EvaluationLabels
from qrag.datasets import score_answer
from qrag.experiments.artifacts import write_json


def main():
    sources = {
        "hotpotqa": (
            "https://raw.githubusercontent.com/hotpotqa/hotpot/master/hotpot_evaluate_v1.py",
            {"normalize_answer", "f1_score", "exact_match_score"},
        ),
        "musique": (
            "https://raw.githubusercontent.com/StonyBrookNLP/musique/main/metrics/answer.py",
            {"normalize_answer", "get_tokens", "compute_f1", "compute_exact"},
        ),
    }
    rng = random.Random(17)
    words = ["the", "India", "no", "yes", "noanswer", "red", "red", "blue!", "1995", ""]
    fixtures = [("", ""), ("yes indeed", "yes"), ("the", ""), ("India.", "India")]
    fixtures += [
        (
            " ".join(rng.choices(words, k=rng.randrange(5))),
            " ".join(rng.choices(words, k=rng.randrange(5))),
        )
        for _ in range(1000)
    ]
    report = {}
    for dataset, (url, allowed) in sources.items():
        with httpx.Client(
            transport=httpx.HTTPTransport(retries=3), timeout=60
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            source = response.content
        tree = ast.parse(source)
        # Execute only the previously inspected pure metric functions, not the
        # module's CLI/imports or any downloaded application code.
        funcs = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in allowed
        ]
        assert {f.name for f in funcs} == allowed
        namespace = {
            "re": re,
            "string": string,
            "Counter": Counter,
            "collections": collections,
        }
        exec(compile(ast.Module(body=funcs, type_ignores=[]), url, "exec"), namespace)
        for prediction, reference in fixtures:
            labels = EvaluationLabels(reference, frozenset(), dataset=dataset)
            actual = score_answer(prediction, labels)
            expected = (
                namespace["f1_score"](prediction, reference)[0]
                if dataset == "hotpotqa"
                else namespace["compute_f1"](reference, prediction)
            )
            assert abs(actual["answer_f1"] - expected) < 1e-12, (
                dataset,
                prediction,
                reference,
            )
            exact = (
                namespace["exact_match_score"](prediction, reference)
                if dataset == "hotpotqa"
                else namespace["compute_exact"](reference, prediction)
            )
            assert actual["answer_em"] == exact
        report[dataset] = {
            "source": url,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "pairs_checked": len(fixtures),
            "all_agree": True,
        }
    write_json(Path("docs/research_report/evidence/metric_verification.json"), report)
    print(report)


if __name__ == "__main__":
    main()
