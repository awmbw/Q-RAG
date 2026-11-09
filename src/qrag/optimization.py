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
    k: int

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
        if type(self.k) is not int or not 0 <= self.k <= len(linear):
            raise ValueError("k must be an integer between zero and candidate count")
        linear.flags.writeable = pairs.flags.writeable = False
        object.__setattr__(self, "linear", linear)
        object.__setattr__(self, "pairs", pairs)

    def validate_selection(self, indices: tuple[int, ...]) -> None:
        if len(indices) != self.k or len(set(indices)) != len(indices):
            raise ValueError("Selection must contain exactly k distinct indices")
        if any(type(i) is not int or not 0 <= i < len(self.linear) for i in indices):
            raise ValueError("Invalid candidate index")

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
    ranked = np.argsort(-scores, kind="stable")[:problem.k]
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

    add_row(dict.fromkeys(range(n), 1.0), problem.k, problem.k)
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
    indices = min(combinations(range(len(problem.linear)), problem.k),
                  key=problem.energy)
    energy = problem.energy(indices)
    return SelectionResult(indices, energy, "optimal", True, perf_counter() - start,
                           energy, 0.0)
