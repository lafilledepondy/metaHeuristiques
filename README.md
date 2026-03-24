# Graph Partitioning Solver

A Python-based solver for the balanced graph partitioning problem, designed to partition weighted graphs into balanced classes while minimizing the sum of edge weights between classes (min-cut objective).

## Description

This project implements optimization algorithms to solve the graph partitioning problem.

- **Input**: A weighted undirected graph and parameter `p` (number of classes)
- **Output**: A balanced partition of graph nodes into `p` classes minimizing cut weight

### Project structure

- `src/`
  - `main.py` : entry point providing GUI/CLI launching plus ready-made examples.
  - `solver.py` : command-line that parses arguments and dispatches to algorithms.
  - `algos.py` : implementations of Enumeration, Gradient, and Kernighan-Lin solvers.
  - `data.py`, `solution.py`, `projetUtils.py` : helpers for reading instances, representing partitions, and validating feasibility.
  - `ScriptExperiments.py`, `scriptCreateSummaryFiles.py`, `SummaryFileGrad.py` : utilities to batch-run experiments and aggregate logs/results.
- `data/` : sample weighted graph instances.
- `solution/` : expected solutions for the bundled instances.
- `outputs_exe/` : default folder where CLI runs write `.sol` files if no custom path is provided.
- `resultats_csv/`: CSV summaries generated from experiments.

## Installation

### Requirements

- Python 3.1+

### Setup

```bash
# Clone the repository
git clone https://gitlab.emi.u-bordeaux.fr/meta/meta.git
cd meta

# Create virtual environment
python3 -m venv meta_env
source meta_env/bin/activate # on Linux
# meta_env\Scripts\activate # on Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the `main.py`

The solver can be run in two modes:

#### 1. GUI Mode (No Parameters)

Launch the graphical interface to select parameters interactively:

```bash
cd src
python main.py
```

#### 2. Command-Line Mode (With Parameters)

```bash
cd src
python main.py -d <data_file> -a <algorithm> -p <num_classes> [options]
```

**Required Arguments:**

- `-d, --dataFilePath` - Path to the graph data file
- `-a, --algorithm` - Algorithm choice: 1 (Enumeration), 2 (Gradient Descent), 3 (Kernighan-Lin)
- `-p, --nbClasses` - Number of partition classes
- `-nb, --nbRuns <nb_max_iter>` - When using the Gradient solver (`-a 2`), set the number of multi-start. This `nb_max_iter` value determines how many local searches are performed before picking the best solution.

**Optional Arguments:**

- `-f, --solutionFolderPath` - Output folder for solution files (default: creates 'outputs_exe' folder if not provided)
- `-e, --epsilon` - Balance tolerance factor (default: 0.1)
- `-t, --timeLimit` - Time limit in seconds (default: 3600 seconds = 1 hour)
- `-nb, --nbRuns` - Specific to Gradient solver ; default is 20 (number) of multi-start iterations.

#### Example

```bash
python main.py -d ../data/graph.txt -a 1 -p 4 -e 0.1 -t 3600
```

Or with custom output folder:

```bash
python main.py -d ../data/graph.txt -a 1 -p 4 -f ./results -e 0.1 -t 3600
```

#### Running Batch Experiments

```bash
python ScriptExperiments.py -d <data_folder> -f <experiment_folder> -a <algo_list> -p <class_list> -e <epsilon_list> -t <time_limit>
```

#### Built-in Examples

`src/main.py` ships with quick demo helpers you can uncomment to see the algorithms in action without any CLI arguments:

- `enum_example()` runs the brute-force enumeration on `data/cinqSommets.txt`.
- `gradient_descent_example()` showcases the greedy gradient routine (set `nb_iter` to match your desired `nb_max_iter`).
- `kl_example()` executes a Kernighan-Lin pass for the 2-class case.

#### Generating Result Summary

```bash
python scriptCreateSummaryFiles.py -l <log_folder>
```

<!-- ## Data Format

TODO

Graph files should contain:



- Header: `n m deg_min deg_max` (number of nodes, edges, min degree, max degree)
- Edges: `u v [weight]` (1-based node indices, weight optional, default 1)
- Footer: Degree information for each node -->

## Acknowledgment

Inspired by the ROAD 2026 optimization project framework by Professor Thibault PRUNET.
