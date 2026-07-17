"""CSV report export for the ReviewMind demo."""

import os
import pickle


def load_cached_report(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def export_report(rows, filename):
    path = os.path.join("/tmp/reports", filename)
    with open(path, "w") as f:
        for row in rows:
            f.write(",".join(str(v) for v in row.values()) + "\n")
    return path
