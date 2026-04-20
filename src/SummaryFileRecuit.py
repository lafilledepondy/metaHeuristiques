import os
import argparse
import csv
import re

from projetUtils import valid_folder


def parse_log_file(path):
    values = {
        "logFile": os.path.basename(path),
        "data_file": "missing",
        "p": "missing",
        "epsilon": "missing",
        "nb_runs": "missing",
        "elapsed_time": "missing",
        "best": "missing",
        "worst": "missing",
        "mean": "missing",
        "median": "missing",
        "std_dev": "missing",
        "nb_best_found": "missing",
        "cpu_total": "missing",
        "cpu_mean": "missing",
        "T0_best": "missing",
        "Tf_best": "missing",
        "T0_mean": "missing",
        "Tf_mean": "missing",
        "solution_file": "missing",
    }

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # first parse explicit solver log fields that do not use key=value format
    explicit_patterns = {
        "data_file": r"Data file path\s*=\s*(.+)",
        "p": r"Number of classes\s*=\s*(.+)",
        "epsilon": r"Epsilon\s*=\s*(.+)",
        "nb_runs": r"Number of multi-start runs\s*=\s*(.+)",
        "elapsed_time": r"cpuTime\s*=\s*(.+)",
        "solution_file": r"Solution is written in the following file:\s*(.+)",
    }

    for key, pattern in explicit_patterns.items():
        match = re.search(pattern, content)
        if match:
            values[key] = match.group(1).strip()

    # support solver log value `cpuTime` as elapsed_time when elapsed_time is absent
    if values["elapsed_time"] == "missing":
        match = re.search(r"cpuTime\s*=\s*(.+)", content)
        if match:
            values["elapsed_time"] = match.group(1).strip()

    # also capture key=value style lines for stats and optional fields
    for key in [
        "best",
        "worst",
        "mean",
        "median",
        "std_dev",
        "nb_best_found",
        "cpu_total",
        "cpu_mean",
        "T0_best",
        "Tf_best",
        "T0_mean",
        "Tf_mean",
        "nb_runs",
        "elapsed_time",
    ]:
        match = re.search(rf"^{re.escape(key)}\s*=\s*(.+)$", content, flags=re.MULTILINE)
        if match:
            values[key] = match.group(1).strip()

    # support dictionary-style stats lines if present
    stats_match = re.search(
        r"(?:Recuit\s*Simule|RecuitSimule|Multi-start)\s+stats:\s*(\{.*?\})",
        content,
        flags=re.DOTALL
    )
    if stats_match:
        try:
            import ast
            stats_dict = ast.literal_eval(stats_match.group(1))
            values.update({
                "best": stats_dict.get("best", values["best"]),
                "worst": stats_dict.get("worst", values["worst"]),
                "mean": stats_dict.get("mean", values["mean"]),
                "median": stats_dict.get("median", values["median"]),
                "std_dev": stats_dict.get("std_dev", values["std_dev"]),
                "nb_best_found": stats_dict.get("nb_best_found", values["nb_best_found"]),
                "cpu_total": stats_dict.get("cpu_total", values["cpu_total"]),
                "cpu_mean": stats_dict.get("cpu_mean", values["cpu_mean"]),
                "T0_best": stats_dict.get("T0_best", values["T0_best"]),
                "Tf_best": stats_dict.get("Tf_best", values["Tf_best"]),
                "T0_mean": stats_dict.get("T0_mean", values["T0_mean"]),
                "Tf_mean": stats_dict.get("Tf_mean", values["Tf_mean"]),
                "nb_runs": stats_dict.get("nb_runs", values["nb_runs"]),
            })
        except Exception:
            pass

    return values


def main():
    parser = argparse.ArgumentParser(
        description="Create a RecuitSimule summary CSV from a folder of RecuitSimule logs."
    )
    parser.add_argument(
        "-l", "--logFolderPath",
        type=valid_folder,
        required=True,
        help="Path to the folder containing RecuitSimule .log files.",
    )
    args = parser.parse_args()

    summary_file_path = os.path.join(args.logFolderPath, "result_summary_recuit.csv")
    fieldnames = [
        "logFile",
        "data_file",
        "p",
        "epsilon",
        "nb_runs",
        "elapsed_time",
        "best",
        "worst",
        "mean",
        "median",
        "std_dev",
        "nb_best_found",
        "cpu_total",
        "cpu_mean",
        "T0_best",
        "Tf_best",
        "T0_mean",
        "Tf_mean",
        "solution_file",
    ]

    with open(summary_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        log_files = sorted([f for f in os.listdir(args.logFolderPath) if f.endswith(".log")])
        for log_file in log_files:
            log_path = os.path.join(args.logFolderPath, log_file)
            row = parse_log_file(log_path)
            writer.writerow(row)

    if log_files:
        print("RecuitSimule summary written to:", summary_file_path)
    else:
        os.remove(summary_file_path)
        print("No log files found; no summary file created.")


if __name__ == "__main__":
    main()
