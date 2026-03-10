"""
Réalisé avec l'appui du GenAI.
"""

import os
import time
import signal
import csv
import networkx as nx
from networkx.algorithms.community import kernighan_lin_bisection

TIME_LIMIT = 3600

class TimeoutException(Exception): 
  pass

def handler(signum, frame): 
  raise TimeoutException()

signal.signal(signal.SIGALRM, handler)

def read_project_graph(path):
  G = nx.Graph()
  with open(path, "r") as f:
    lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
  n, m = map(int, lines[0].split())
  edge_lines = lines[2:2+m]
  edges = [(int(u), int(v), float(w)) for u, v, w in
           (l.split() for l in edge_lines)]
  G.add_weighted_edges_from(edges)
  return G

def run_all_datasets(data_path, output_file):
  with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["dataFileName", "solutionValue", "cpuTime"])
    for file in sorted(os.listdir(data_path)):
      full_path = os.path.join(data_path, file)
      if not os.path.isfile(full_path): continue
      G = read_project_graph(full_path)
      nodes = list(G.nodes())
      mid = len(nodes)//2
      init_part = (set(nodes[:mid]), set(nodes[mid:]))
      start = time.perf_counter()
      signal.alarm(TIME_LIMIT)
      try:
        part = kernighan_lin_bisection(
          G, partition=init_part, weight="weight"
        )
        cpu = time.perf_counter() - start
        cut = nx.cut_size(G, *part, weight="weight")
      except TimeoutException:
        cpu = TIME_LIMIT
        cut = -1
      finally:
        signal.alarm(0)
      name = os.path.splitext(file)[0]
      writer.writerow([name, f"{cut:.1f}", f"{cpu:.6f}"])

def main():
  run_all_datasets("data", "results_networkx.csv")

if __name__ == "__main__":  
  main()      

