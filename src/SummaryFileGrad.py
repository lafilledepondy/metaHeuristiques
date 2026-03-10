from projetUtils import *
import argparse
import os
import re
import ast

# ---------------------- ARGUMENT PARSER ----------------------

parser = argparse.ArgumentParser(description="Process command line arguments.")
parser.add_argument("-l", "--logFolderPath", type=valid_folder, required=True,
                    help="The path to the log folder.")
args = parser.parse_args()

print("----------- ARGUMENTS -----------")
print("Log folder path:", args.logFolderPath)
print("------------------------------------")

# ---------------------- OUTPUT FILE ----------------------

summaryFilePath = os.path.join(args.logFolderPath, 'result_summary.csv')

# Fields we want to extract (clean version)
keys = [
    "Algorithm",
    "Number of classes",
    "Epsilon",
    "Time limit",
    "Number of multi-start runs for Gradient",
    "multi_best",
    "multi_worst",
    "multi_mean",
    "multi_median",
    "multi_std_dev",
    "multi_nb_best_found",
    "multi_nb_runs",
    "solutionValue",
    "cpuTime",
    "isFeasible"
]

with open(summaryFilePath, 'w') as summaryFile:

    # Write header
    summaryFile.write("logFile;" + ";".join(keys) + "\n")

    for logFile in os.listdir(args.logFolderPath):
        if not logFile.endswith('.log'):
            continue

        log_path = os.path.join(args.logFolderPath, logFile)

        values = {key: "missing" for key in keys}

        with open(log_path, 'r') as f:
            content = f.read()

        # ---------------------- SIMPLE KEY = VALUE ----------------------
        simple_patterns = {
            "Algorithm": r"Algorithm\s*=\s*(.+)",
            "Number of classes": r"Number of classes\s*=\s*(.+)",
            "Epsilon": r"Epsilon\s*=\s*(.+)",
            "Time limit": r"Time limit\s*=\s*(.+)",
            "Number of multi-start runs for Gradient":
                r"Number of multi-start runs for Gradient\s*=\s*(.+)",
            "solutionValue": r"solutionValue\s*=\s*(.+)",
            "cpuTime": r"cpuTime\s*=\s*(.+)",
            "isFeasible": r"isFeasible\s*=\s*(.+)",
        }

        for key, pattern in simple_patterns.items():
            match = re.search(pattern, content)
            if match:
                values[key] = match.group(1).strip()

        # ---------------------- MULTI-START STATS ----------------------
        stats_match = re.search(r"Multi-start stats:\s*(\{.*?\})", content)
        if stats_match:
            try:
                stats_dict = ast.literal_eval(stats_match.group(1))

                values["multi_best"] = stats_dict.get("best", "missing")
                values["multi_worst"] = stats_dict.get("worst", "missing")
                values["multi_mean"] = stats_dict.get("mean", "missing")
                values["multi_median"] = stats_dict.get("median", "missing")
                values["multi_std_dev"] = stats_dict.get("std_dev", "missing")
                values["multi_nb_best_found"] = stats_dict.get("nb_best_found", "missing")
                values["multi_nb_runs"] = stats_dict.get("nb_runs", "missing")

            except Exception:
                pass

        # ---------------------- WRITE LINE ----------------------
        summaryFile.write(
            f"{logFile};" + ";".join(str(values[k]) for k in keys) + "\n"
        )

# Remove file if only header
if os.stat(summaryFilePath).st_size <= len("logFile;" + ";".join(keys) + "\n"):
    os.remove(summaryFilePath)
    print("No summary file created because no log files were found")
else:
    print("Summary written to:", summaryFilePath)