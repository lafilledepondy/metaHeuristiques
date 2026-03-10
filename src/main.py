from gui import main as gui_main

import sys
import subprocess
import os


def _print_banner(title, subtitle=None, width=60):
    border = "+" + "=" * (width - 2) + "+"
    body_width = width - 4
    print(border)
    print(f"| {title.center(body_width)} |")
    if subtitle:
        print(f"| {subtitle.center(body_width)} |")
    print(border)


def _print_section(title, width=60):
    print("\n" + title.upper().center(width, "-"))


def pseudo_main():
    """
        * if no arguments are provided, launch the GUI
        * else call solver.py with the given arguments
    """
    if len(sys.argv) == 1:
        gui_main()
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solver_path = os.path.join(script_dir, "solver.py")

    cmd = [sys.executable, solver_path] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def enum_example():
    from algos import EnumerationSolver
    from data import readGraphFromFile
    from solution import printSolution

    _print_section("Énumération explicite exemple")

    k = 2
    eps = 0.2
    dataFile = "data/cinqSommets.txt"
    print(f"Fichier données : {dataFile}")
    graph = readGraphFromFile(dataFile)
    solution = EnumerationSolver().solve(graph, k, eps)
    printSolution(solution)


def gradient_descent_example():
    from algos import GradientSolver
    from data import readGraphFromFile
    from solution import printSolution

    _print_section("Descente de gradient (algorithme glouton du gradient sans optimisation) exemple")

    k = 2
    eps = 0.2
    nb_iter = 20
    dataFile = "data/cinqSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    solution, stats = GradientSolver().solve(graph, k, eps, nb_iter)
    printSolution(solution)
    print("Extra stats:", stats)


def kl_example():
    from algos import KernighanAndLinSolver
    from data import readGraphFromFile
    from solution import printSolution

    _print_section("Kernighan-lin exemple")

    k = 2
    dataFile = "data/cinqSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    solution = KernighanAndLinSolver().solve(graph, k, 0)
    printSolution(solution)


def main():
    _print_banner(
        title="Partitionner des Graphes",
        subtitle="Méta-Heuristiques Projet",
        width=66,
    )

    # === Uncomment to run a specific example ===
    # enum_example()
    # gradient_descent_example()
    # kl_example()

    # === Uncomment to run the GUI or the solver with command-line arguments ===
    # pseudo_main()


if __name__ == "__main__":
    main()
