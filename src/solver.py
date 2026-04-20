from algos import EnumerationSolver, GradientSolver, KernighanAndLinSolver, GradientHeuristicSolver, RecuitSimuleSolver, SimpleGeneticAlgoSolver, initializeInitialSolution
from data import readGraphFromFile
from data import *
from solution import *
from projetUtils import *
from gui import main as gui_main

import sys
import time
import platform
import argparse
import os

def build_parser():
    parser = argparse.ArgumentParser(
        description="Process command line arguments.")

    parser.add_argument("-d", "--dataFilePath", type=valid_file,
                        required=False, help="The path to the data file.")
    parser.add_argument("-a", "--algorithm", type=float,
                        required=False, choices=[1.0, 2.0, 3.1, 3.2, 4.0, 5.0, 6.0], help="Algorithm to use.")
    parser.add_argument("-p", "--nbClasses", type=positive_int,
                        required=False, help="The number of classes.")
    parser.add_argument("-e", "--epsilon", type=float,
                        default=0.1, help="Balance tolerance epsilon (default = 0.1)")
    parser.add_argument("-t", "--timeLimit", type=positive_int,
                        default=3600, help="The time limit. Default is 3600 seconds.")
    parser.add_argument("-f", "--solutionFolderPath", type=str,
                        default="", help="Optional output folder (default: outputs_exe).")
    parser.add_argument("-nb", "--nbRuns", type=positive_int,
                        default=50, help="Number of multi-start runs (only for Gradient)")    
    parser.add_argument("-k","--kParameter", type=int,
                         default=3, help="k parameter for Gradient Heuristic    (k-th improvement)")
    return parser


def get_interactive_args():
    skip_gui_prompt = os.environ.get("META_SKIP_SOLVER_GUI_PROMPT") == "1"
    if not skip_gui_prompt:
        if prompt_yes_no("Gui ?"):
            gui_main()
            sys.exit(0)

    data_file_path = prompt_typed_value(
        "dataFilePath (relative path to the data file)",
        caster=str,
        validator=valid_file
    )

    algorithm = prompt_choice(
        "Algo\n1.0 enum, 2.0 gradient, 3.1 KL (slow), 3.2 KL (fast), 4.0 Gradient+Heuristic, 5.0 RecuitSimule, 6.0 SimpleGeneticAlgo",
        choices=[1.0, 2.0, 3.1, 3.2, 4.0, 5.0, 6.0]
    )

    if algorithm in (3.1, 3.2):
        nb_classes = 2
        epsilon = 0.0
    else:
        nb_classes = prompt_typed_value(
            "nbClasses",
            caster=int,
            validator=positive_int
        )
        epsilon = prompt_typed_value(
            "epsilon",
            caster=float,
            default=0.1
        )

    time_limit = prompt_typed_value(
        "timeLimit",
        caster=int,
        validator=positive_int,
        default=3600
    )

    nb_runs = 20
    k_parameter = 3
    if algorithm == 2.0 or algorithm == 4.0:
        nb_runs = prompt_typed_value(
            "nbRuns (only for gradient)",
            caster=int,
            validator=positive_int,
            default=20
        )
    if algorithm == 4.0:
        k_parameter = prompt_typed_value(
            "kParameter (only for Gradient Heuristic)",
            caster=int,
            validator=positive_int,
            default=3
        )

    return argparse.Namespace(
        dataFilePath=data_file_path,
        algorithm=algorithm,
        nbClasses=nb_classes,
        epsilon=epsilon,
        timeLimit=time_limit,
        solutionFolderPath="",
        nbRuns=nb_runs,
        kParameter=k_parameter

    )


def should_use_interactive_mode(parsed_args):
    return parsed_args.dataFilePath is None or parsed_args.algorithm is None


parser = build_parser()
cli_args = parser.parse_args()
args = get_interactive_args() if should_use_interactive_mode(cli_args) else cli_args

if args.dataFilePath is None or args.algorithm is None:
    parser.error("Arguments --dataFilePath and --algorithm are required in CLI mode.")

if args.algorithm in (3.1, 3.2):
    args.nbClasses = 2
    args.epsilon = 0.0
elif args.nbClasses is None:
    parser.error("Argument --nbClasses is required for algorithms 1.0, 2.0, 4.0, 5.0, and 6.0.")

# Handle solution folder path
solutionFolderPath = args.solutionFolderPath.strip()
if not solutionFolderPath:
    solutionFolderPath = "outputs_exe"
    if not os.path.exists(solutionFolderPath):
        os.makedirs(solutionFolderPath)
elif not os.path.isdir(solutionFolderPath):
    print(f"Error: Solution folder '{solutionFolderPath}' does not exist")
    sys.exit(1)

# Handle KL & num classes
if (args.algorithm == 3.1 or args.algorithm == 3.2) and args.nbClasses != 2:
    print("Error: Kernighan-Lin algorithm only supports 2 classes (p=2)")
    sys.exit(1)

print("----------- ARGUMENTS -----------")
print("Data file path =", args.dataFilePath)
print("Algorithm =", args.algorithm)
print("Number of classes =", args.nbClasses )
print("Epsilon =", args.epsilon)
print("Time limit =", args.timeLimit)
print("Solution folder path =", args.solutionFolderPath)
print("Number of multi-start runs =", args.nbRuns)
print("------------------------------------")

# Read the data from the file
dataFileName = os.path.splitext(os.path.basename(args.dataFilePath))[0]
data = readGraphFromFile(args.dataFilePath)

# Solve the problem
begin = time.time()
if args.algorithm == 1.0:

    sol_init = initializeInitialSolution(
        "random",
        data,
        PartitionSolution(data, args.nbClasses),
        args.epsilon,
    )
    solution = EnumerationSolver().solve(data, args.nbClasses, args.epsilon, sol_init)
elif args.algorithm == 2.0:
    gradient_solver = GradientSolver()
    initial_solutions = []
    for _ in range(args.nbRuns):
        initial_solutions.append(
            initializeInitialSolution(
                "random",
                data,
                PartitionSolution(data, args.nbClasses),
                args.epsilon,
            )
        )
    solution, stats = gradient_solver.MultiStartGradient(initial_solutions, args.epsilon)
    print("Multi-start stats:", stats)
    gradient_solver.plot(solution, stats)
elif args.algorithm == 3.1:
    sol_init = initializeInitialSolution(
        "equally",
        data,
        PartitionSolution(data, args.nbClasses),
        0,
    )
    solution = KernighanAndLinSolver().solve_version_enum(data, args.nbClasses, 0, sol_init)
elif args.algorithm == 3.2:
    sol_init = initializeInitialSolution(
        "equally",
        data,
        PartitionSolution(data, args.nbClasses),
        0,
    )
    solution = KernighanAndLinSolver().solve(data, args.nbClasses, 0, sol_init)

    
elif args.algorithm == 4.0:
    solver = GradientHeuristicSolver(k=args.kParameter)

    solution, stats = solver.multi_start(
        data,
        args.nbClasses,
        args.epsilon,
        args.nbRuns
    )

    print("Gradient Heuristic Multi-start stats:", stats)
    solver.plot(solution, stats)
elif args.algorithm == 5.0:
    sol_init = initializeInitialSolution(
        "random",
        data,
        PartitionSolution(data, args.nbClasses),
        args.epsilon,
    )
    recuit_solver = RecuitSimuleSolver()
    solution, stats  = recuit_solver.MultiStartRecuitSimule(data, args.nbClasses, args.epsilon)
    print("Recuit Simule stats:", stats)
    recuit_solver.plot(solution)
elif args.algorithm == 6.0:
    sol_init = initializeInitialSolution(
        "random",
        data,
        PartitionSolution(data, args.nbClasses),
        args.epsilon,
    )
    ags_solver = SimpleGeneticAlgoSolver()
    solution = ags_solver.solve(data, args.nbClasses, args.epsilon, sol_init)
    ags_solver.plot(solution)
else:
    print("Unknown algorithm of the problem")
    sys.exit(0)
end = time.time()

# Print the result and exit


if solution is not None:
    print("\ndataFileName =", dataFileName)
    print("solutionValue =", solution.objective_value)
    print("cpuTime =", end - begin)
    # Check the solution
    isFeasible = checkSolution(data.nbNodes(), solution, args.nbClasses, args.epsilon)
    print("isFeasible =", isFeasible)
    # Write the solution to the file
    path_separator = '\\' if platform.system() == 'Windows' else '/'
    solutionFilePath = dataFileName + "_A" + str(args.algorithm) + "_P" + str(args.nbClasses) + "_EPS"+ str(args.epsilon)+ ".sol"
    # solutionFilePath = dataFileName + ".sol"
    solutionFilePath = solutionFolderPath + path_separator + solutionFilePath
    print("Solution is written in the following file: ", solutionFilePath)
    recordSolution(solution, solutionFilePath)
else:
    print("isFeasible =", False)
sys.exit(0)
