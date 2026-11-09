"""Write a portable, measured host report; never include credentials or home paths."""

import argparse
import importlib.metadata as metadata
import os
import platform
import shutil
import subprocess
from pathlib import Path

from qrag.experiments.artifacts import write_json


def collect() -> dict:
    import numpy as np
    import torch
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from scipy.optimize import milp

    cuda = torch.cuda.is_available()
    device = "cuda" if cuda else "cpu"
    tensor = torch.arange(16, device=device, dtype=torch.float32).reshape(4, 4)
    assert torch.equal(tensor @ torch.eye(4, device=device), tensor)
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    assert np.allclose(Statevector(qc).probabilities(), [0.5, 0, 0, 0.5])
    result = milp([-1.0], integrality=[1], bounds=([0], [1]))
    assert result.success and result.x[0] == 1
    names = [
        "numpy",
        "scipy",
        "torch",
        "transformers",
        "sentence-transformers",
        "huggingface-hub",
        "qiskit",
        "qiskit-aer",
        "qiskit-algorithms",
        "faiss-cpu",
        "networkx",
        "fastapi",
        "pytest",
        "ruff",
    ]
    packages = {name: metadata.version(name) for name in names}
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, amount = line.split(":", 1)
        if name in {"MemTotal", "MemAvailable"}:
            memory[name + "_gib"] = round(int(amount.split()[0]) / 2**20, 2)
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "memory": memory,
        "disk_free_gib": round(shutil.disk_usage(".").free / 2**30, 2),
        "cuda_available": cuda,
        "torch_cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if cuda else None,
        "gpu_total_gib": torch.cuda.get_device_properties(0).total_memory / 2**30
        if cuda
        else None,
        "packages": packages,
        "verification": [
            "tensor matrix multiplication on selected device",
            "Bell-state simulation",
            "HiGHS binary optimization",
            "pip check",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run([os.sys.executable, "-m", "pip", "check"], check=True)
    write_json(args.output, collect())
