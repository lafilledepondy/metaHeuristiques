from data import *
from solution import *
from projetUtils import checkSolution

import math
import itertools

import statistics
import random
from array import array

import solution

# =========================================================
# ======================= Solvers =========================
# =========================================================
class Solver:
    def solve(self, data: GraphData, p: int, eps: float) -> PartitionSolution:
        raise NotImplementedError("Solver is an abstract class")

# ================== EnumerationSolver ====================
class EnumerationSolver(Solver):
    def solve(self, data: GraphData, p: int, eps: float) -> PartitionSolution:
        return self.Enumeration(data, p, eps)
        
    def Enumeration(self,data: GraphData, p: int, eps:float) -> PartitionSolution:
        """Énumération (explicite) canonique des partitions en p classes non vides et équilibrées."""
        if data is None:
            return None
        n = data.nbNodes()
        if p <= 1 or p > n:
            print(f"Invalid p={p} for n={n}")
            return None
        best_val = float("inf")
        best_assignment = None

        for assignment in itertools.product(range(p), repeat=n):

            sol = PartitionSolution(data, p)
            for node, lab in enumerate(assignment):
                sol.set_class(node, lab)

            if not checkSolution(n, sol, p, eps):
                continue

            val = sol.compute_objective()

            if val < best_val:
                best_val = val
                best_assignment = assignment
        if best_assignment is None: 
            print(f"No feasible solution found for p={p} and epsilon={eps}") 
            return None
        sol = PartitionSolution(data, p)
        for node, lab in enumerate(best_assignment):
            sol.set_class(node, lab)
        sol.compute_objective()
        return sol

# ==================== GradientSolver =====================
class GradientSolver(Solver):
    def solve(self, graph, p, epsilon, nb_runs):
        solution = PartitionSolution(graph, p)

        solution = self.initializeInitialSolution(solution, epsilon)

        assert checkSolution(graph.nbNodes(), solution, p, epsilon)

        return self.MultiStartGradient(graph, p, epsilon, nb_runs)
        
    def initializeInitialSolution(self, solution: PartitionSolution, epsilon: float):
        n = solution.graph.nbNodes()
        p = solution.p

        max_allowed = math.ceil((n / p) * (1 + epsilon))

        nodes = list(range(n))
        random.shuffle(nodes)

        sizes = [0] * p
        solution.classe[:] = array('b', [-1] * n)

        for node in nodes:
            # classes that still have room
            feasible_classes = [k for k in range(p) if sizes[k] < max_allowed]

            if not feasible_classes:
                raise ValueError("No feasible class left during initialization")

            k = random.choice(feasible_classes)
            solution.classe[node] = k
            sizes[k] += 1

        solution.compute_objective()
        return solution
    
    def Gradient(self, solution: PartitionSolution, eps: float) -> PartitionSolution:
        """
        Descente de gradient -version récursive -
        Retourne un optimum local.
        """
        n = solution.graph.nbNodes()
        p = solution.p

        best_solution = solution
        best_value = solution.compute_objective()

        # Parcours du voisinage V(S)
        for node in range(n):
            old_class = solution.classe[node]

            for new_class in range(p):
                if new_class == old_class:
                    continue

                # Créer un voisin
                neighbor = PartitionSolution(solution.graph, p)
                neighbor.classe[:] = solution.classe[:]
                neighbor.objective_value = solution.objective_value

                move_node(neighbor, node, new_class)

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
            return self.Gradient(best_solution, eps) 

    def MultiStartGradient(self, graph: GraphData, p: int, epsilon: float, nb_runs: int):
        """
        Runs Gradient descent multiple times and computes statistics
        on local optima.
        """

        best_solution = None
        best_value = float("inf")

        values = []          # objective values of all runs
        solutions = []       # keep solutions if needed

        for run in range(nb_runs):
            # 1. Initial solution
            solution = PartitionSolution(graph, p)
            self.initializeInitialSolution(solution, epsilon)

            # 2. Local search
            local_opt = self.Gradient(solution, epsilon)
            val = local_opt.compute_objective()

            values.append(val)
            solutions.append(local_opt)

            # Track best solution
            if val < best_value:
                best_value = val
                best_solution = local_opt

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
            "nb_runs": nb_runs
        }

        return best_solution, stats           

# ================ KernighanAndLinSolver ==================
class KernighanAndLinSolver(Solver):
    def initializeSolution(self, data: GraphData, p: int) -> PartitionSolution:
        n = data.nbNodes()
        sol = PartitionSolution(data, p)
        for i in range(n):
            sol.set_class(i, i % p) # 0, 1, 0, 1... for p=2
        sol.compute_objective() 
        return sol
    
    def calculerDx(self, solution: PartitionSolution):
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

    def solve(self, data: GraphData, p: int, eps: float = 0.0) -> PartitionSolution:
        # cas : p != 2 est traité dans solver.py
        
        solution = self.initializeSolution(data, p)        

        gain = 1
        while gain > 0:
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

                # choisir a in C_1 et b in C_2 qui maximisent le gain
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
            gain = max(cumsum)
            
            if gain > 0:
                k = cumsum.index(gain)
                
                for i in range(k+1):
                    a, b = swap_sequence[i]
                    swap_nodes(solution, a, b) # apply swap

        return solution