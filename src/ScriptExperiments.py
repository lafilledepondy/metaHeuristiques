import os
import subprocess
import sys
import argparse
from datetime import datetime
from projetUtils import positive_int, valid_folder


# Create the parser
parser = argparse.ArgumentParser(description="Run solver experiments over instances, algorithms and class counts")

# Add the arguments
parser.add_argument("-d", "--dataFolderPath", type=valid_folder, 
                    required=True, help="Path to folder with data instances")
parser.add_argument("-f", "--experimentsFolderPath", type=str, 
                    required=True, help="Base path to store experiment outputs (folder will be created)")
parser.add_argument("-a", "--AlgorithmList", nargs='*', type=float, choices=[1.0, 2.0, 3.1, 3.2, 4.0, 5.0, 6.0], 
                    required=True, help="List of algorithms to run (1.0, 2.0, 3.1, 3.2, 4.0, 5.0 or 6.0)")
parser.add_argument("-p", "--nbClassesList", nargs='*', type=positive_int, 
                    required=True, help="List of numbers of classes to test (p values)")
parser.add_argument("-e", "--epsilonList", nargs='*', type=float, 
                    required=True, help="List of epsilon values to test (i.e )")
parser.add_argument("-t", "--timeLimit", type=positive_int, 
                    default=3600, help="Time limit per run in seconds (default 3600 seconds = 1 hour)")
parser.add_argument("-k","--kParameter", type=int,
                     default=3, help="k parameter for Gradient Heuristic (k-th improvement)")


print("Start experiments for graph partitioning problem")

# Parse the arguments
args = parser.parse_args()
args.AlgorithmList = list(dict.fromkeys(args.AlgorithmList))
args.nbClassesList = list(dict.fromkeys(args.nbClassesList))
args.epsilonList = list(dict.fromkeys(args.epsilonList))


print("----------- ARGUMENTS -----------")
print("Data folder path:", args.dataFolderPath)
print("Experiments base folder path:", args.experimentsFolderPath)
print("Algorithms:", args.AlgorithmList)
print("Numbers of classes (p):", args.nbClassesList)
print("Epsilon values:", args.epsilonList)
print("Time limit:", args.timeLimit)
print("nombre de k ameliorations pour Gradient Heuristic =", args.kParameter)
print("------------------------------------")

# Prepare experiments folder with timestamp
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
experimentsFolderPath = f"{args.experimentsFolderPath}_{formatted_time}"
os.makedirs(experimentsFolderPath, exist_ok=True)
solutionFolderPath = os.path.join(experimentsFolderPath, "solutions")
os.makedirs(solutionFolderPath, exist_ok=True)
logFolderPath = os.path.join(experimentsFolderPath, "logs")
os.makedirs(logFolderPath, exist_ok=True)

# Write the current time to a file
with open(os.path.join(experimentsFolderPath, 'time_of_experiments.txt'), 'w') as time_file:
    time_file.write('Experiments were run at this time: ' + str(now))

failed_experiments = []

# Loop over all files in the input folder
for dataFile in sorted(os.listdir(args.dataFolderPath)):
    dataFilePath = os.path.join(args.dataFolderPath, dataFile)
    if not os.path.isfile(dataFilePath):
        continue
    dataFileName = os.path.splitext(os.path.basename(dataFile))[0]

    for algo in args.AlgorithmList:
        for p in args.nbClassesList:
            for eps in args.epsilonList:
                print(f'Solving instance {dataFileName} with algorithm {algo}, p={p}, epsilon={eps}')

                solver_script = os.path.join(os.path.dirname(__file__), 'solver.py')
                cmd = [sys.executable, solver_script, f'-d={dataFilePath}', f'-a={algo}', f'-p={p}', f'-e={eps}',
                    f'-t={args.timeLimit}', f'-f={solutionFolderPath}', f'-k={args.kParameter}']
                print('>', ' '.join(cmd))

                try:
                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeLimit + 5)
                except subprocess.TimeoutExpired:
                    print(f"TIMEOUT: {dataFileName}, algo {algo}, p {p}, eps {eps}")
                    failed_experiments.append((dataFileName, algo, p, eps, 'TIMEOUT'))
                    continue

                log_path = os.path.join(logFolderPath, f'{dataFileName}_A{algo}_P{p}_EPS{eps}.log')
                with open(log_path, 'w', encoding='utf-8') as log_file:
                    log_file.write('--- STDOUT ---\n')
                    log_file.write(process.stdout or '')
                    log_file.write('\n--- STDERR ---\n')
                    log_file.write(process.stderr or '')

                if process.returncode != 0:
                    print(f"ERROR (non-zero exit): instance={dataFileName} algo={algo} p={p} eps={eps}")
                    failed_experiments.append((dataFileName, algo, p, eps, 'ERROR'))

# Report failed experiments
if failed_experiments:
    try:
        from tabulate import tabulate
        print("----------- FAILED EXPERIMENTS -----------")
        print(tabulate(failed_experiments, headers=["Data", "Algo", "p", "eps", "Reason"]))
        with open(os.path.join(experimentsFolderPath, 'failed_experiments.txt'), 'w', encoding='utf-8') as f:
            f.write(tabulate(failed_experiments, headers=["Data", "Algo", "p", "eps", "Reason"]))
    except Exception:
        # fallback: simple write
        with open(os.path.join(experimentsFolderPath, 'failed_experiments.txt'), 'w', encoding='utf-8') as f:
            for item in failed_experiments:
                f.write('\t'.join(map(str, item)) + '\n')
