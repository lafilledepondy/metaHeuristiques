from algos import EnumerationSolver, GradientSolver, KernighanAndLinSolver
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

# Create the parser
parser = argparse.ArgumentParser(
    description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFilePath", type=valid_file, 
                    required=True, help="The path to the data file.")
parser.add_argument("-a", "--algorithm", type=int, 
                    required=True, choices=[1,2,3], help="The algorithm to save the problem.")
parser.add_argument("-p", "--nbClasses", type=positive_int, 
                    required=True, help="The number of classes.")
parser.add_argument("-e", "--epsilon",type=float, 
                    default=0.1, help="Balance tolerance epsilon (default = 0.1)")
parser.add_argument("-t", "--timeLimit", type=positive_int, 
                    default=3600, help="The time limit. Default is 3600 seconds = 1 hour-.")
parser.add_argument("-f", "--solutionFolderPath", type=str, 
                    default="", help="The path to the solution folder (optional, defaults to 'outputs_exe').")
parser.add_argument("-nb", "--nbRuns", type=positive_int, 
                    default=20, help="Number of multi-start runs (only for Gradient)")


# Parse the arguments
args = parser.parse_args()

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
if args.algorithm == 3 and args.nbClasses != 2:
    print("Error: Kernighan-Lin algorithm only supports 2 classes (p=2)")
    sys.exit(1)    

print("----------- ARGUMENTS -----------")
print("Data file path =", args.dataFilePath)
print("Algorithm =", args.algorithm)
print("Number of classes =", args.nbClasses )
print("Epsilon =", args.epsilon)
print("Time limit =", args.timeLimit)
print("Solution folder path =", args.solutionFolderPath)
print("Number of multi-start runs for Gradient =", args.nbRuns)
print("------------------------------------")

# Read the data from the file
dataFileName = os.path.splitext(os.path.basename(args.dataFilePath))[0]
data = readGraphFromFile(args.dataFilePath)

# Solve the problem
begin = time.time()
if args.algorithm == 1:
    solution = EnumerationSolver().solve(data, args.nbClasses, args.epsilon)
elif args.algorithm == 2:
    solution, stats = GradientSolver().solve(
            data,
            args.nbClasses,
            args.epsilon,
            args.nbRuns
        )
    print("Multi-start stats:", stats)
elif args.algorithm == 3:
    solution = KernighanAndLinSolver().solve(data, args.nbClasses, args.epsilon)
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
