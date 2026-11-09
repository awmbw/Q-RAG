"""One energy definition shared by ranking, MILP and a tiny exhaustive oracle."""

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array


@dataclass(frozen=True)
class SelectionProblem:
    linear: np.ndarray
    pairs: np.ndarray  # Strict upper triangle: each interaction is counted once.
    k: int | None
    token_costs: np.ndarray | None = None
    token_budget: int | None = None
    min_count: int = 0

    def __post_init__(self) -> None:
        linear = np.array(self.linear, dtype=float, copy=True)
        pairs = np.array(self.pairs, dtype=float, copy=True)
        if linear.ndim != 1 or not len(linear):
            raise ValueError("linear must be a nonempty vector")
        if pairs.shape != (len(linear), len(linear)):
            raise ValueError("pair matrix shape does not match linear vector")
        if not np.isfinite(linear).all() or not np.isfinite(pairs).all():
            raise ValueError("Objective coefficients must be finite")
        if np.any(np.tril(pairs) != 0):
            raise ValueError("pairs must have a zero diagonal and lower triangle")
        if self.k is not None and (type(self.k) is not int or not 0 <= self.k <= len(linear)):
            raise ValueError("k must be an integer between zero and candidate count")
        if type(self.min_count) is not int or not 0 <= self.min_count <= len(linear):
            raise ValueError('Invalid minimum count')
        if self.k is not None and self.min_count > self.k:
            raise ValueError('Minimum count exceeds k')
        if self.token_costs is not None:
            costs = np.array(self.token_costs, dtype=float, copy=True)
            if costs.shape != linear.shape or not np.isfinite(costs).all() or np.any(costs <= 0):
                raise ValueError('Token costs must be positive finite candidate costs')
            if type(self.token_budget) is not int or self.token_budget < 0:
                raise ValueError('Token budget must be a nonnegative integer')
            costs.flags.writeable = False
            object.__setattr__(self, 'token_costs', costs)
        elif self.token_budget is not None or self.k is None:
            raise ValueError('A variable-count problem requires token costs and budget')
        linear.flags.writeable = pairs.flags.writeable = False
        object.__setattr__(self, "linear", linear)
        object.__setattr__(self, "pairs", pairs)

    def validate_selection(self, indices: tuple[int, ...]) -> None:
        if (self.k is not None and len(indices) != self.k) or len(set(indices)) != len(indices):
            raise ValueError("Selection must contain exactly k distinct indices")
        if any(type(i) is not int or not 0 <= i < len(self.linear) for i in indices):
            raise ValueError("Invalid candidate index")
        if len(indices) < self.min_count:
            raise ValueError('Selection violates minimum count')
        if self.token_costs is not None and sum(self.token_costs[list(indices)]) > self.token_budget + 1e-8:
            raise ValueError('Selection exceeds token budget')

    def energy(self, indices: tuple[int, ...]) -> float:
        self.validate_selection(indices)
        x = np.zeros(len(self.linear))
        x[list(indices)] = 1
        return float(self.linear @ x + x @ self.pairs @ x)


def build_problem(
    relevance: np.ndarray, similarities: np.ndarray, k: int,
    alpha: float = 1.0, beta: float = 0.2,
) -> SelectionProblem:
    """Match the legacy positive-similarity redundancy objective, adding exact k."""
    if not np.isfinite([alpha, beta]).all() or alpha < 0 or beta < 0:
        raise ValueError("alpha and beta must be finite and nonnegative")
    return SelectionProblem(
        -alpha * np.asarray(relevance),
        np.triu(beta * np.maximum(np.asarray(similarities), 0), k=1), k,
    )


@dataclass(frozen=True)
class SelectionResult:
    indices: tuple[int, ...] | None
    energy: float | None
    status: str
    optimal: bool
    seconds: float
    lower_bound: float | None = None
    relative_gap: float | None = None
    message: str = ""


def select_top_k(problem: SelectionProblem, relevance: np.ndarray) -> SelectionResult:
    start = perf_counter()
    scores = np.asarray(relevance, dtype=float)
    if scores.shape != problem.linear.shape or not np.isfinite(scores).all():
        raise ValueError("Invalid relevance vector")
    ranked = []
    for i in np.argsort(-scores, kind="stable"):
        if problem.k is not None and len(ranked) >= problem.k:
            break
        if problem.token_costs is None or sum(problem.token_costs[ranked]) + problem.token_costs[i] <= problem.token_budget:
            ranked.append(int(i))
    indices = tuple(sorted(int(i) for i in ranked))
    return SelectionResult(indices, problem.energy(indices), "ranking", False,
                           perf_counter() - start)


def _finite_or_none(value: object) -> float | None:
    return float(value) if value is not None and np.isfinite(value) else None


def select_milp(problem: SelectionProblem, time_limit: float = 10.0) -> SelectionResult:
    """Linearize x_i*x_j exactly; y is continuous because x is binary."""
    if not np.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be positive and finite")
    start = perf_counter()
    n = len(problem.linear)
    edges = [(int(i), int(j)) for i, j in zip(*np.nonzero(problem.pairs))]
    coefficients = np.r_[problem.linear, [problem.pairs[i, j] for i, j in edges]]
    row_ids, col_ids, values = [], [], []
    lower, upper = [], []

    def add_row(entries: dict[int, float], low: float, high: float) -> None:
        row = len(lower)
        for col, value in entries.items():
            row_ids.append(row)
            col_ids.append(col)
            values.append(value)
        lower.append(low)
        upper.append(high)

    add_row(dict.fromkeys(range(n), 1.0), problem.k if problem.k is not None else problem.min_count,
            problem.k if problem.k is not None else np.inf)
    if problem.token_costs is not None:
        add_row(dict(enumerate(problem.token_costs)), -np.inf, problem.token_budget)
    for offset, (i, j) in enumerate(edges):
        y = n + offset
        add_row({y: 1, i: -1}, -np.inf, 0)
        add_row({y: 1, j: -1}, -np.inf, 0)
        add_row({y: 1, i: -1, j: -1}, -1, np.inf)
    matrix = coo_array(
        (np.asarray(values, dtype=float), (row_ids, col_ids)),
        shape=(len(lower), len(coefficients)),
    ).tocsc()
    result = milp(
        coefficients, integrality=np.r_[np.ones(n), np.zeros(len(edges))],
        bounds=Bounds(0, 1), constraints=LinearConstraint(matrix, lower, upper),
        options={"time_limit": time_limit, "mip_rel_gap": 0.0},
    )
    status = {0: "optimal", 1: "limit", 2: "infeasible", 3: "unbounded", 4: "error"}
    indices = None
    if result.x is not None:
        x = np.asarray(result.x[:n])
        if not np.isfinite(x).all() or np.max(np.abs(x - np.rint(x))) > 1e-5:
            raise RuntimeError("MILP returned a nonintegral incumbent")
        indices = tuple(int(i) for i in np.flatnonzero(np.rint(x)))
        problem.validate_selection(indices)
    if result.status == 0 and indices is None:
        raise RuntimeError("MILP reported optimality without an incumbent")
    return SelectionResult(
        indices, problem.energy(indices) if indices is not None else None,
        status.get(result.status, "error"), result.status == 0,
        perf_counter() - start,
        _finite_or_none(getattr(result, "mip_dual_bound", None)),
        _finite_or_none(getattr(result, "mip_gap", None)), str(result.message),
    )


def select_exhaustive(problem: SelectionProblem) -> SelectionResult:
    """Correctness reference only, deliberately limited to small candidate pools."""
    if len(problem.linear) > 20:
        raise ValueError("Exhaustive oracle is restricted to at most 20 candidates")
    start = perf_counter()
    sizes = [problem.k] if problem.k is not None else range(problem.min_count, len(problem.linear)+1)
    def feasible():
        for size in sizes:
            for candidate in combinations(range(len(problem.linear)), size):
                try:
                    problem.validate_selection(candidate)
                except ValueError:
                    continue
                yield candidate
    indices = min(feasible(), key=problem.energy, default=None)
    if indices is None:
        return SelectionResult(None, None, 'infeasible', False, perf_counter()-start)
    energy = problem.energy(indices)
    return SelectionResult(indices, energy, "optimal", True, perf_counter() - start,
                           energy, 0.0)


def raw_energy(problem: SelectionProblem, indices) -> float:
    x = np.zeros(len(problem.linear))
    x[list(indices)] = 1
    return float(problem.linear @ x + x @ problem.pairs @ x)


def select_greedy(problem, relevance=None, similarities=None, coverage=None, mode='energy'):
    start = perf_counter()
    selected = []
    candidates = set(range(len(problem.linear)))
    while candidates and (problem.k is None or len(selected) < problem.k):
        feasible = [i for i in sorted(candidates) if problem.token_costs is None or
                    sum(problem.token_costs[selected]) + problem.token_costs[i] <= problem.token_budget]
        if not feasible:
            break
        def gain(i):
            if mode == 'mmr':
                redundancy = max((similarities[i, j] for j in selected), default=0)
                return .7 * relevance[i] - .3 * redundancy
            if mode == 'coverage':
                before = np.max(coverage[selected], axis=0) if selected else np.zeros(coverage.shape[1])
                return float(np.maximum(before, coverage[i]).sum() - before.sum()) + .1*relevance[i]
            return raw_energy(problem, selected) - raw_energy(problem, selected+[i])
        best = max(feasible, key=lambda i: (gain(i), -i))
        if problem.k is None and len(selected) >= problem.min_count and gain(best) <= 0:
            break
        selected.append(best)
        candidates.remove(best)
    indices = tuple(sorted(selected))
    problem.validate_selection(indices)
    return SelectionResult(indices, problem.energy(indices), 'heuristic', False, perf_counter()-start)


def select_annealing(problem, seed=42, steps=2000):
    """Feasible fixed-count swaps or token-budget add/drop/swap moves."""
    start = perf_counter()
    rng = np.random.default_rng(seed)
    initial = select_top_k(problem, -problem.linear).indices
    current, best = set(initial), tuple(initial)
    current_energy = best_energy = problem.energy(best)
    scale = max(1e-3, np.abs(problem.linear).sum() + np.abs(problem.pairs).sum())
    for step in range(steps):
        candidate = set(current)
        selected = sorted(candidate)
        other = sorted(set(range(len(problem.linear))) - candidate)
        if problem.k is not None or rng.random() < .5:
            if not selected or not other:
                continue
            candidate.remove(int(rng.choice(selected)))
            candidate.add(int(rng.choice(other)))
        elif rng.random() < .5 and other:
            candidate.add(int(rng.choice(other)))
        elif selected:
            candidate.remove(int(rng.choice(selected)))
        indices = tuple(sorted(candidate))
        try:
            problem.validate_selection(indices)
        except ValueError:
            continue
        energy = problem.energy(indices)
        temperature = scale * .1 * (1e-4 ** (step / max(1, steps-1)))
        if energy < current_energy or rng.random() < np.exp(min(0, (current_energy-energy)/temperature)):
            current, current_energy = candidate, energy
        if energy < best_energy:
            best, best_energy = indices, energy
    return SelectionResult(best, best_energy, 'annealing', False, perf_counter()-start)


def select_random_samples(problem,seed=42,shots=1024):
    """Strong small-instance control: best of the same number of feasible samples."""
    if problem.k is None or problem.token_costs is not None or shots<1:
        raise ValueError('Uniform feasible sampling requires a fixed count and positive shots')
    start=perf_counter();rng=np.random.default_rng(seed)
    candidates={tuple(sorted(int(i) for i in rng.choice(len(problem.linear),problem.k,replace=False))) for _ in range(shots)}
    best=min(candidates,key=lambda indices:(problem.energy(indices),indices))
    return SelectionResult(best,problem.energy(best),'random_best_of_samples',False,perf_counter()-start),{
        'classical_baseline':'uniform feasible fixed-count sampling', 'seed':seed,'shots':shots,
        'unique_subsets':len(candidates),'selection_policy':'minimum common objective over all sampled feasible subsets'}
