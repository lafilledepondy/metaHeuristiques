import heapq

from data import *
from solution import *
from projetUtils import checkSolution

import math
import itertools
import time
import statistics
import random
from array import array
import matplotlib.pyplot as plt
import numpy as np

import solution

def initializeInitialSolution(algo:str, data: GraphData, solution: PartitionSolution, epsilon: float):
    n = solution.graph.nbNodes()
    p = solution.p

    if p < 1 or p > n:
        raise ValueError("Invalid number of classes")

    if (algo == "random"):

        max_allowed = math.ceil((n / p) * (1 + epsilon))

        nodes = list(range(n))
        random.shuffle(nodes)

        solution.classe[:] = array('b', [-1] * n)
        solution.class_sizes = array('i', [0] * p)

        for node in nodes:
            # classes that still have room
            feasible_classes = [k for k in range(p) if solution.class_sizes[k] < max_allowed]

            if not feasible_classes:
                raise ValueError("No feasible class left during initialization")

            k = random.choice(feasible_classes)
            solution.set_class(node, k)
    
    elif (algo == "equally"):
        for i in range(n):
            solution.set_class(i, i % p) # 0, 1, 0, 1... for p=2

    else:
        raise ValueError(f"Unknown initialization algorithm: {algo}")
    
    solution.compute_objective()
    return solution    

# =========================================================
# ======================= Solvers =========================
# =========================================================
class Solver:
    def solve(self, data: GraphData, p: int, eps: float, solInit: PartitionSolution) -> PartitionSolution:
        raise NotImplementedError("Solver is an abstract class")

# ================== EnumerationSolver ====================
class EnumerationSolver(Solver):
    def solve(self, data: GraphData, p: int, eps: float, solInit: PartitionSolution) -> PartitionSolution:
        """Énumération (explicite) canonique des partitions en p classes non vides et équilibrées."""
        n = data.nbNodes()
        # Initial bound to reduce the calculation time
        best_val = solInit.compute_objective()
        best_assignment = list(solInit.classe)

        # Iterate over all posible partitions
        for assignment in itertools.product(range(p), repeat=n):

            sol = PartitionSolution(data, p)
            for node, lab in enumerate(assignment):
                sol.set_class(node, lab)

            # Check whether the solution is feasible
            if not checkSolution(n, sol, p, eps):
                continue

            # Calculate the value of the cut
            val = sol.compute_objective() 
            
            # Retain the best solution
            if val < best_val:
                best_val = val
                best_assignment = assignment
        sol = PartitionSolution(data, p)
        for node, lab in enumerate(best_assignment):
            sol.set_class(node, lab)
        sol.compute_objective()
        return sol

# ==================== GradientSolver =====================
class GradientSolver(Solver):
    def __init__(self):
        self.last_path_objectives = []
        self.last_multistart_values = []

    def solve(self, graph: GraphData, p: int, epsilon: float, solInit: PartitionSolution) -> PartitionSolution:
        if solInit is None:
            raise ValueError("GradientSolver requires an external initial solution (solInit)")

        if not checkSolution(graph.nbNodes(), solInit, p, epsilon):
            raise ValueError("Provided initial solution is infeasible")

        solution = PartitionSolution(graph, p)
        solution.classe[:] = solInit.classe[:]
        solution.class_sizes[:] = solInit.class_sizes[:]
        solution.objective_value = solInit.objective_value
        self.last_path_objectives = []
        return self.Gradient(solution, epsilon)
        
    # def initializeInitialSolution(self, solution: PartitionSolution, epsilon: float):
    #     n = solution.graph.nbNodes()
    #     p = solution.p

    #     max_allowed = math.ceil((n / p) * (1 + epsilon))

    #     nodes = list(range(n))
    #     random.shuffle(nodes)

    #     sizes = [0] * p
    #     solution.classe[:] = array('b', [-1] * n)

    #     for node in nodes:
    #         # classes that still have room
    #         feasible_classes = [k for k in range(p) if sizes[k] < max_allowed]

    #         if not feasible_classes:
    #             raise ValueError("No feasible class left during initialization")

    #         k = random.choice(feasible_classes)
    #         solution.classe[node] = k
    #         sizes[k] += 1

    #     solution.compute_objective()
    #     return solution
    
    def Gradient(self, solution: PartitionSolution, eps: float) -> PartitionSolution:
        """
        Descente de gradient -version récursive -
        Retourne un optimum local.
        """
        n = solution.graph.nbNodes()
        p = solution.p
        adj = solution.graph.adjacency()

        best_solution = solution
        best_value = solution.compute_objective()

        if not self.last_path_objectives:
            self.last_path_objectives.append(best_value)

        # Parcours du voisinage V(S)
        for node in range(n):
            old_class = solution.classe[node]

            for new_class in range(p):
                if new_class == old_class:
                    continue

                # Créer un voisin
                neighbor = PartitionSolution(solution.graph, p)
                neighbor.classe[:] = solution.classe[:]
                neighbor.class_sizes[:] = solution.class_sizes[:]
                neighbor.objective_value = solution.objective_value

                move_node(neighbor, adj, node, new_class)

                # Vérifier la faisabilité
                if not checkSolution(n, neighbor, p, eps):
                    continue

                val = neighbor.compute_objective()

                if val < best_value:
                    best_solution = neighbor
                    best_value = val

        # Condition d’arrêt
        if best_solution is solution:
            return solution
        else:
            self.last_path_objectives.append(best_value)
            return self.Gradient(best_solution, eps) 

    def MultiStartGradient(self, initial_solutions: list[PartitionSolution], epsilon: float):
        """
        Runs Gradient descent multiple times and computes statistics
        on local optima.
        """
        if not initial_solutions:
            raise ValueError("initial_solutions must contain at least one solution")

        best_solution = None
        best_value = float("inf")

        values = []          # objective values of all runs
        solutions = []       # keep solutions if needed

        for init_sol in initial_solutions:
            # Each run starts from an externally-constructed initial solution.
            local_opt = self.solve(init_sol.graph, init_sol.p, epsilon, init_sol)
            val = local_opt.compute_objective()

            values.append(val)
            solutions.append(local_opt)

            # Track best solution
            if val < best_value:
                best_value = val
                best_solution = local_opt

        self.last_multistart_values = values[:]

        # ===== Statistics =====
        worst_value = max(values)
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        nb_best_found = values.count(best_value)

        stats = {
            "best": best_value,
            "worst": worst_value,
            "mean": mean_value,
            "median": median_value,
            "std_dev": std_dev,
            "nb_best_found": nb_best_found,
            "nb_runs": len(initial_solutions)
        }

        return best_solution, stats           

    def plot(self, best_solution: PartitionSolution | dict | None = None, stats: dict | None = None):
        if not self.last_path_objectives and not self.last_multistart_values:
            raise ValueError("No Gradient history available. Run solve() or MultiStartGradient() before plotting.")

        if stats is None and isinstance(best_solution, dict):
            stats = best_solution

        has_multi = bool(self.last_multistart_values)

        # ===== Single-run analysis: convergence path =====
        if not has_multi:
            values = np.array(self.last_path_objectives, dtype=float)
            iters = np.arange(len(values))
            best_so_far = np.minimum.accumulate(values)
            improv = np.maximum(0.0, values[:-1] - values[1:]) if len(values) > 1 else np.array([])

            fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
            ax_path, ax_improv, ax_ratio, ax_summary = axes

            ax_path.plot(iters, values, color="#457b9d", linewidth=1.8, marker="o", markersize=4, label="Objectif")
            ax_path.plot(iters, best_so_far, color="#e63946", linewidth=1.6, linestyle="--", label="Best-so-far")
            ax_path.set_xlabel("Itération")
            ax_path.set_ylabel("Valeur de l'objectif")
            ax_path.set_title("Trajectoire de convergence")
            ax_path.grid(alpha=0.2)
            ax_path.legend()

            if len(improv) > 0:
                ax_improv.bar(np.arange(1, len(values)), improv, color="#2a9d8f", alpha=0.85)
            ax_improv.set_xlabel("Itération")
            ax_improv.set_ylabel("Gain")
            ax_improv.set_title("Amélioration par étape")
            ax_improv.grid(alpha=0.2, axis="y")

            if len(values) > 0 and values[0] != 0:
                relative = values / values[0]
            else:
                relative = np.ones_like(values)
            ax_ratio.plot(iters, relative, color="#f4a261", linewidth=1.8, marker="o", markersize=3)
            ax_ratio.set_xlabel("Itération")
            ax_ratio.set_ylabel("Objectif / Objectif initial")
            ax_ratio.set_title("Progrès relatif")
            ax_ratio.grid(alpha=0.2)

            total_gain = float(values[0] - values[-1]) if len(values) > 1 else 0.0
            gain_pct = (100.0 * total_gain / values[0]) if len(values) > 0 and values[0] != 0 else 0.0
            n_improving_steps = int(np.sum(improv > 0)) if len(improv) > 0 else 0
            rows = [
                ["initial", float(values[0]) if len(values) > 0 else 0.0],
                ["final", float(values[-1]) if len(values) > 0 else 0.0],
                ["best", float(np.min(values)) if len(values) > 0 else 0.0],
                ["nb_iterations", len(values)],
                ["nb_improving_steps", n_improving_steps],
                ["total_gain", total_gain],
                ["gain_pct", gain_pct],
            ]

            ax_summary.axis("off")
            table = ax_summary.table(
                cellText=[[k, f"{v:.4f}" if isinstance(v, (float, int)) and k not in {"nb_iterations", "nb_improving_steps"} else v] for k, v in rows],
                colLabels=["Stat", "Value"],
                loc="center",
                cellLoc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8.8)
            table.scale(1.0, 1.3)
            ax_summary.set_title("Résumé convergence")

            fig.suptitle("Analyse Gradient - Run unique", fontsize=11)
            fig.tight_layout()
            plt.show()
            return

        # ===== Multi-start analysis: distribution across runs =====
        values = np.array(self.last_multistart_values, dtype=float)
        fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
        ax_hist, ax_box, ax_ecdf, ax_summary = axes

        bins = min(20, max(5, len(values)))
        ax_hist.hist(values, bins=bins, color="#457b9d", alpha=0.85)
        best_val = None
        if isinstance(best_solution, dict):
            if "best" in best_solution:
                best_val = float(best_solution["best"])
        elif best_solution is not None:
            best_val = float(best_solution.compute_objective())
        if best_val is not None:
            ax_hist.axvline(best_val, color="#e63946", linestyle="--", linewidth=1.6, label="Best fourni")
        elif len(values) > 0:
            best_val = float(np.min(values))
            ax_hist.axvline(best_val, color="#e63946", linestyle="--", linewidth=1.6, label="Best observé")
        ax_hist.set_xlabel("Valeur de l'objectif")
        ax_hist.set_ylabel("Fréquence")
        ax_hist.set_title("Distribution des runs")
        ax_hist.grid(alpha=0.2)
        if len(values) > 0:
            ax_hist.legend()

        ax_box.boxplot(
            values,
            vert=False,
            patch_artist=True,
            boxprops={"facecolor": "#a8dadc", "color": "#457b9d"},
            medianprops={"color": "#e63946", "linewidth": 2},
            whiskerprops={"color": "#457b9d"},
            capprops={"color": "#457b9d"},
        )
        ax_box.set_yticks([1])
        ax_box.set_yticklabels(["Runs"])
        ax_box.set_xlabel("Valeur de l'objectif")
        ax_box.set_title("Boxplot")
        ax_box.grid(alpha=0.2, axis="x")

        sorted_vals = np.sort(values)
        ecdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax_ecdf.step(sorted_vals, ecdf, where="post", color="#264653", linewidth=1.8)
        ax_ecdf.set_xlabel("Valeur de l'objectif")
        ax_ecdf.set_ylabel("Proportion cumulée")
        ax_ecdf.set_ylim(0, 1.02)
        ax_ecdf.set_title("ECDF")
        ax_ecdf.grid(alpha=0.2)

        ax_summary.axis("off")
        rows = []
        if stats is not None:
            for key in ["best", "worst", "mean", "median", "std_dev", "nb_best_found", "nb_runs"]:
                if key in stats:
                    rows.append([key, stats[key]])
        else:
            rows = [
                ["best", float(np.min(values))],
                ["worst", float(np.max(values))],
                ["mean", float(np.mean(values))],
                ["median", float(np.median(values))],
                ["q1", float(np.percentile(values, 25))],
                ["q3", float(np.percentile(values, 75))],
                ["std_dev", float(np.std(values, ddof=1)) if len(values) > 1 else 0.0],
                ["nb_runs", len(values)],
            ]

        table = ax_summary.table(
            cellText=[[k, f"{v:.4f}" if isinstance(v, (float, int)) and k not in {"nb_runs", "nb_best_found"} else v] for k, v in rows],
            colLabels=["Stat", "Value"],
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.8)
        table.scale(1.0, 1.25)
        ax_summary.set_title("Résumé des stats")

        fig.suptitle("Analyse Gradient - Multi-start", fontsize=11)
        fig.tight_layout()
        plt.show()

# ================ KernighanAndLinSolver ==================
class KernighanAndLinSolver(Solver):
    # def initializeSolution(self, data: GraphData, p: int) -> PartitionSolution:
    #     n = data.nbNodes()
    #     sol = PartitionSolution(data, p)
    #     for i in range(n):
    #         sol.set_class(i, i % p) # 0, 1, 0, 1... for p=2
    #     sol.compute_objective() 
    #     return sol
    
    def calculerDx(self, solution: PartitionSolution) -> list[float]:
        """D[x] = E[x] - I[x]"""        
        n = solution.graph.nbNodes()
        adj = solution.graph.adjacency()
        Dx = [0.0] * n 
        
        for noeud in range(n):
            noeud_class = solution.classe[noeud]

            for voisin, w in adj[noeud]: # pour tout noeud : w = 1
                voisin_class = solution.classe[voisin]

                # /\ inter-intra
                if voisin_class == noeud_class:
                    Dx[noeud] -= float(w)  # I[x]
                else:
                    Dx[noeud] += float(w)  # E[x]
        return Dx
    
    def computeGain(self, solution: PartitionSolution, node_a, node_b, Dx):
        """delta = D[a] + D[b] - 2 * w(a,b)"""
        edge_weight = solution.graph.edgeWeight(node_a, node_b) # just in case even though we know that for all edges w =1 
        return Dx[node_a] + Dx[node_b] - 2 * edge_weight
    
    def updateDxAfterSwap(self, solution: PartitionSolution, node_a, node_b, Dx):
        n = solution.graph.nbNodes()
        adj = solution.graph.adjacency()
        
        Dx[node_a], Dx[node_b] = float("inf"), float("inf") # indicateur 'inf' --> noeuds déjà échangés
        # plus considérés pour les prochains swaps
        
        for node in range(n):
            if Dx[node] == float("inf"): # skip already swapped nodes
                continue
            
            # NB : Dx <- Dx -w -w = Dx - 2w
            for neighbor, w in adj[node]:
                if neighbor == node_a:
                    if solution.classe[node] == solution.classe[node_b]:
                        Dx[node] -= 2 * w  # external --> internal
                    else:
                        Dx[node] += 2 * w  # internal --> external
                    break
            
            for neighbor, w in adj[node]:
                if neighbor == node_b:
                    if solution.classe[node] == solution.classe[node_a]:
                        Dx[node] -= 2 * w  # external --> internal
                    else:
                        Dx[node] += 2 * w  # internal --> external
                    break

    def solve_version_enum(self, data: GraphData, p: int, eps: float = 0.0, solInit: PartitionSolution = None) -> PartitionSolution:
        # cas : p != 2 est traité dans solver.py
        if solInit is None:
            raise ValueError("KernighanAndLinSolver requires an external initial solution (solInit)")
        solution = solInit
        listeGain = 1

        while listeGain > 0:
            Dx = self.calculerDx(solution)
            
            swap_sequence = [] # <> [(La, Lb_1), ...]
            listeGain = []
            prison = set()
            
            classes = solution.classes()
            # split into respective classes
            C1 = set(classes.get(0, []))  
            C2 = set(classes.get(1, []))  
            n_swaps =  min(len(C1), len(C2))

            for _ in range(n_swaps):
                max_gain = float("-inf")
                best_pair = None

                # choisir a in C_1 et b in C_2 qui maximisent le listeGain
                for a in C1 - prison:
                    for b in C2 - prison:
                        gain = self.computeGain(solution, a, b, Dx)
                        if gain > max_gain:
                            max_gain = gain
                            best_pair = (a, b)
                
                # aucun swap possible
                if best_pair is None:
                    break
                
                # sinon append in swap_sequence
                a, b = best_pair
                swap_sequence.append((a, b))
                listeGain.append(max_gain)
                prison.update({a, b})
                
                self.updateDxAfterSwap(solution, a, b, Dx)
            
            if not listeGain:
                break

            cumsum = [sum(listeGain[:i+1]) for i in range(len(listeGain))] # on considere que i_0 = 0
            listeGain = max(cumsum)
            
            if listeGain > 0:
                k = cumsum.index(listeGain)
                
                for i in range(k+1):
                    a, b = swap_sequence[i]
                    swap_nodes(solution, a, b) # apply swap

        return solution    

    def solve(self, data: GraphData, p: int, eps: float = 0.0, solInit: PartitionSolution = None) -> PartitionSolution:
        # cas : p != 2 est traité dans solver.py
        if solInit is None:
            raise ValueError("KernighanAndLinSolver requires an external initial solution (solInit)")
        solution = solInit
        listeGain = 1

        while listeGain > 0:
            Dx = self.calculerDx(solution)

            swap_sequence = [] # <> [(La, Lb_1), ...]
            listeGain = []
            prison = set()

            classes = solution.classes()
            # split into respective classes
            C1 = set(classes.get(0, []))
            C2 = set(classes.get(1, []))
            n_swaps = min(len(C1), len(C2))

            # build initial heap
            heap = []
            for a in C1:
                for b in C2:
                    g = self.computeGain(solution, a, b, Dx)
                    heapq.heappush(heap, (-g, a, b)) # -g car heapq garde le min dans le root on veut garder le max dans le root

            # choisir a in C_1 et b in C_2 qui maximisent le listeGain
            for _ in range(n_swaps):
                max_gain = float("-inf")
                best_pair = None

                # lazy iterations
                # on change la structure de données pour éviter de recalculer tous les gains à chaque itération 
                # en utilisant le heapq 
                # cela nous permet de trouver le meilleur swap en O(log(n)) au lieu de O(n^2) à chaque itération
                # on garde le max gain dans le racine de l'arbre(root) 
                # ceci est possible car on fait `-g` ce qui garde bien le max dans le root 
                # de defaut heapq garde le min dans le root 
                # ensuite on convertit en abs(g) 
                while heap:
                    neg_g, a, b = heapq.heappop(heap)
                    if a in prison or b in prison:
                        continue

                    true_g = self.computeGain(solution, a, b, Dx)

                    if abs(true_g + neg_g) > 1e-9:
                        heapq.heappush(heap, (-true_g, a, b))
                        continue

                    best_pair = (a, b)
                    max_gain = true_g
                    break

                # aucun swap possible
                if best_pair is None:
                    break

                # sinon append in swap_sequence
                a, b = best_pair
                swap_sequence.append((a, b))
                listeGain.append(max_gain)
                prison.update({a, b})

                # update Dx incrementally
                adj = solution.graph.adjacency()
                for x in range(solution.graph.nbNodes()):
                    if x in prison:
                        continue
                    for y, w in adj[x]:
                        if y == a:
                            if solution.classe[x] == solution.classe[a]:
                                Dx[x] += 2 * w
                            else:
                                Dx[x] -= 2 * w
                        elif y == b:
                            if solution.classe[x] == solution.classe[b]:
                                Dx[x] += 2 * w
                            else:
                                Dx[x] -= 2 * w

                # update heap locally
                affected = set()
                for v, _ in adj[a]:
                    affected.add(v)
                for v, _ in adj[b]:
                    affected.add(v)

                for x in affected:
                    if x in prison:
                        continue
                    if x in C1:
                        for y in C2 - prison:
                            g = Dx[x] + Dx[y] - 2 * solution.graph.edgeWeight(x, y)
                            heapq.heappush(heap, (-g, x, y))
                    else:
                        for y in C1 - prison:
                            g = Dx[y] + Dx[x] - 2 * solution.graph.edgeWeight(y, x)
                            heapq.heappush(heap, (-g, y, x))

            if not listeGain:
                break

            cumsum = [sum(listeGain[: i + 1]) for i in range(len(listeGain))]
            listeGain = max(cumsum)

            if listeGain > 0:
                k = cumsum.index(listeGain)
                for i in range(k + 1):
                    a, b = swap_sequence[i]
                    swap_nodes(solution, a, b)
        return solution

# ================ Gradient&HeuristicSolver ==================
class GradientHeuristicSolver(Solver):
    def __init__(self, k: int = 1):
        self.k = k
        self.last_path_objectives = []
        self.last_multistart_values = []

    def solve(self, data: GraphData, p: int, eps: float, solInit: PartitionSolution) -> PartitionSolution:
        if solInit is None:
            raise ValueError("Initial solution required")

        n = data.nbNodes()
        adj = data.adjacency()

        self.last_path_objectives = []
        self.last_multistart_values = []

        if not checkSolution(n, solInit, p, eps):
            raise ValueError("Initial solution infeasible")

        # Ci <- C0 (Initialisation)
        current_solution = PartitionSolution(data, p)
        current_solution.classe[:] = solInit.classe[:]
        current_solution.class_sizes[:] = solInit.class_sizes[:]
        current_solution.objective_value = solInit.objective_value

        self.last_path_objectives.append(current_solution.compute_objective())

        finished = False
        while not finished:
            current_f = current_solution.compute_objective()
            
            # Variables for the inner loop (TantQue j < k)
            j = 0
            saved_candidate = None
            
            # Explore neighborhood V(Ci)
            # We iterate through nodes and possible class changes
            found_kth = False
            for node in range(n):
                if found_kth: break
                
                old_class = current_solution.classe[node]
                for new_class in range(p):
                    if new_class == old_class:
                        continue

                    # Generate neighbor C
                    neighbor = PartitionSolution(data, p)
                    neighbor.classe[:] = current_solution.classe[:]
                    neighbor.class_sizes[:] = current_solution.class_sizes[:]
                    
                    move_node(neighbor, adj, node, new_class)

                    # Check feasibility
                    if not checkSolution(n, neighbor, p, eps):
                        continue

                    # If f(C) is better than f(Ci)
                    neighbor_f = neighbor.compute_objective()
                    if neighbor_f < current_f:
                        j += 1
                        saved_candidate = neighbor # Sauvegarder C
                        
                        # Stop if we reached the k-th improvement
                        if j >= self.k:
                            found_kth = True
                            break
            
            # Si Sauvegarde existe Alors
            if saved_candidate is not None:
                current_solution = saved_candidate
                # i <- i + 1 (Implicit in while loop)
                self.last_path_objectives.append(current_solution.compute_objective())
            else:
                # Sinon fini <- vrai
                finished = True

        return current_solution
    
    def multi_start(self, data, p, eps, nb_runs):
        best_solution = None
        best_value = float("inf")
        values = []

        self.last_path_objectives = []

        for _ in range(nb_runs):
            sol_init = initializeInitialSolution(
                "random",
                data,
                PartitionSolution(data, p),
                eps
            )

            local_opt = self.solve(data, p, eps, sol_init)
            val = local_opt.compute_objective()

            values.append(val)

            if val < best_value:
                best_value = val
                best_solution = local_opt

        self.last_multistart_values = values

        import statistics
        stats = {
            "best": best_value,
            "worst": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "nb_runs": nb_runs,
            "k": self.k
        }

        return best_solution, stats 
    def plot(self, best_solution=None, stats=None):
        if not self.last_path_objectives and not self.last_multistart_values:
            raise ValueError("No Gradient history available. Run solve() or multi_start() before plotting.")

        if stats is None and isinstance(best_solution, dict):
            stats = best_solution

        has_multi = bool(self.last_multistart_values)

        # Mode Run Unique
        if not has_multi:
            values = np.array(self.last_path_objectives, dtype=float)
            iters = np.arange(len(values))
            best_so_far = np.minimum.accumulate(values)
            improv = np.maximum(0.0, values[:-1] - values[1:]) if len(values) > 1 else np.array([])

            fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
            ax_path, ax_improv, ax_ratio, ax_summary = axes

            ax_path.plot(iters, values, color="#457b9d", linewidth=1.8, marker="o", markersize=4, label="Objectif")
            ax_path.plot(iters, best_so_far, color="#e63946", linewidth=1.6, linestyle="--", label="Best-so-far")
            ax_path.set_xlabel("Itération")
            ax_path.set_ylabel("Valeur de l'objectif")
            ax_path.set_title("Trajectoire de convergence")
            ax_path.grid(alpha=0.2)
            ax_path.legend()

            if len(improv) > 0:
                ax_improv.bar(np.arange(1, len(values)), improv, color="#2a9d8f", alpha=0.85)
            ax_improv.set_xlabel("Itération")
            ax_improv.set_ylabel("Gain")
            ax_improv.set_title("Amélioration par étape")
            ax_improv.grid(alpha=0.2, axis="y")

            if len(values) > 0 and values[0] != 0:
                relative = values / values[0]
            else:
                relative = np.ones_like(values)
            ax_ratio.plot(iters, relative, color="#f4a261", linewidth=1.8, marker="o", markersize=3)
            ax_ratio.set_xlabel("Itération")
            ax_ratio.set_ylabel("Progrès relatif")
            ax_ratio.set_title("Progrès relatif")
            ax_ratio.grid(alpha=0.2)

            total_gain = float(values[0] - values[-1]) if len(values) > 1 else 0.0
            gain_pct = (100.0 * total_gain / values[0]) if len(values) > 0 and values[0] != 0 else 0.0
            n_improving_steps = int(np.sum(improv > 0)) if len(improv) > 0 else 0
            rows = [
                ["initial", float(values[0]) if len(values) > 0 else 0.0],
                ["final", float(values[-1]) if len(values) > 0 else 0.0],
                ["best", float(np.min(values)) if len(values) > 0 else 0.0],
                ["nb_iterations", len(values)],
                ["nb_improving_steps", n_improving_steps],
                ["total_gain", total_gain],
                ["gain_pct", gain_pct],
            ]

            ax_summary.axis("off")
            table = ax_summary.table(
                cellText=[[k, f"{v:.4f}" if isinstance(v, (float, int)) and k not in {"nb_iterations", "nb_improving_steps"} else v] for k, v in rows],
                colLabels=["Stat", "Value"],
                loc="center",
                cellLoc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8.8)
            table.scale(1.0, 1.3)
            ax_summary.set_title("Résumé convergence")

            fig.suptitle(f"Analyse Gradient Amélioré (k={self.k}) - Run unique", fontsize=11)
            fig.tight_layout()
            plt.show()
            return

        # Mode Multi-start
        values = np.array(self.last_multistart_values, dtype=float)
        fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
        ax_hist, ax_box, ax_ecdf, ax_summary = axes

        bins = min(20, max(5, len(values)))
        ax_hist.hist(values, bins=bins, color="#457b9d", alpha=0.85)
        
        # Gestion du meilleur résultat pour le trait vertical
        best_val = None
        if stats and "best" in stats:
            best_val = stats["best"]
        elif len(values) > 0:
            best_val = np.min(values)
            
        if best_val is not None:
            ax_hist.axvline(best_val, color="#e63946", linestyle="--", label="Meilleur")
        
        ax_hist.set_title("Distribution des runs")
        ax_hist.grid(alpha=0.2)
        ax_hist.legend()

        ax_box.boxplot(values, vert=False, patch_artist=True, boxprops={"facecolor": "#a8dadc"})
        ax_box.set_title("Boîte à moustaches")

        sorted_vals = np.sort(values)
        ecdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax_ecdf.step(sorted_vals, ecdf, where="post", color="#264653")
        ax_ecdf.set_title("ECDF (Confiance)")

        ax_summary.axis("off")
        if stats:
            rows = [[k, v] for k, v in stats.items()]
        else:
            rows = [["best", np.min(values)], ["mean", np.mean(values)], ["nb_runs", len(values)]]

        ax_summary.table(cellText=[[k, f"{v:.2f}" if isinstance(v, float) else v] for k, v in rows], 
                         colLabels=["Stat", "Valeur"], loc="center").scale(1.0, 1.3)
        
        fig.suptitle(f"Analyse Gradient Amélioré (k={self.k}) - Multi-start", fontsize=11)
        fig.tight_layout()
        plt.show()

# ================== RecuitSimuleSolver ====================
class RecuitSimuleSolver(Solver):
    def __init__(self):
        self.last_best_history = []
        self.last_temperature_history = []
        self.last_acceptance_history = []
        self.last_multistart_values = []

    def initial_temperature(self, X, p, eps, tau=0.8, sample_size=None):
        """ Méthode de Kirkpatrick analytique"""
        n = X.graph.nbNodes()
        adj = X.graph.adjacency()

        deltas = []
        if not sample_size: 
            sample_size = max(50, int(n * (p - 1) * 0.1))

        for _ in range(sample_size):
            neighbor = random_neighbor(X, adj, p, eps)
            if neighbor is None:
                continue
            node, new_class, delta = neighbor
            if delta != 0:
                deltas.append(abs(delta)) 
        if not deltas:
            return 1.0
        
        avg_delta = sum(deltas) / len(deltas)
        return -avg_delta / math.log(tau)
    
    def cooling(self, T, alpha = 0.9):
        return alpha*T
        
    def _run_recuit(self, solInit: PartitionSolution, p: int, eps: float):
        """Run one simulated annealing search and return solution with temperatures."""
        n = solInit.graph.nbNodes()
        adj = solInit.graph.adjacency()

        self.last_best_history = []
        self.last_temperature_history = []
        self.last_acceptance_history = []

        # Initial Solution
        X = solInit
        X.compute_objective()
        val = X.objective_value
        best_classe = X.classe[:]
        best_val = val
        
        # Temperatures
        T0 = self.initial_temperature(X, p, eps)
        T_final = 0.01 * T0
        T = T0

        self.last_best_history.append(best_val)
        self.last_temperature_history.append(T)
        self.last_acceptance_history.append(0.0)

        while T > T_final:
            accepted_moves = 0
            attempted_moves = 0
            for _ in range(n**2):
                neighbor = random_neighbor(X, adj, p, eps)
                if neighbor is None:
                    continue
                attempted_moves += 1
                node, new_class, delta = neighbor

                if delta < 0 or random.random() < math.exp(-delta / T):
                    move_node(X, adj, node, new_class)
                    val += delta
                    accepted_moves += 1
                    # Save best solution
                    if val < best_val:
                        best_classe = X.classe[:]
                        best_val = val

            acceptance_rate = (accepted_moves / attempted_moves) if attempted_moves > 0 else 0.0
            self.last_best_history.append(best_val)
            self.last_temperature_history.append(T)
            self.last_acceptance_history.append(acceptance_rate)

            T = self.cooling(T)  
        X_best = PartitionSolution(X.graph, X.p)
        X_best.classe = best_classe
        X_best.objective_value = best_val
        return X_best, T0, T_final


    def solve(self, data: GraphData, p: int, eps: float, solInit: PartitionSolution) -> PartitionSolution:
        return self._run_recuit(solInit, p, eps)[0]
    
    def MultiStartRecuitSimule(self, data: GraphData, p: int, eps: float, nb_runs: int =20):
        if nb_runs < 1:
            raise ValueError("nb_runs must be at least 1")
        self.last_multistart_values = []
        best_solution = None
        best_value = float("inf")
        values = []
        cpu_times = []
        T0_values = []
        Tf_values = []
        best_T0 = None
        best_Tf = None
        for _ in range(nb_runs):
            sol_init = initializeInitialSolution(
                "random",
                data,
                PartitionSolution(data, p),
                eps,
            )
            start_time = time.time()
            local_opt, T0, Tf = self._run_recuit(sol_init, p, eps)
            run_time = time.time() - start_time
            val = local_opt.compute_objective()
            values.append(val)
            cpu_times.append(run_time)
            T0_values.append(T0)
            Tf_values.append(Tf)
            if val < best_value:
                best_value = val
                best_solution = local_opt
                best_T0 = T0
                best_Tf = Tf
        self.last_multistart_values = values[:]
        worst_value = max(values)
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        nb_best_found = values.count(best_value)
        stats = {
            "best": best_value,
            "worst": worst_value,
            "mean": mean_value,
            "median": median_value,
            "std_dev": std_dev,
            "nb_best_found": nb_best_found,
            "cpu_total": sum(cpu_times),
            "cpu_mean": statistics.mean(cpu_times),
            "T0_best": best_T0,
            "Tf_best": best_Tf,
            "T0_mean": statistics.mean(T0_values),
            "Tf_mean": statistics.mean(Tf_values),
            "nb_runs": nb_runs,
        }
        return best_solution, stats
    
    def plot(self, best_solution: PartitionSolution | dict | None = None, stats: dict | None = None):
        if not self.last_best_history and not self.last_multistart_values:
            raise ValueError("No Recuit history available. Run solve() or MultiStartRecuitSimule() before plotting.")

        if stats is None and isinstance(best_solution, dict):
            stats = best_solution

        has_single = bool(self.last_best_history and self.last_temperature_history and self.last_acceptance_history)
        if has_single:
            best_hist = np.array(self.last_best_history, dtype=float)
            temp_hist = np.array(self.last_temperature_history, dtype=float)
            acceptance_hist = np.array(self.last_acceptance_history, dtype=float)

            fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
            ax_best, ax_temp, ax_accept, ax_summary = axes

            ax_best.plot(best_hist, color="#2a9d8f", linewidth=1.8, marker="o", markersize=3)
            ax_best.set_xlabel("Palier")
            ax_best.set_ylabel("Meilleure valeur")
            ax_best.set_title("Best-so-far")
            ax_best.grid(alpha=0.2)

            ax_temp.plot(temp_hist, color="#f4a261", linewidth=1.8, marker="o", markersize=3)
            ax_temp.set_yscale("log")
            ax_temp.set_xlabel("Palier")
            ax_temp.set_ylabel("Température")
            ax_temp.set_title("Refroidissement")
            ax_temp.grid(alpha=0.2)

            ax_accept.plot(acceptance_hist, color="#e63946", linewidth=1.8, marker="o", markersize=3)
            ax_accept.axhline(float(np.mean(acceptance_hist)) if len(acceptance_hist) > 0 else 0.0, color="#264653", linestyle="--", linewidth=1.2, label="Moyenne")
            ax_accept.set_xlabel("Palier")
            ax_accept.set_ylabel("Taux d'acceptation")
            ax_accept.set_ylim(0, 1.05)
            ax_accept.set_title("Acceptation des moves")
            ax_accept.grid(alpha=0.2)
            if len(acceptance_hist) > 0:
                ax_accept.legend()

            ax_summary.axis("off")
            rows = []
            if stats is not None:
                for key in ["best", "worst", "mean", "median", "std_dev", "nb_runs", "T0_best", "Tf_best", "T0_mean", "Tf_mean"]:
                    if key in stats:
                        rows.append([key, stats[key]])
                rows.append(["accept_rate_mean", float(np.mean(acceptance_hist)) if len(acceptance_hist) > 0 else 0.0])
            else:
                rows = [
                    ["best", float(np.min(best_hist))],
                    ["worst", float(np.max(best_hist))],
                    ["mean", float(np.mean(best_hist))],
                    ["median", float(np.median(best_hist))],
                    ["std_dev", float(np.std(best_hist, ddof=1)) if len(best_hist) > 1 else 0.0],
                    ["accept_rate_mean", float(np.mean(acceptance_hist)) if len(acceptance_hist) > 0 else 0.0],
                ]

            table = ax_summary.table(
                cellText=[[k, f"{v:.4f}" if isinstance(v, (float, int)) else v] for k, v in rows],
                colLabels=["Stat", "Value"],
                loc="center",
                cellLoc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8.5)
            table.scale(1.0, 1.3)
            ax_summary.set_title("Résumé des stats")

            fig.suptitle("Analyse Recuit Simulé", fontsize=11)
            fig.tight_layout()
            plt.show()
            return

        has_multi = bool(self.last_multistart_values)
        values = np.array(self.last_multistart_values, dtype=float)
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
        ax_multi, ax_box, ax_summary = axes

        bins = min(20, max(5, len(values)))
        ax_multi.hist(values, bins=bins, color="#457b9d", alpha=0.85)
        best_val = None
        if isinstance(best_solution, dict):
            if "best" in best_solution:
                best_val = float(best_solution["best"])
        elif best_solution is not None:
            best_val = float(best_solution.compute_objective())
        if best_val is not None:
            ax_multi.axvline(best_val, color="#e63946", linestyle="--", linewidth=1.6, label="Best fourni")
        elif len(values) > 0:
            best_val = float(np.min(values))
            ax_multi.axvline(best_val, color="#e63946", linestyle="--", linewidth=1.6, label="Best observé")
        ax_multi.set_xlabel("Valeur de l'objectif")
        ax_multi.set_ylabel("Fréquence")
        ax_multi.set_title("Fréquence des runs")
        ax_multi.grid(alpha=0.2)
        if len(values) > 0:
            ax_multi.legend()

        ax_box.boxplot(
            values,
            vert=False,
            patch_artist=True,
            boxprops={"facecolor": "#a8dadc", "color": "#457b9d"},
            medianprops={"color": "#e63946", "linewidth": 2},
            whiskerprops={"color": "#457b9d"},
            capprops={"color": "#457b9d"},
        )
        ax_box.set_yticks([1])
        ax_box.set_yticklabels(["Runs"])
        ax_box.set_xlabel("Valeur de l'objectif")
        ax_box.set_title("Boxplot horizontal")
        ax_box.grid(alpha=0.2, axis="x")

        ax_summary.axis("off")
        rows = []
        if stats is not None:
            for key in ["best", "worst", "mean", "median", "std_dev", "nb_best_found", "nb_runs", "cpu_total", "cpu_mean", "T0_best", "Tf_best", "T0_mean", "Tf_mean"]:
                if key in stats:
                    rows.append([key, stats[key]])
        else:
            rows = [
                ["best", float(np.min(values))],
                ["worst", float(np.max(values))],
                ["mean", float(np.mean(values))],
                ["median", float(np.median(values))],
                ["std_dev", float(np.std(values, ddof=1)) if len(values) > 1 else 0.0],
                ["nb_runs", len(values)],
            ]

        table = ax_summary.table(
            cellText=[[k, f"{v:.4f}" if isinstance(v, (float, int)) and k not in {"nb_runs", "nb_best_found"} else v] for k, v in rows],
            colLabels=["Stat", "Value"],
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)
        table.scale(1.0, 1.3)
        ax_summary.set_title("Résumé des stats")

        fig.suptitle("Analyse Recuit Simulé - Multi-start", fontsize=11)
        fig.tight_layout()
        plt.show()    


# ================ SimpleGeneticAlgoSolver ==================
class SimpleGeneticAlgoSolver(Solver):
    POP_SIZE = 30 # small pop -> fast, enough diversity  
    GENERATIONS = 50 # limited iterations
    CROSSOVER_PROB = 0.9 # proba = probalite de faire un crossover entre 2 parents ; high -> exploit good parents
    MUTATION_PROB = 0.1 # proba mutation sur en enfant (apres crossover) low -> avoid random search

    def __init__(self):
        self.last_best_history = []
        self.last_mean_history = []
        self.last_population_objectives = []

    def plot(self, best_solution: PartitionSolution | None = None):
        if not self.last_best_history or not self.last_mean_history or not self.last_population_objectives:
            raise ValueError("No GA history available. Run solve() before plotting.")

        best_hist = np.array(self.last_best_history, dtype=float)
        mean_hist = np.array(self.last_mean_history, dtype=float)
        final_obj = np.array(self.last_population_objectives, dtype=float)
        unique_vals, counts = np.unique(final_obj, return_counts=True)
        proportions = counts / counts.sum()
        cum_props = np.cumsum(proportions)

        if best_solution is not None:
            best_obj = float(best_solution.compute_objective())
        else:
            best_obj = float(np.min(final_obj))

        best_so_far = np.minimum.accumulate(best_hist)
        gap = mean_hist - best_hist
        improvement_idx = np.where(np.diff(best_hist) < 0)[0] + 1
        q25, q50, q75 = np.percentile(final_obj, [25, 50, 75])

        fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

        # Evolution and convergence signals.
        axes[0].plot(best_hist, label="Meilleur objectif", color="#2a9d8f", linestyle=":", linewidth=1.8)
        axes[0].plot(mean_hist, label="Objectif moyen", color="#f4a261", linewidth=1.8)
        axes[0].fill_between(np.arange(len(gap)), best_hist, mean_hist, color="#f4a261", alpha=0.15, label="Écart moyen-best")
        if len(improvement_idx) > 0:
            axes[0].scatter(
                improvement_idx,
                best_hist[improvement_idx],
                color="#e63946",
                s=22,
                zorder=3,
                label="Améliorations du best",
            )
        axes[0].set_xlabel("Génération")
        axes[0].set_ylabel("Valeur de coupe")
        axes[0].set_title("Évolution de l'objectif")
        axes[0].text(
            0.02,
            0.98,
            f"Améliorations: {len(improvement_idx)}\nBest final: {best_hist[-1]:.2f}",
            transform=axes[0].transAxes,
            va="top",
            fontsize=8,
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
        )
        axes[0].legend()

        # Final population frequencies and key quantiles.
        axes[1].bar(unique_vals, counts, width=0.08, alpha=0.8, color="#2a9d8f")
        axes[1].axvline(best_obj, color="#e63946", linestyle="--", linewidth=1.5, label="Meilleur trouvé")
        axes[1].axvspan(q25, q75, color="#457b9d", alpha=0.12, label="IQR (Q1-Q3)")
        axes[1].set_xlabel("Valeur de l'objectif")
        axes[1].set_ylabel("Nombre d'individus")
        axes[1].set_title("Fréquences population finale")
        top_i = int(np.argmax(counts))
        axes[1].text(
            unique_vals[top_i],
            counts[top_i],
            f"mode={unique_vals[top_i]:.2f}\n({counts[top_i]} ind.)",
            ha="center",
            va="bottom",
            fontsize=8,
        )
        axes[1].legend()

        # empirical CDF 
        sorted_obj = np.sort(final_obj)
        ecdf = np.arange(1, len(sorted_obj) + 1) / len(sorted_obj)
        axes[2].step(sorted_obj, ecdf, where="post", color="#264653", label="ECDF")
        axes[2].scatter(
            unique_vals,
            cum_props,
            color="#e76f51",
            s=20,
            label="Points cumulés (valeurs uniques)",
        )
        axes[2].set_xlabel("Valeur de l'objectif")
        axes[2].set_ylabel("Proportion cumulée")
        axes[2].set_ylim(0, 1.02)
        axes[2].set_title("ECDF population finale")
        axes[2].legend()

        fig.suptitle(
            f"Analyse Algo Genetique simple | pop={len(final_obj)} | best={np.min(final_obj):.2f} | mean={np.mean(final_obj):.2f}",
            fontsize=11,
        )
        fig.tight_layout()
        plt.show()

    def fitness(self, sol: PartitionSolution):
        return -(sol.compute_objective())  # min <=> -(max)

    def tournament_selection(self, population, fitness_vals, k=3):
        # Tournament Selection : It randomly selects a small group of individuals from the 
        # population and chooses the fittest among them as a parent. This process is repeated 
        # until the required number of parents is selected.
        # section 7.b <https://www.geeksforgeeks.org/dsa/genetic-algorithms/>
        selected = []
        for _ in range(len(population)):
            idx = random.sample(range(len(population)), k) # random pick k
            best = max(idx, key=lambda i: fitness_vals[i]) # best fitness
            selected.append(population[best]) # keep best parent for next gen
        return selected

    def crossover(self, parent1: PartitionSolution, parent2: PartitionSolution):
        # One Point Crossover : A random Point is chosen to be The CrossOver Point , then we 
        # fill the child with genes from both parents.       
        # section 8.a <https://www.geeksforgeeks.org/dsa/genetic-algorithms/>
        n = parent1.graph.nbNodes()
        cut = random.randint(1, n - 1)

        child1 = PartitionSolution(parent1.graph, parent1.p)
        child2 = PartitionSolution(parent1.graph, parent1.p)

        child1.classe[:] = parent1.classe[:cut] + parent2.classe[cut:]
        child2.classe[:] = parent2.classe[:cut] + parent1.classe[cut:]

        return child1, child2

    def mutate(self, sol: PartitionSolution, eps: float):
        # Swap Mutation: We Choose two Point and we switch them.
        # section 9.b <https://www.geeksforgeeks.org/dsa/genetic-algorithms/>
        n = sol.graph.nbNodes()

        if random.random() < self.MUTATION_PROB:  # proba of mutation 
            a = random.randint(0, n - 1)          
            b = random.randint(0, n - 1)          
            while b == a: # avoid same node
                b = random.randint(0, n - 1)
            swap_nodes(sol, a, b) # SWAP

        return sol 

    def repair(self, sol: PartitionSolution, eps: float):
        # checks the feasibilty after mutatation && crossover
        if checkSolution(sol.graph.nbNodes(), sol, sol.p, eps):
            return sol
        # else another init sol
        return initializeInitialSolution("random", sol.graph, sol, eps)

    def solve(self, data: GraphData, p: int, eps: float, solInit: PartitionSolution) -> PartitionSolution:
        # POPULATION INIT
        population = []
        for _ in range(self.POP_SIZE):
            sol = PartitionSolution(data, p)
            sol = initializeInitialSolution("random", data, sol, eps)
            population.append(sol)

        # extra plots 
        self.last_best_history = []
        self.last_mean_history = []
        self.last_population_objectives = []
        current_objectives = [sol.compute_objective() for sol in population]
        self.last_best_history.append(min(current_objectives))
        self.last_mean_history.append(statistics.mean(current_objectives))

        # best sol
        best_sol = min(population, key=lambda s: s.compute_objective())

        # evolution 
        for _ in range(self.GENERATIONS):
            # FITNESS EVALUATION
            fitness_vals = [self.fitness(sol) for sol in population]
            # PARENT SELECTION
            parents = self.tournament_selection(population, fitness_vals)

            random.shuffle(parents)
            new_population = []

            # CROSSOVER + MUTATION + REPAIR
            for i in range(0, self.POP_SIZE, 2):
                p1, p2 = parents[i], parents[i + 1]

                if random.random() < self.CROSSOVER_PROB:
                    c1, c2 = self.crossover(p1, p2)
                else:
                    c1, c2 = p1, p2

                c1 = self.mutate(c1, eps)
                c2 = self.mutate(c2, eps)

                c1 = self.repair(c1, eps)
                c2 = self.repair(c2, eps)

                new_population.extend([c1, c2])

            population = new_population

            current_objectives = [sol.compute_objective() for sol in population]
            self.last_best_history.append(min(current_objectives))
            self.last_mean_history.append(statistics.mean(current_objectives))

            # update best sol
            current_best = min(population, key=lambda s: s.compute_objective())
            if current_best.compute_objective() < best_sol.compute_objective():
                best_sol = current_best

        self.last_population_objectives = [sol.compute_objective() for sol in population]

        return best_sol