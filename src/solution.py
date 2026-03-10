# solution.py
# Inspiré par le code du projet d’optimisation ROAD 2026 du proffesseur PRUNET Thibault

from array import array


class PartitionSolution:
    """ Représente une solution de partitionnement d'un graphe en p classes."""

    def __init__(self, graph, p):
        self.graph = graph
        self.p = p                                              # nb de classe
        self.classe = array('b', [-1] * self.graph.nbNodes())   # partition
        self.objective_value = None                             # valeur du cut

    def set_class(self, node, k):
        """Affecte un sommet à une classe."""
        self.classe[node] = k

    def classes(self):
        """Retourne un dictionnaire {classe: [sommets]}."""
        result = {k: [] for k in range(self.p)}
        unassigned = []
        for v, k in enumerate(self.classe):
            if k is None:
                unassigned.append(v)
            else:
                # Tolérance : si une classe invalide est trouvée, on la crée
                if k not in result:
                    result[k] = []
                result[k].append(v)
        if unassigned:
            result['unassigned'] = unassigned
        return result

    def count_cross_edges_and_weight(self):
        adj = self.graph.adjacency()
        n = self.graph.nbNodes()
        nb = 0
        total_w = 0.0
        for u in range(n):
            for v, w in adj[u]:
                if v <= u:
                    continue
                ku = self.classe[u]
                kv = self.classe[v]
                if ku is None or kv is None:
                    continue
                if ku != kv:
                    nb += 1
                    total_w += w
        return nb, total_w

    def compute_objective(self):
        """Calcule et retourne la valeur de l'objectif : poids total des arêtes inter-classes."""
        _, total_w = self.count_cross_edges_and_weight()
        self.objective_value = total_w
        return self.objective_value

    def intra_class_stats(self):
        """Retourne un dict {classe: (nb_arêtes_intra, somme_poids_intra)}."""
        adj = self.graph.adjacency()
        n = self.graph.nbNodes()
        stats = {k: [0, 0.0] for k in range(self.p)}
        for u in range(n):
            for v, w in adj[u]:
                if v <= u:
                    continue
                ku = self.classe[u]
                kv = self.classe[v]
                if ku is None or kv is None:
                    continue
                if ku == kv and 0 <= ku < self.p:
                    stats[ku][0] += 1
                    stats[ku][1] += w
        return {k: (cnt, wt) for k, (cnt, wt) in stats.items()}


def printSolution(solution):
    width = 68
    banner = "=" * width

    def section(title):
        print("\n" + title.upper().center(width, "-"))

    print("\n" + banner)
    print("Solution de partitionnement".center(width))
    print(banner)
    print(f"Classes : {solution.p} | Sommets : {solution.graph.nbNodes()}")


    classes = solution.classes()
    section("Classe distribution")
    for k in range(solution.p):
        nodes = classes.get(k, [])
        print(f"Classe {k:>2} | taille = {len(nodes):>2} | {nodes}")

    # Afficher les sommets non affectés, si présents
    if 'unassigned' in classes:
        print(f"Pas assignés  | taille = {len(classes['unassigned']):>2} | {classes['unassigned']}")

    nb_cross, weight_cross = solution.count_cross_edges_and_weight()
    section("Cut statistiques")
    print(f"Arêtes inter-classes : {nb_cross:>3} | poids total = {weight_cross:.2f}")
    val = solution.compute_objective()
    print(f"Valeur du cut (f) : {val} \n")

    # Statistiques intra-classe
    intra = solution.intra_class_stats()
    print("Arêtes intra-classe par classe :")
    for k in range(solution.p):
        nb, w = intra.get(k, (0, 0.0))
        print(f"Classe {k:>2} | arêtes = {nb:>3} | poids = {w:.2f}")

    print(banner + "\n")


def move_node(solution, node, new_class):
    """Déplace un sommet vers une nouvelle classe et met à jour l'objectif."""
    old_class = solution.classe[node]
    if old_class == new_class:
        return  # Pas de changement

    adj = solution.graph.adjacency()
    delta = 0.0

    for neighbor, weight in adj[node]:
        neighbor_class = solution.classe[neighbor]
        if neighbor_class < 0:
            continue
        if neighbor_class == old_class:
            delta += weight  # Perte d'une arête intra-classe
        if neighbor_class == new_class:
            delta -= weight  # Gain d'une arête intra-classe

    # Mettre à jour la classe du sommet
    solution.classe[node] = new_class

    # Mettre à jour la valeur de l'objectif
    if solution.objective_value is not None:
        solution.objective_value += delta

def swap_nodes(solution, node1, node2):
    """Échange les classes de deux sommets et met à jour l'objectif."""
    class1 = solution.classe[node1]
    class2 = solution.classe[node2]
    if class1 == class2:
        return  # Pas de changement

    adj = solution.graph.adjacency()
    delta = 0.0

    for neighbor, weight in adj[node1]:
        if neighbor == node2:
            continue  # l'arête (node1, node2) ne change pas après l'échange
        neighbor_class = solution.classe[neighbor]
        if neighbor_class < 0:
            continue
        if neighbor_class == class1:
            delta += weight
        if neighbor_class == class2:
            delta -= weight

    for neighbor, weight in adj[node2]:
        if neighbor == node1:
            continue
        neighbor_class = solution.classe[neighbor]
        if neighbor_class is None:
            continue
        if neighbor_class == class2:
            delta += weight
        if neighbor_class == class1:
            delta -= weight

    # Échanger les classes des deux sommets
    solution.classe[node1], solution.classe[node2] = class2, class1

    # Mettre à jour la valeur de l'objectif
    if solution.objective_value is not None:
        solution.objective_value += delta



