#data.py
# Inspiré par le code du projet d’optimisation ROAD 2026 du proffesseur PRUNET Thibault
import sys

class GraphData:
    """Représentation d'un graphe non orienté pondéré"""

    def __init__(self, name):
        self._name = name
        self._n = 0
        self._m = 0
        self._deg_min = 0
        self._deg_max = 0

        # Liste d'adjacence : graph[u] = [(v, w), ...]
        self._adj = []

        # Degrés des sommets
        self._degrees = []

    # Accesseurs
    def name(self):
        return self._name

    def nbNodes(self):
        return self._n

    def nbEdges(self):
        return self._m

    def degMin(self):
        return self._deg_min

    def degMax(self):
        return self._deg_max

    def adjacency(self):
        return self._adj

    def degree(self, v):
        return self._degrees[v]

    def edgeWeight(self, u, v):
        for neighbor, weight in self._adj[u]:
            if neighbor == v:
                return weight
        return 0

    # Ajout d'arêtes
    def addEdge(self, u, v, w=1):
        self._adj[u].append((v, w))
        self._adj[v].append((u, w))
        self._degrees[u] += 1
        self._degrees[v] += 1


def readGraphFromFile(filepath):
    """Lecture d un fichier de graphe"""
    try:
        with open(filepath, "r") as f:
            import os
            name = os.path.splitext(os.path.basename(filepath))[0]
            graph = GraphData(name)

            # Lecture des 4 premières valeurs
            header = []
            while len(header) < 4:
                line = f.readline()
                if not line:
                    raise ValueError("Fichier incomplet.")
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                header.extend(map(int, line.split()))

            graph._n, graph._m, graph._deg_min, graph._deg_max = header

            # Initialisation des structures
            graph._adj = [[] for _ in range(graph._n)]
            graph._degrees = [0] * graph._n

            # Lecture des arêtes
            edges_read = 0
            for line in f:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue

                parts = line.split()

                # Bloc des degrés -> fin des arêtes
                if edges_read >= graph._m:
                    break

                # Format : u v [w] (fichier 1-based -> conversion en 0-based)
                u = int(parts[0]) - 1
                v = int(parts[1]) - 1
                w = 1 if len(parts) == 2 else float(parts[2])

                graph.addEdge(u, v, w)
                edges_read += 1

            # degrés des sommets
            for line in f:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue

                parts = line.split()
                if len(parts) != 2:
                    continue

                v = int(parts[0]) - 1
                deg = int(parts[1])

                graph._degrees[v] = deg
            return graph
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return None
    

def printData(graph):
    print("=== Données du graphe ===")
    print(f"Nom : {graph.name()}")
    print(f"Nombre de sommets : {graph.nbNodes()}")
    print(f"Nombre d'arêtes : {graph.nbEdges()}")
    print(f"Degré min : {graph.degMin()}")
    print(f"Degré max : {graph.degMax()}")
    print()

    print("Liste d'adjacence :")
    for u in range(graph.nbNodes()):
        print(f"  {u} -> {graph.adjacency()[u]}")


