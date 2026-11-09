"""Exploratory feasible-superposition control; frozen primary code is untouched."""

import argparse
import json
from pathlib import Path

import numpy as np

import qrag.experiments.study as study
import qrag.quantum as quantum
from qrag.experiments.artifacts import file_hash, source_hash, value_hash, write_json

ORIGINAL_CIRCUIT = quantum.qaoa_circuit


def prepared_circuit(problem, angles, p=1, mixer="xy", seed=42):
    circuit, encoding = ORIGINAL_CIRCUIT(problem, angles, p, mixer, seed)
    if mixer != "xy":
        return circuit, encoding
    prepared = circuit.copy_empty_like()
    initial_count = len(encoding["initial_indices"])
    for instruction in circuit.data[:initial_count]:
        assert instruction.operation.name == "x"
        prepared.append(
            instruction.operation,
            [circuit.find_bit(q).index for q in instruction.qubits],
        )
    n = circuit.num_qubits
    ring = [(i, i + 1) for i in range(n - 1)]
    if n > 2:
        ring.append((n - 1, 0))
    for i, j in ring:
        prepared.rxx(np.pi / 4, i, j)
        prepared.ryy(np.pi / 4, i, j)
    for instruction in circuit.data[initial_count:]:
        prepared.append(
            instruction.operation,
            [circuit.find_bit(q).index for q in instruction.qubits],
        )
    encoding.update(
        {
            "state_preparation": "seeded feasible basis state followed by one fixed XY ring sweep",
            "preparation_angle": float(np.pi / 4),
            "preparation_included_in_compilation": True,
            "study_scope": "post-freeze exploratory preparation control; not the principal confirmatory comparison",
        }
    )
    return prepared, encoding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(Path("configs/preparation_control.json").read_text())[
        "configs"
    ]
    expected = {entry["config"]: entry["sha256"] for entry in entries}
    if file_hash(args.config) != expected[str(args.config)]:
        raise ValueError("Frozen exploratory configuration changed")
    spec = json.loads(args.config.read_text())
    output = Path("results") / args.config.stem
    core_hash = source_hash()
    extension_hash = file_hash(Path(__file__))
    combined_hash = value_hash(
        {"frozen_core_sha256": core_hash, "extension_sha256": extension_hash}
    )
    snapshot = output.parent / (output.name + "_extension_snapshot.json")
    if snapshot.exists():
        previous = json.loads(snapshot.read_text())
        if previous["combined_sha256"] != combined_hash:
            raise ValueError("Preparation extension changed before resume")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            snapshot,
            {
                "combined_sha256": combined_hash,
                "frozen_core_sha256": core_hash,
                "extension_sha256": extension_hash,
                "extension_source": Path(__file__).read_text(),
                "configuration_sha256": file_hash(args.config),
            },
        )
    # This process has one scientific writer and no concurrent study workers.
    # The composite identity explicitly includes this extension's exact bytes.
    quantum.qaoa_circuit = prepared_circuit
    study.source_hash = lambda: combined_hash
    try:
        study.run_study(spec, output, resume=(output / "manifest.json").exists())
    finally:
        if output.exists():
            write_json(
                output / "extension_snapshot.json", json.loads(snapshot.read_text())
            )


if __name__ == "__main__":
    main()
