"""
Réalisé avec l'appui du GenAI pour la conception graphique.
"""

import os
import sys
import threading
import time
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


ALGORITHMS = [
    ("Enumeration", "1.0"),
    ("Gradient Descent", "2.0"),
    ("KL (enum)", "3.1"),
    ("KL (heapq)", "3.2"),
    ("Gradient+Heuristic", "4.0"),
    ("Recuit Simule", "5.0"),
    ("Simple Genetic Algo", "6.0"),
]


class ComparisonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Partitioning - Multi-Algorithm Comparison")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.minsize(screen_width, screen_height)

        self.root.update_idletasks()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text="Multi-Algorithm Comparison", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        chart_frame = ttk.LabelFrame(main, text="Comparison Charts", padding=10)
        chart_frame.grid(row=0, column=3, rowspan=40, sticky="nsew", padx=(12, 0))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(1, weight=1)
        chart_frame.rowconfigure(3, weight=1)

        ttk.Label(main, text="Data File *", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.data_file_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.data_file_var, width=75).grid(row=1, column=1, sticky="ew", padx=6)
        ttk.Button(main, text="Browse", command=self.browse_data_file).grid(row=1, column=2, sticky="ew")

        ttk.Label(main, text="Algorithms *", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="nw", pady=(12, 4))
        algo_frame = ttk.LabelFrame(main, text="Select one or more algorithms", padding=8)
        algo_frame.grid(row=2, column=1, columnspan=2, sticky="ew")

        self.algo_vars = {}
        for i, (label, value) in enumerate(ALGORITHMS):
            var = tk.BooleanVar(value=False)
            self.algo_vars[value] = var
            ttk.Checkbutton(
                algo_frame,
                text=label,
                variable=var,
                command=self.on_algo_selection_changed,
            ).grid(row=i // 4, column=i % 4, sticky="w", padx=8, pady=4)

        for col in range(4):
            algo_frame.columnconfigure(col, weight=1)

        row = 3
        ttk.Label(main, text="Number of Classes *", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.nb_classes_var = tk.StringVar(value="2")
        self.nb_classes_spinbox = ttk.Spinbox(main, from_=1, to=1000, textvariable=self.nb_classes_var, width=10)
        self.nb_classes_spinbox.grid(row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(main, text="Epsilon", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.epsilon_var = tk.StringVar(value="0.1")
        self.epsilon_entry = ttk.Entry(main, textvariable=self.epsilon_var, width=12)
        self.epsilon_entry.grid(row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(main, text="Time Limit (seconds)", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.time_limit_var = tk.StringVar(value="3600")
        ttk.Entry(main, textvariable=self.time_limit_var, width=12).grid(row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(main, text="Gradient Runs (-nb)", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.nb_runs_var = tk.StringVar(value="20")
        self.nb_runs_entry = ttk.Entry(main, textvariable=self.nb_runs_var, width=12)
        self.nb_runs_entry.grid(row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(main, text="Gradient+Heuristic Best Solution Runs (-bestNb)", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.nb_run_best_solution_var = tk.StringVar(value="3")
        self.nb_run_best_solution_entry = ttk.Entry(main, textvariable=self.nb_run_best_solution_var, width=12)
        self.nb_run_best_solution_entry.grid(row=row, column=1, sticky="w", padx=6)

        row += 1
        ttk.Label(main, text="Solution Folder", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=5)
        self.solution_folder_var = tk.StringVar(value="outputs_exe")
        ttk.Entry(main, textvariable=self.solution_folder_var, width=75).grid(row=row, column=1, sticky="ew", padx=6)
        ttk.Button(main, text="Browse", command=self.browse_solution_folder).grid(row=row, column=2, sticky="ew")

        row += 1
        buttons = ttk.Frame(main)
        buttons.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(14, 8))
        ttk.Button(buttons, text="Run Comparison", command=self.run).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=8)
        ttk.Button(buttons, text="Exit", command=self.exit_app).pack(side=tk.LEFT)

        row += 1
        content = ttk.Frame(main)
        content.grid(row=row, column=0, columnspan=3, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        results_frame = ttk.Frame(content)
        results_frame.grid(row=0, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)

        ttk.Label(results_frame, text="Results", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(8, 4))

        cols = ("algorithm", "objective", "cpu", "feasible", "status")
        self.tree = ttk.Treeview(results_frame, columns=cols, show="headings", height=14)
        self.tree.heading("algorithm", text="Algorithm")
        self.tree.heading("objective", text="Objective")
        self.tree.heading("cpu", text="CPU Time (s)")
        self.tree.heading("feasible", text="Feasible")
        self.tree.heading("status", text="Status")
        self.tree.column("algorithm", width=240, anchor="w")
        self.tree.column("objective", width=100, anchor="center")
        self.tree.column("cpu", width=110, anchor="center")
        self.tree.column("feasible", width=90, anchor="center")
        self.tree.column("status", width=240, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")

        self.tree.tag_configure("fastest", background="#e8f8ee")
        self.tree.tag_configure("best_objective", background="#e8f1fb")
        self.tree.tag_configure("best_both", background="#f7f1d4")

        scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns")

        ttk.Label(
            chart_frame,
            text="CPU time sorted ",
            font=("Segoe UI", 9),
            foreground="#555",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.time_chart_canvas = tk.Canvas(chart_frame, width=260, height=320, bg="white", highlightthickness=1, highlightbackground="#d0d0d0")
        self.time_chart_canvas.grid(row=1, column=0, sticky="nsew")

        ttk.Label(
            chart_frame,
            text="Objective value",
            font=("Segoe UI", 9, "bold"),
            foreground="#444",
        ).grid(row=2, column=0, sticky="w", pady=(10, 6))

        self.objective_chart_canvas = tk.Canvas(chart_frame, width=260, height=320, bg="white", highlightthickness=1, highlightbackground="#d0d0d0")
        self.objective_chart_canvas.grid(row=3, column=0, sticky="nsew")

        legend = ttk.Frame(chart_frame)
        legend.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(legend, text="Legend:", foreground="#555").pack(side=tk.LEFT)
        self._legend_item(legend, "Fastest time", "#2ecc71").pack(side=tk.LEFT, padx=(10, 0))
        self._legend_item(legend, "Best objective", "#3498db").pack(side=tk.LEFT, padx=(10, 0))
        self._legend_item(legend, "Other runs", "#8d99ae").pack(side=tk.LEFT, padx=(10, 0))

        row += 1
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(main, textvariable=self.status_var, foreground="#555").grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 0))

        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=0)
        main.columnconfigure(3, weight=0, minsize=300)
        main.rowconfigure(row - 1, weight=1)

        self._saved_nb_classes = self.nb_classes_var.get()
        self._saved_epsilon = self.epsilon_var.get()
        self._kl_forced_active = False
        self._results = []
        self.on_algo_selection_changed()

    def _legend_item(self, parent, text, color):
        item = ttk.Frame(parent)
        swatch = tk.Canvas(item, width=14, height=14, highlightthickness=0)
        swatch.create_rectangle(0, 0, 14, 14, fill=color, outline="")
        swatch.pack(side=tk.LEFT)
        ttk.Label(item, text=text, foreground="#444").pack(side=tk.LEFT, padx=4)
        return item

    def browse_data_file(self):
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("All files", "*.*"), ("Text files", "*.txt"), ("CSV files", "*.csv")],
        )
        if filename:
            self.data_file_var.set(filename)

    def browse_solution_folder(self):
        folder = filedialog.askdirectory(title="Select Solution Folder")
        if folder:
            self.solution_folder_var.set(folder)

    def selected_algorithms(self):
        return [algo for algo, var in self.algo_vars.items() if var.get()]

    def has_kl_selected(self):
        selected = self.selected_algorithms()
        return any(algo in ("3.1", "3.2") for algo in selected)

    def _update_run_inputs_state(self):
        selected = set(self.selected_algorithms())
        self.nb_runs_entry.configure(state="normal" if "2.0" in selected else "disabled")
        self.nb_run_best_solution_entry.configure(state="normal" if "4.0" in selected else "disabled")

    def on_algo_selection_changed(self):
        kl_selected = self.has_kl_selected()
        if kl_selected and not self._kl_forced_active:
            self._saved_nb_classes = self.nb_classes_var.get()
            self._saved_epsilon = self.epsilon_var.get()
            self.nb_classes_var.set("2")
            self.epsilon_var.set("0.0")
            self.nb_classes_spinbox.configure(state="disabled")
            self.epsilon_entry.configure(state="disabled")
            self._kl_forced_active = True
            self.status_var.set("KL selected: p and epsilon are forced to 2 and 0.0.")
        elif not kl_selected and self._kl_forced_active:
            self.nb_classes_spinbox.configure(state="normal")
            self.epsilon_entry.configure(state="normal")
            self.nb_classes_var.set(self._saved_nb_classes or "2")
            self.epsilon_var.set(self._saved_epsilon or "0.1")
            self._kl_forced_active = False
            self.status_var.set("Ready.")

        self._update_run_inputs_state()

    def validate_inputs(self):
        errors = []
        force_kl_constraints = self.has_kl_selected()

        if not self.data_file_var.get().strip():
            errors.append("Data file path is required.")
        elif not os.path.isfile(self.data_file_var.get().strip()):
            errors.append("Selected data file does not exist.")

        if not self.selected_algorithms():
            errors.append("Select at least one algorithm.")

        if not force_kl_constraints:
            try:
                nb_classes = int(self.nb_classes_var.get())
                if nb_classes <= 0:
                    errors.append("Number of classes must be positive.")
            except ValueError:
                errors.append("Number of classes must be an integer.")

            try:
                float(self.epsilon_var.get())
            except ValueError:
                errors.append("Epsilon must be a valid number.")

        try:
            t = int(self.time_limit_var.get())
            if t <= 0:
                errors.append("Time limit must be positive.")
        except ValueError:
            errors.append("Time limit must be an integer.")

        selected = set(self.selected_algorithms())

        if "2.0" in selected:
            try:
                r = int(self.nb_runs_var.get())
                if r <= 0:
                    errors.append("Gradient runs must be positive.")
            except ValueError:
                errors.append("Gradient runs must be an integer.")

        if "4.0" in selected:
            try:
                r_best = int(self.nb_run_best_solution_var.get())
                if r_best <= 0:
                    errors.append("Gradient+Heuristic runs must be positive.")
            except ValueError:
                errors.append("Gradient+Heuristic runs must be an integer.")

        return errors

    def reset(self):
        self.data_file_var.set("")
        self.nb_classes_var.set("2")
        self.epsilon_var.set("0.1")
        self.time_limit_var.set("3600")
        self.nb_runs_var.set("20")
        self.nb_run_best_solution_var.set("3")
        self.solution_folder_var.set("outputs_exe")
        for algo, var in self.algo_vars.items():
            var.set(False)
        self.nb_classes_spinbox.configure(state="normal")
        self.epsilon_entry.configure(state="normal")
        self._saved_nb_classes = self.nb_classes_var.get()
        self._saved_epsilon = self.epsilon_var.get()
        self._kl_forced_active = False
        self._results = []
        self.on_algo_selection_changed()
        self._update_run_inputs_state()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._redraw_charts()
        self.status_var.set("Ready.")

    def exit_app(self):
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        errors = self.validate_inputs()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._results = []
        self._redraw_charts()
        self.status_var.set("Running selected algorithms...")

        worker = threading.Thread(target=self.execute_comparison, daemon=True)
        worker.start()

    def execute_comparison(self):
        solver_script = os.path.join(os.path.dirname(__file__), "solver.py")
        data_file_path = self.data_file_var.get().strip()
        selected = self.selected_algorithms()
        force_kl_constraints = any(algo in ("3.1", "3.2") for algo in selected)

        if force_kl_constraints:
            effective_nb_classes = 2
            effective_epsilon = 0.0
            self._set_status("KL selected: forcing p=2 and epsilon=0.0 for all algorithms.")
        else:
            effective_nb_classes = int(self.nb_classes_var.get())
            effective_epsilon = float(self.epsilon_var.get())

        time_limit = int(self.time_limit_var.get())
        solution_folder = self.solution_folder_var.get().strip() or "outputs_exe"

        os.makedirs(solution_folder, exist_ok=True)

        for algo in selected:
            display_name = self._algo_display_name(algo)
            self._set_status(f"Running {display_name}...")
            started = time.time()

            cmd = [
                sys.executable,
                solver_script,
                "-d", data_file_path,
                "-a", algo,
                "-p", str(effective_nb_classes),
                "-e", str(effective_epsilon),
                "-t", str(time_limit),
                "-f", solution_folder,
            ]

            if algo == "2.0":
                nb_runs = int(self.nb_runs_var.get())
                cmd.extend(["-nb", str(nb_runs)])
            elif algo == "4.0":
                nb_run_best_solution = int(self.nb_run_best_solution_var.get())
                cmd.extend(["-nb", str(nb_run_best_solution)])

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                elapsed = time.time() - started

                if result.returncode != 0:
                    status = (result.stderr or "solver failed").strip().splitlines()[-1]
                    self._add_result(display_name, "-", f"{elapsed:.3f}", "-", status)
                    continue

                objective = self._extract_last_value(result.stdout, "solutionValue =")
                cpu = self._extract_last_value(result.stdout, "cpuTime =")
                feasible = self._extract_last_value(result.stdout, "isFeasible =")

                if cpu == "-":
                    cpu = f"{elapsed:.3f}"

                self._add_result(display_name, objective, cpu, feasible, "ok")
            except Exception as exc:
                elapsed = time.time() - started
                self._add_result(display_name, "-", f"{elapsed:.3f}", "-", str(exc))

        self._set_status("Comparison finished.")
        self.root.after(0, lambda: messagebox.showinfo("Done", "Comparison finished."))

    def _algo_display_name(self, algo):
        for label, value in ALGORITHMS:
            if value == algo:
                return label
        return algo

    def _algo_short_label(self, algo):
        short_by_value = {
            "1.0": "Enum",
            "2.0": "Grad",
            "3.1": "KL-Enum",
            "3.2": "KL-Heap",
            "4.0": "GR+Heur",
            "5.0": "RecuitSim",
            "6.0": "AGS",
        }

        short_by_display = {
            "Enumeration": "Enum",
            "Gradient Descent": "Grad",
            "KL (enum)": "KL-Enum",
            "KL (heapq)": "KL-Heap",
            "Gradient+Heuristic": "GR+Heur",
            "Recuit Simule": "RecuitSim",
            "Simple Genetic Algo": "AGS",
        }

        if algo in short_by_value:
            return short_by_value[algo]

        if algo in short_by_display:
            return short_by_display[algo]

        return algo

    def _extract_last_value(self, output, prefix):
        for line in reversed(output.splitlines()):
            line = line.strip()
            if line.startswith(prefix):
                return line.replace(prefix, "", 1).strip()
        return "-"

    def _add_result(self, algorithm, objective, cpu, feasible, status):
        def insert_result():
            try:
                cpu_value = float(cpu)
            except (TypeError, ValueError):
                cpu_value = None

            try:
                objective_value = float(objective)
            except (TypeError, ValueError):
                objective_value = None

            self._results.append(
                {
                    "algorithm": algorithm,
                    "objective": objective,
                    "objective_value": objective_value,
                    "cpu": cpu,
                    "cpu_value": cpu_value,
                    "feasible": feasible,
                    "status": status,
                }
            )

            self.tree.insert("", tk.END, values=(algorithm, objective, cpu, feasible, status))
            self._refresh_result_tags()

            self._redraw_charts()

        self.root.after(0, insert_result)

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def _best_cpu_value(self):
        values = [entry["cpu_value"] for entry in self._results if entry["cpu_value"] is not None]
        return min(values) if values else None

    def _best_objective_value(self):
        values = [entry["objective_value"] for entry in self._results if entry["objective_value"] is not None]
        return min(values) if values else None

    def _sorted_results(self, key_name):
        valid = [entry for entry in self._results if entry.get(f"{key_name}_value") is not None]
        invalid = [entry for entry in self._results if entry.get(f"{key_name}_value") is None]
        return sorted(valid, key=lambda entry: entry[f"{key_name}_value"]) + invalid

    def _refresh_result_tags(self):
        best_cpu = self._best_cpu_value()
        best_objective = self._best_objective_value()
        children = self.tree.get_children()

        for index, item_id in enumerate(children):
            if index >= len(self._results):
                self.tree.item(item_id, tags=())
                continue

            entry = self._results[index]
            tags = []
            if best_cpu is not None and entry["cpu_value"] == best_cpu:
                tags.append("fastest")
            if best_objective is not None and entry["objective_value"] == best_objective:
                tags.append("best_objective")

            if "fastest" in tags and "best_objective" in tags:
                tags = ["best_both"]

            self.tree.item(item_id, tags=tuple(tags))

    def _redraw_charts(self):
        self._draw_metric_chart(
            canvas=getattr(self, "time_chart_canvas", None),
            results=self._sorted_results("cpu"),
            value_key="cpu_value",
            label_key="algorithm",
            metric_name="CPU time",
            unit="s",
            highlight_color="#2ecc71",
            default_color="#8d99ae",
        )
        self._draw_metric_chart(
            canvas=getattr(self, "objective_chart_canvas", None),
            results=self._sorted_results("objective"),
            value_key="objective_value",
            label_key="algorithm",
            metric_name="Objective value",
            unit="",
            highlight_color="#3498db",
            default_color="#8d99ae",
        )

    def _draw_metric_chart(self, canvas, results, value_key, label_key, metric_name, unit, highlight_color, default_color):
        if canvas is None:
            return

        canvas.delete("all")
        width = int(canvas.winfo_width() or 320)
        height = int(canvas.winfo_height() or 170)
        margin_left = 18
        margin_right = 12
        margin_top = 16
        margin_bottom = 24

        if not results:
            canvas.create_text(width // 2, height // 2, text=f"No {metric_name.lower()} data yet", fill="#666", font=("Segoe UI", 10, "italic"))
            return

        values = [entry[value_key] for entry in results if entry[value_key] is not None]
        if not values:
            canvas.create_text(width // 2, height // 2, text=f"No numeric {metric_name.lower()} to plot", fill="#666", font=("Segoe UI", 10, "italic"))
            return

        max_value = max(values)
        chart_width = max(1, width - margin_left - margin_right)
        chart_height = max(1, height - margin_top - margin_bottom)
        bar_gap = 10 if len(results) <= 4 else 8
        bar_height = max(16, min(32, (chart_height - bar_gap * (len(results) - 1)) // max(1, len(results))))
        label_area = 92
        scale = (chart_width - label_area - 26) / max_value if max_value > 0 else 1.0
        best_value = min(values)

        canvas.create_line(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom, fill="#999")
        canvas.create_line(margin_left, margin_top, margin_left, height - margin_bottom, fill="#999")
        canvas.create_text(margin_left, 6, text=metric_name, anchor="w", fill="#444", font=("Segoe UI", 9, "bold"))

        y = margin_top
        for entry in results:
            value = entry[value_key]
            short_label = self._algo_short_label(entry[label_key])
            canvas.create_text(margin_left + 4, y + bar_height / 2, text=short_label, anchor="w", fill="#333", font=("Segoe UI", 9, "bold"))

            if value is None:
                canvas.create_text(width - margin_right - 6, y + bar_height / 2, text="n/a", anchor="e", fill="#999", font=("Segoe UI", 9))
            else:
                bar_length = max(2, value * scale)
                x0 = margin_left + label_area
                x1 = min(width - margin_right, x0 + bar_length)
                bar_color = highlight_color if value == best_value else default_color
                canvas.create_rectangle(x0, y, x1, y + bar_height, fill=bar_color, outline="")
                value_text = f"{value:.3f}{unit}" if unit else f"{value:.3f}"
                if bar_length >= 56:
                    canvas.create_text(x1 - 4, y + bar_height / 2, text=value_text, anchor="e", fill="white", font=("Segoe UI", 9, "bold"))
                else:
                    canvas.create_text(x0 + 3, y + bar_height / 2, text=value_text, anchor="w", fill="#111", font=("Segoe UI", 8, "bold"))

            y += bar_height + bar_gap


def main():
    root = tk.Tk()
    gui = ComparisonGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
