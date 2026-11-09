"""Actual Qiskit QAOA simulation with checked energies and complete compilation.

Optimization uses exact statevector expectations unless training_shots is set.
Final measurements are sampled; optional noise affects the final circuit only.
This module does not claim quantum hardware execution or a speedup.
"""

from time import perf_counter

import numpy as np
from scipy.optimize import minimize

from qrag.optimization import SelectionResult


def ising_coefficients(linear, pairs):
    linear, pairs = np.asarray(linear), np.asarray(pairs)
    constant = 0.5 * linear.sum() + 0.25 * pairs.sum()
    fields = -0.5 * linear - 0.25 * (pairs.sum(axis=0) + pairs.sum(axis=1))
    return float(constant), fields, 0.25 * pairs


def diagonal_energies(linear, pairs):
    n = len(linear)
    if n > 20:
        raise ValueError("Explicit spectrum limited to 20 qubits")
    bits = (
        (np.arange(2**n, dtype=np.uint64)[:, None] >> np.arange(n, dtype=np.uint64)) & 1
    ).astype(float)
    return bits @ linear + np.einsum(
        "bi,ij,bj->b", bits, pairs, bits, optimize=True
    ), bits


def encoded_coefficients(problem, mixer):
    if problem.k is None or problem.token_costs is not None:
        raise ValueError(
            "Quantum study supports native fixed count only; no token-budget encoding is claimed"
        )
    linear, pairs = problem.linear.copy(), problem.pairs.copy()
    penalty = 0.0
    constant = 0.0
    if mixer == "penalty":
        penalty = float(np.abs(linear).sum() + np.abs(pairs).sum() + 1)
        linear += penalty * (1 - 2 * problem.k)
        pairs += np.triu(np.full_like(pairs, 2 * penalty), 1)
        constant = penalty * problem.k**2
    elif mixer != "xy":
        raise ValueError("Mixer must be penalty or xy")
    return linear, pairs, constant, penalty


def qaoa_circuit(problem, angles, p=1, mixer="xy", seed=42):
    from qiskit import QuantumCircuit

    n = len(problem.linear)
    linear, pairs, offset, penalty = encoded_coefficients(problem, mixer)
    constant, fields, couplings = ising_coefficients(linear, pairs)
    phase_scale = max(
        1.0, float(np.max(np.abs(fields))), float(np.max(np.abs(couplings)))
    )
    qc = QuantumCircuit(n)
    initial = ()
    if mixer == "xy":
        initial = tuple(
            sorted(
                int(i)
                for i in np.random.default_rng(seed).choice(n, problem.k, replace=False)
            )
        )
        for i in initial:
            qc.x(i)
    else:
        qc.h(range(n))
    for layer in range(p):
        gamma, beta = angles[2 * layer : 2 * layer + 2]
        for i, field in enumerate(fields):
            if field:
                qc.rz(2 * gamma * field / phase_scale, i)
        for i, j in zip(*np.nonzero(couplings)):
            qc.rzz(2 * gamma * couplings[i, j] / phase_scale, int(i), int(j))
        if mixer == "xy":
            ring = [(i, i + 1) for i in range(n - 1)]
            if n > 2:
                ring.append((n - 1, 0))
            for i, j in ring:
                qc.rxx(beta, i, j)
                qc.ryy(beta, i, j)
        else:
            qc.rx(2 * beta, range(n))
    return qc, {
        "phase_scale": phase_scale,
        "penalty_strength": penalty,
        "initial_indices": initial,
        "encoded_offset": offset,
        "ising_constant": constant,
        "encoded_pair_count": int(np.count_nonzero(pairs)),
    }


def compilation_resources(circuit, seed=42):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap

    result = {}
    for target in ("all_to_all", "line"):
        compiled = transpile(
            circuit,
            basis_gates=["rz", "sx", "x", "cx"],
            optimization_level=1,
            coupling_map=CouplingMap.from_line(circuit.num_qubits)
            if target == "line" and circuit.num_qubits > 1
            else None,
            seed_transpiler=seed,
        )
        result[target] = {
            "depth": compiled.depth(),
            "two_qubit_gates": sum(
                1 for instruction in compiled.data if len(instruction.qubits) == 2
            ),
            "operations": dict(compiled.count_ops()),
            "qubits": compiled.num_qubits,
        }
    return {
        "basis_gates": ["rz", "sx", "x", "cx"],
        "optimization_level": 1,
        "transpiler_seed": seed,
        "targets": "synthetic all-to-all and bidirectional line; not calibrated physical devices",
        **result,
    }


def solve_qaoa(
    problem,
    p=1,
    seed=42,
    shots=1024,
    max_evals=64,
    mixer="xy",
    noise=0.0,
    training_shots=0,
):
    from qiskit.quantum_info import Statevector

    n = len(problem.linear)
    if n > 16:
        raise ValueError("Laptop QAOA study limited to 16 candidates")
    if (
        type(p) is not int
        or p < 1
        or p > 4
        or shots < 1
        or max_evals < 2 * p + 2
        or not 0 <= noise < 1
        or training_shots < 0
    ):
        raise ValueError("Invalid QAOA budget")
    started = perf_counter()
    linear, pairs, constant, _ = encoded_coefficients(problem, mixer)
    energies, bits = diagonal_energies(linear, pairs)
    energies += constant
    rng = np.random.default_rng(seed)
    trace = []

    def objective(angles):
        circuit, _ = qaoa_circuit(problem, angles, p, mixer, seed)
        probabilities = Statevector.from_instruction(circuit).probabilities()
        value = (
            float(
                np.mean(
                    energies[rng.choice(len(energies), training_shots, p=probabilities)]
                )
            )
            if training_shots
            else float(probabilities @ energies)
        )
        trace.append(value)
        return value

    initial = rng.uniform(-np.pi, np.pi, size=2 * p)
    optimization = minimize(
        objective,
        initial,
        method="COBYLA",
        options={"maxiter": max_evals, "rhobeg": 0.5, "tol": 1e-3},
    )
    circuit, encoding = qaoa_circuit(problem, optimization.x, p, mixer, seed)
    probabilities = Statevector.from_instruction(circuit).probabilities()
    resources = compilation_resources(circuit, seed)
    if noise:
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, depolarizing_error

        model = NoiseModel()
        model.add_all_qubit_quantum_error(depolarizing_error(noise, 2), ["cx"])
        for gate in ["sx", "x"]:
            model.add_all_qubit_quantum_error(depolarizing_error(noise / 10, 1), gate)
        measured = circuit.copy()
        measured.measure_all()
        measured = transpile(
            measured,
            basis_gates=["rz", "sx", "x", "cx"],
            optimization_level=1,
            seed_transpiler=seed,
        )
        simulator = AerSimulator(
            method="density_matrix", noise_model=model, max_parallel_threads=4
        )
        counts = (
            simulator.run(measured, shots=shots, seed_simulator=seed)
            .result()
            .get_counts()
        )
        sampled_counts = {
            int(key.replace(" ", ""), 2): count for key, count in counts.items()
        }
    else:
        sampled = rng.choice(len(probabilities), shots, p=probabilities)
        states, counts = np.unique(sampled, return_counts=True)
        sampled_counts = dict(zip(states.tolist(), counts.tolist()))
    feasible = []
    feasible_shots = 0
    for state, count in sampled_counts.items():
        indices = tuple(int(i) for i in np.flatnonzero(bits[state]))
        try:
            problem.validate_selection(indices)
        except ValueError:
            continue
        feasible.append(indices)
        feasible_shots += count
    best = min(
        feasible, key=lambda indices: (problem.energy(indices), indices), default=None
    )
    seconds = perf_counter() - started
    resources.update(
        {
            "execution_mode": "ideal expectation optimization; final noisy density-matrix sampling"
            if noise
            else (
                "finite-shot objective and final sampling"
                if training_shots
                else "ideal expectation optimization; finite-shot final sampling"
            ),
            "hardware": False,
            "p": p,
            "mixer": mixer,
            "seed": seed,
            "shots": shots,
            "training_shots_per_evaluation": training_shots,
            "max_evals": max_evals,
            "evaluations": len(trace),
            "optimizer_success": bool(optimization.success),
            "optimizer_message": str(optimization.message),
            "angles": optimization.x.tolist(),
            "training_energies": trace,
            "best_training_energy": float(optimization.fun),
            "feasible_shots": feasible_shots,
            "feasible_fraction": feasible_shots / shots,
            "unique_feasible_samples": len(feasible),
            "ideal_feasible_probability": float(
                probabilities[np.sum(bits, axis=1) == problem.k].sum()
            ),
            "noise_two_qubit_depolarizing_probability": noise,
            "noise_one_qubit_probability": noise / 10,
            "noise_note": "Final all-to-all compiled sampling only; no noisy parameter optimization or device calibration is claimed.",
            "selection_policy": "minimum surrogate energy among all measured feasible samples; deterministic index tie-break; no repair",
            "sampled_counts": {
                str(state): count for state, count in sampled_counts.items()
            },
            **encoding,
        }
    )
    return SelectionResult(
        best,
        problem.energy(best) if best is not None else None,
        "sampled_feasible" if best is not None else "no_feasible_shot",
        False,
        seconds,
    ), resources
