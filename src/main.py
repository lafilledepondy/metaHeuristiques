import data

from projetUtils import checkSolution, _print_banner, _print_section, pseudo_main


def enum_example():
    from algos import EnumerationSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution

    _print_section("Énumération explicite exemple")

    k = 2
    eps = 0.2
    dataFile = "data/cinqSommets.txt"
    print(f"Fichier données : {dataFile}")
    graph = readGraphFromFile(dataFile)
    sol_init = initializeInitialSolution("random", graph, PartitionSolution(graph, k), eps)
    solution = EnumerationSolver().solve(graph, k, eps, sol_init)
    assert(checkSolution(graph.nbNodes(), solution, k, eps) == True) 
    printSolution(solution)


def gradient_descent_example():
    from algos import GradientSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution

    _print_section("Descente de gradient (algorithme glouton du gradient sans optimisation) exemple")

    k = 2
    eps = 0.2
    nb_iter = 20
    dataFile = "data/vingtEtunSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    initial_solutions = [
        initializeInitialSolution("random", graph, PartitionSolution(graph, k), eps)
        for _ in range(nb_iter)
    ]
    grad_solver = GradientSolver()
    solution, stats = grad_solver.MultiStartGradient(initial_solutions, eps)
    assert(checkSolution(graph.nbNodes(), solution, k, eps) == True) 
    printSolution(solution)
    print("Extra stats:", stats)
    grad_solver.plot(solution, stats)


def kl_enum_example():
    from algos import KernighanAndLinSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution

    _print_section("Kernighan-lin exemple")

    k = 2
    dataFile = "data/cinqCentSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    sol_init = initializeInitialSolution("equally", graph, PartitionSolution(graph, k), 0)
    kl_solver = KernighanAndLinSolver()
    solution = kl_solver.solve_version_enum(graph, k, 0, sol_init)
    assert(checkSolution(graph.nbNodes(), solution, k, 0) == True) 
    printSolution(solution)
    kl_solver.plot(solution)

def kl_heap_example():
    from algos import KernighanAndLinSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution

    _print_section("Kernighan-lin exemple")

    k = 2
    dataFile = "data/cinqCentSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    sol_init = initializeInitialSolution("equally", graph, PartitionSolution(graph, k), 0)
    kl_solver = KernighanAndLinSolver()
    solution = kl_solver.solve(graph, k, 0, sol_init)
    assert(checkSolution(graph.nbNodes(), solution, k, 0) == True) 
    printSolution(solution)
    kl_solver.plot(solution)

def gradHeuristic_example():
    pass

def recuitsimule_example():
    from algos import RecuitSimuleSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution
    _print_section("Recuit simulé exemple")

    k = 2
    eps = 0.2
    nb_iter = 20
    dataFile = "data/vingtEtunSommets.txt"
    print(f"Fichier données : {dataFile}")

    graph = readGraphFromFile(dataFile)
    recuit_solver = RecuitSimuleSolver()
    solution, stats = recuit_solver.MultiStartRecuitSimule(graph, k, eps, nb_iter)
    assert(checkSolution(graph.nbNodes(), solution, k, eps) == True)
    printSolution(solution)
    print("Extra stats:", stats)
    recuit_solver.plot(solution, stats)

def ags_example():
    from algos import SimpleGeneticAlgoSolver, initializeInitialSolution
    from data import readGraphFromFile
    from solution import PartitionSolution, printSolution
    import random

    _print_section("Algorithme génétique simple exemple")

    k = 4
    eps = 0.5
    seed = 45
    dataFile = "data/dixSommets.txt"
    print(f"Fichier données : {dataFile}")
    print(f"Seed aléatoire : {seed}")

    random.seed(seed)

    graph = readGraphFromFile(dataFile)
    sol_init = initializeInitialSolution("random", graph, PartitionSolution(graph, k), eps)
    ags_solver = SimpleGeneticAlgoSolver()
    solution = ags_solver.solve(graph, k, eps, sol_init)
    assert(checkSolution(graph.nbNodes(), solution, k, eps) == True) 
    printSolution(solution)

    ags_solver.plot(solution)

def main():
    _print_banner(
        title="Partitionner des Graphes",
        subtitle="Méta-Heuristiques Projet",
        width=66,
    )

    # === Uncomment to run a specific example ===
    # enum_example()
    # gradient_descent_example()
    # kl_enum_example()
    # kl_heap_example()
    # gradHeuristic_example()
    # recuitsimule_example()
    # ags_example()

    pseudo_main()         


if __name__ == "__main__":
    main()
