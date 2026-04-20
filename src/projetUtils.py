import os
import argparse
import math

def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive integer value")
    return ivalue


def valid_file(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError(f"{value} does not exist or is not a file")
    return value


def valid_folder(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError(f"{value} does not exist or is not a directory (you should create it before)")
    return value

def checkSolution(n, solution, p, epsilon) -> bool:
    """Vérifie si une solution est réalisable pour `p` classes.
    - 2 <= p <= n
    - chaque sommet est affecté 
    - les tailles des classes sont plus petites de |N|/p*(1+epsilon) avec |N|=n le nombre de sommets
    """
    # Validité de p 
    if n <= 0 or solution is None:
        return False
    if p < 2 or p > n:
        return False


    labels = solution.classe
    if len(labels) != n:
        return False
    # Comptage des tailles 
    sizes = [0] * p 
    for lab in labels: 
        if not isinstance(lab, int) or not (0 <= lab < p): 
            return False 
        sizes[lab] += 1 
    
    #les tailles des classes sont plus petites de |A|/p*(1+epsilon) avec |A| le nombre de sommets 
    max_allowed = math.ceil((n / p) * (1 + epsilon))
    if any(size > max_allowed for size in sizes): 
        return False 
    return True
    


def recordSolution(solution, solutionFilePath, one_based_vertices=True):
    """Écrit la solution de partition dans un fichier .sol avec des lignes de commentaires

    Format : 
    # valeur_objetif nbNoeuds nbAretes
    <valeur_objetif> <nbNoeuds> <nbAretes>
    # nbClasses
    <p>
    # somme_des_poids_inter_classes nb_aretes_inter_classes
    <somme_poids_inter> <nb_aretes_inter>
    # Classes (noeds de 1 à n)
    <liste_sommets_classe_1>
    <liste_sommets_classe_2>
    ...
    # somme_des_poids_intra_classes nb_aretes_intra_classe
    <somme_poids_intra_classe_1> <nb_aretes_intra_classe_1>
    <somme_poids_intra_classe_2> <nb_aretes_intra_classe_2>
    ...

    Notes:
    - Les listes de sommets sont écrites en indices 1-based si `one_based_vertices=True`.
    - Si une classe est vide, une ligne vide est écrite pour la classe correspondante.
    - Si la solution est infaisable (toutes les classes vides), on écrit deux lignes : "-1" puis "0".
    """
    try:
        # Récupérer les classes et les listes de sommets par classe (0..p-1)
        classes = solution.classes() if solution is not None else {}
        p = solution.p if solution is not None else 0
        class_lists = [classes.get(k, []) for k in range(p)] if solution is not None else []

        # Cas infaisable : aucune classe avec des sommets
        if solution is None or all(len(lst) == 0 for lst in class_lists):
            with open(solutionFilePath, 'w', encoding='utf-8') as f:
                f.write("# valeur_objetif nbNoeuds nbAretes\n")
                f.write("-1\n")
                f.write("# nbClasses\n")
                f.write("0\n")
            return

        # Calcul des statistiques globales et intra-classe
        nb_inter, wt_inter = solution.count_cross_edges_and_weight()
        intra = solution.intra_class_stats() 

        num_classes = p
        n = solution.graph.nbNodes()
        m = solution.graph.nbEdges()
        val = solution.objective_value if solution.objective_value is not None else solution.compute_objective()

        with open(solutionFilePath, 'w', encoding='utf-8') as f:
            f.write("# valeur_objetif nbNoeuds nbAretes\n")
            f.write(f"{val} {n} {m}\n")

            f.write("# nbClasses\n")
            f.write(f"{num_classes}\n")

            f.write("# somme_des_poids_inter_classes nb_aretes_inter_classes\n")
            f.write(f"{wt_inter} {nb_inter}\n")

            f.write("# Classes (noeds de 1 à n)\n")
            for k in range(num_classes):
                lst = sorted(class_lists[k])
                if one_based_vertices:
                    out = " ".join(str(v + 1) for v in lst)
                else:
                    out = " ".join(str(v) for v in lst)
                f.write(out + "\n")

            f.write("# somme_des_poids_intra_classes nb_aretes_intra_classe\n")
            for k in range(num_classes):
                nb_intra, wt_intra = intra.get(k, (0, 0.0))
                f.write(f"{wt_intra} {nb_intra}\n")
                
    except IOError as e:
        print(f"Error writing solution file: {e}")
        raise

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


def prompt_yes_no(question, options_hint="yes/no"):
    while True:
        prompt = question
        if "[" not in question or "]" not in question:
            prompt = f"{question} [{options_hint}]"

        raw = input(f"{prompt}\n>>> ").strip().lower()
        if raw == "":
            print("Please answer yes or no.")
            continue
        if raw in {"y", "yes", "o", "oui"}:
            return True
        if raw in {"n", "no", "non"}:
            return False
        print("Please answer yes or no.")


def prompt_typed_value(question, caster=str, validator=None, default=None, allow_empty=False):
    """type a value with a specific type"""
    while True:
        prompt = f"{question}"
        if default is not None:
            prompt += f" (default: {default})"
        prompt += "\n>>> "

        raw = input(prompt).strip()

        if raw == "":
            if default is not None:
                return default
            if allow_empty:
                return ""
            print("Value required.")
            continue

        try:
            value = caster(raw)
            if validator is not None:
                value = validator(value)
            return value
        except Exception as exc:
            print(f"Invalid value: {exc}")


def prompt_choice(question, choices, default=None):
    """yes or no ; or a value in a set of choices"""
    allowed = set(choices)
    while True:
        prompt = f"{question}"
        if default is not None:
            prompt += f" (default: {default})"
        prompt += "\n>>> "

        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default

        try:
            value = float(raw)
        except ValueError:
            print("Invalid choice format.")
            continue

        if value in allowed:
            return value
        print(f"Invalid choice. Allowed values: {sorted(choices)}")

from gui import main as gui_main

import sys

def pseudo_main():
    """
        * if no arguments are provided, ask whether to launch GUI
        * else call solver.py with the given arguments
    """
    if len(sys.argv) == 1:
        use_gui = prompt_yes_no("Gui ?")
        if use_gui:
            single_algo_gui = prompt_yes_no(
                "Run 1 algo or multi-algo Gui ? [yes=1 algo, no=multi-algo]"
            )

            if single_algo_gui:
                gui_main()
                return
            else:
                from gui_comparison import main as gui_comparison_main
                gui_comparison_main()
                return 
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solver_path = os.path.join(script_dir, "solver.py")

    cmd = [sys.executable, solver_path] + sys.argv[1:]

    env = os.environ.copy()
    # if user already answered in main.py then avoid asking the same GUI question in solver.py
    if len(sys.argv) == 1:
        env["META_SKIP_SOLVER_GUI_PROMPT"] = "1"

    os.execve(sys.executable, cmd, env)