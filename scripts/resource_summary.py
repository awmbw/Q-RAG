"""Include zero-feasible outcomes when summarizing completed quantum circuits."""

import re
from collections import defaultdict
from statistics import mean


def add_circuit_summaries(result, records):
    values = defaultdict(lambda: defaultdict(list))
    counts = defaultdict(int)
    for row in records:
        resource = row.get("resources", {})
        if resource.get("hardware") is not False or "line" not in resource:
            continue
        group = re.sub(r"_s\d+$", "", row["method"])
        counts[group] += 1
        values[group]["feasible_fraction"].append(resource["feasible_fraction"])
        values[group]["line_two_qubit_gates"].append(
            resource["line"]["two_qubit_gates"]
        )
        values[group]["all_to_all_two_qubit_gates"].append(
            resource["all_to_all"]["two_qubit_gates"]
        )
        if row.get("selection"):
            values[group]["selection_seconds"].append(row["selection"]["seconds"])
    for group, metrics in values.items():
        result["table"][group]["completed_circuit_records"] = counts[group]
        for key, observed in metrics.items():
            result["table"][group][key + "_all_completed_circuits"] = mean(observed)
    result["circuit_resource_denominator"] = (
        "All completed circuits, including no-feasible-sample outcomes and later generation failures. Missing circuit measurements are not zero."
    )
    return result
