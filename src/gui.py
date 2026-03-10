"""
Réalisé avec l'appui du GenAI pour la conception graphique.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import time
import platform
from pathlib import Path
import threading
import subprocess

# ====== DESCRIPTIONS ======
ALGO1_DESCRIPTION = "Exhaustive search through all possible partitions\n(Best for small graphs)"
ALGO2_DESCRIPTION = "Iterative optimization using gradient information\n(TODO)"
ALGO3_DESCRIPTION = "Advanced heuristic with vertex swapping\n(TODO)"

class ParametersGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Partitioning - Parameters")
        self.root.geometry("600x950")
        self.root.resizable(False, False)
        
        # ====== CENTER ON THE SCREEN ======
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 600
        window_height = 950
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ====== COLOUR PALETTE & STYLE ======
        self.bg_color = "#f8f9fa"
        self.card_color = "#e8eef5"
        self.text_color = "#2c3e50"
        self.muted_text = "#7f8c8d"

        self.root.configure(bg=self.bg_color)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Run.TButton', foreground='black')
        style.configure('Reset.TButton', foreground='black')
        style.configure('Exit.TButton', foreground='black')
        
        self.pad = 10
        main_frame = ttk.Frame(root, padding=self.pad)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title = ttk.Label(main_frame, text="Graph Partitioning - Parameters", 
                         font=("Segoe UI", 18, "bold"), foreground=self.text_color)
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        ttk.Label(main_frame, text="Data File Path *", font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.data_file_var = tk.StringVar()
        data_file_entry = ttk.Entry(main_frame, textvariable=self.data_file_var, width=40)
        data_file_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(self.pad, 5))
        ttk.Button(main_frame, text="Browse", command=self.browse_data_file).grid(
            row=row, column=2, padx=5)
        row += 1
        
        # ====== ALGORITHM SELECTION ======
        ttk.Label(main_frame, text="Algorithm *", font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.algo_var = tk.StringVar(value="1")
        
        algo_frame = ttk.LabelFrame(main_frame, text="Select Algorithm", padding=15)
        algo_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=self.pad, pady=10)
        
        algo1_frame = tk.Frame(algo_frame, bg=self.card_color)
        algo1_frame.pack(fill=tk.X, pady=8, padx=5)
        algo1_btn = tk.Button(algo1_frame, text="◇ Enumeration", bg=self.card_color, fg=self.text_color,
                             activebackground=self.card_color, activeforeground=self.text_color,
                             bd=0, font=('Segoe UI', 10, 'bold'), anchor=tk.W, justify=tk.LEFT,
                             command=lambda: self.select_algorithm("1", algo1_btn, algo2_btn, algo3_btn))
        algo1_btn.pack(anchor=tk.W, padx=15, pady=8)
        self.algo1_btn = algo1_btn
        ttk.Label(algo1_frame, text=ALGO1_DESCRIPTION,
                 font=('Segoe UI', 10), foreground=self.muted_text).pack(anchor=tk.W, padx=40, pady=(0, 8))
        
        algo2_frame = tk.Frame(algo_frame, bg=self.card_color)
        algo2_frame.pack(fill=tk.X, pady=8, padx=5)
        algo2_btn = tk.Button(algo2_frame, text="◇ Gradient Descent", bg=self.card_color, fg=self.text_color,
                             activebackground=self.card_color, activeforeground=self.text_color,
                             bd=0, font=('Segoe UI', 10, 'bold'), anchor=tk.W, justify=tk.LEFT,
                             command=lambda: self.select_algorithm("2", algo1_btn, algo2_btn, algo3_btn))
        algo2_btn.pack(anchor=tk.W, padx=15, pady=8)
        self.algo2_btn = algo2_btn
        ttk.Label(algo2_frame, text=ALGO2_DESCRIPTION,
                 font=('Segoe UI', 10), foreground=self.muted_text).pack(anchor=tk.W, padx=40, pady=(0, 8))
        
        algo3_frame = tk.Frame(algo_frame, bg=self.card_color)
        algo3_frame.pack(fill=tk.X, pady=8, padx=5)
        algo3_btn = tk.Button(algo3_frame, text="◇ Kernighan and Lin", bg=self.card_color, fg=self.text_color,
                             activebackground=self.card_color, activeforeground=self.text_color,
                             bd=0, font=('Segoe UI', 10, 'bold'), anchor=tk.W, justify=tk.LEFT,
                             command=lambda: self.select_algorithm("3", algo1_btn, algo2_btn, algo3_btn))
        algo3_btn.pack(anchor=tk.W, padx=15, pady=8)
        self.algo3_btn = algo3_btn
        ttk.Label(algo3_frame, text=ALGO3_DESCRIPTION,
                 font=('Segoe UI', 10), foreground=self.muted_text).pack(anchor=tk.W, padx=40, pady=(0, 8))
        
        algo1_btn.config(text="◆ Enumeration")
        
        row += 1
        
        ttk.Label(main_frame, text="Number of Classes *", font=('Segoe UI', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.nb_classes_var = tk.StringVar(value="2")
        self.nb_classes_spinbox = ttk.Spinbox(main_frame, from_=1, to=1000, 
                                         textvariable=self.nb_classes_var, width=10)
        self.nb_classes_spinbox.grid(row=row, column=1, sticky=tk.W, padx=(self.pad, 0))
        row += 1
        
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ====== OPTIONAL PARAMETERS ======
        optional_label = ttk.Label(main_frame, text="Optional Parameters", 
                                  font=('Segoe UI', 11, 'bold'))
        optional_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1
        
        ttk.Label(main_frame, text="Epsilon", font=('Segoe UI   ', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.epsilon_var = tk.StringVar(value="0.1")
        epsilon_entry = ttk.Entry(main_frame, textvariable=self.epsilon_var, width=15)
        epsilon_entry.grid(row=row, column=1, sticky=tk.W, padx=(self.pad, 0))
        ttk.Label(main_frame, text="(default: 0.1)", font=('Segoe UI', 9, 'italic'), 
                 foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        ttk.Label(main_frame, text="Time Limit (seconds)", font=('Segoe UI', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.time_limit_var = tk.StringVar(value="3600")
        time_limit_entry = ttk.Entry(main_frame, textvariable=self.time_limit_var, width=15)
        time_limit_entry.grid(row=row, column=1, sticky=tk.W, padx=(self.pad, 0))
        ttk.Label(main_frame, text="(default: 3600)", font=('Segoe UI', 9, 'italic'), 
                 foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        ttk.Label(main_frame, text="Number of Runs", font=('Segoe UI', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.nb_runs_var = tk.StringVar(value="20")
        self.nb_runs_spinbox = ttk.Spinbox(main_frame, from_=1, to=1000, 
                                         textvariable=self.nb_runs_var, width=10, state='disabled')
        self.nb_runs_spinbox.grid(row=row, column=1, sticky=tk.W, padx=(self.pad, 0))
        ttk.Label(main_frame, text="(default: 20, for Gradient only)", font=('Segoe UI', 9, 'italic'), 
                 foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        ttk.Label(main_frame, text="Solution Folder Path", font=('Segoe UI', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.solution_folder_var = tk.StringVar()
        self.solution_folder_entry = tk.Entry(main_frame, textvariable=self.solution_folder_var, width=40, 
                                         font=('Segoe UI', 10), fg='gray')
        self.solution_folder_entry.insert(0, "(default: outputs_exe)")
        self.solution_folder_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(self.pad, 5))
        ttk.Button(main_frame, text="Browse", command=self.browse_solution_folder).grid(
            row=row, column=2, padx=5)
        
        # Placeholder functionality
        self.placeholder_text = "(default: outputs_exe)"
        def on_focus_in(event):
            if self.solution_folder_entry.get() == self.placeholder_text:
                self.solution_folder_entry.delete(0, tk.END)
                self.solution_folder_entry.config(fg='black')
                self.solution_folder_var.set("")
        
        def on_focus_out(event):
            if self.solution_folder_entry.get() == "":
                self.solution_folder_entry.insert(0, self.placeholder_text)
                self.solution_folder_entry.config(fg='gray')
        
        self.solution_folder_entry.bind("<FocusIn>", on_focus_in)
        self.solution_folder_entry.bind("<FocusOut>", on_focus_out)
        row += 1
        
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # ====== BUTTONS ======
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(4, weight=1)
        
        ttk.Button(button_frame, text="Run", command=self.run, width=15, style='Run.TButton').grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Reset", command=self.reset, width=15, style='Reset.TButton').grid(row=0, column=2, padx=10)
        ttk.Button(button_frame, text="Exit", command=self.exit_app, width=15, style='Exit.TButton').grid(row=0, column=3, padx=10)
        
    def browse_data_file(self):
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("All files", "*.*"), ("Text files", "*.txt"), ("CSV files", "*.csv")]
        )
        if filename:
            self.data_file_var.set(filename)
    
    def browse_solution_folder(self):
        folder = filedialog.askdirectory(title="Select Solution Folder")
        if folder:
            self.solution_folder_var.set(folder)
    
    def select_algorithm(self, algo_num, btn1, btn2, btn3):
        """Handle algorithm selection with diamond indicators"""
        self.algo_var.set(algo_num)
        
        # Update button 
        if algo_num == "1":
            btn1.config(text="◆ Enumeration")
            btn2.config(text="◇ Gradient Descent")
            btn3.config(text="◇ Kernighan and Lin")
            self.nb_classes_spinbox.config(state='normal')
            self.nb_runs_spinbox.config(state='disabled')
        elif algo_num == "2":
            btn1.config(text="◇ Enumeration")
            btn2.config(text="◆ Gradient Descent")
            btn3.config(text="◇ Kernighan and Lin")
            self.nb_classes_spinbox.config(state='normal')
            self.nb_runs_spinbox.config(state='normal')
        elif algo_num == "3":
            btn1.config(text="◇ Enumeration")
            btn2.config(text="◇ Gradient Descent")
            btn3.config(text="◆ Kernighan and Lin")
            self.nb_classes_var.set("2")
            self.nb_classes_spinbox.config(state='disabled')
            self.nb_runs_spinbox.config(state='disabled')
        
        self.on_algo_changed()
    
    def on_algo_changed(self):
        pass
    
    def get_algo_name(self, algo_num):
        algo_names = {
            "1": "Enumeration",
            "2": "Gradient Descent",
            "3": "Kernighan and Lin"
        }
        return algo_names.get(algo_num, "Unknown")
    
    def validate_inputs(self):
        errors = []
        
        if not self.data_file_var.get().strip():
            errors.append("Data File Path is required")
        elif not os.path.isfile(self.data_file_var.get()):
            errors.append(f"Data file not found: {self.data_file_var.get()}")
        
        if not self.algo_var.get():
            errors.append("Algorithm is required")
        
        if not self.nb_classes_var.get().strip():
            errors.append("Number of Classes is required")
        else:
            try:
                nb_classes = int(self.nb_classes_var.get())
                if nb_classes <= 0:
                    errors.append("Number of Classes must be positive")
            except ValueError:
                errors.append("Number of Classes must be an integer")
        
        folder_value = self.solution_folder_var.get().strip()
        if folder_value and folder_value != self.placeholder_text:
            if not os.path.isdir(folder_value):
                errors.append(f"Solution folder not found: {folder_value}")
        
        if self.epsilon_var.get().strip():
            try:
                float(self.epsilon_var.get())
            except ValueError:
                errors.append("Epsilon must be a valid number")
        
        if self.time_limit_var.get().strip():
            try:
                time_limit = int(self.time_limit_var.get())
                if time_limit <= 0:
                    errors.append("Time Limit must be positive")
            except ValueError:
                errors.append("Time Limit must be an integer")
        
        if self.nb_runs_var.get().strip():
            try:
                nb_runs = int(self.nb_runs_var.get())
                if nb_runs <= 0:
                    errors.append("Number of Runs must be positive")
            except ValueError:
                errors.append("Number of Runs must be an integer")
        
        return errors
    
    def run(self):
        errors = self.validate_inputs()
        
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        algo_num = self.algo_var.get()
        
        # Handle placeholder text for display
        folder_display = self.solution_folder_var.get().strip()
        if not folder_display or folder_display == self.placeholder_text:
            folder_display = "outputs_exe (default)"
        
        summary = f"""
            Parameters to use:
            ====================
            Data File: {self.data_file_var.get()}
            Algorithm: {self.get_algo_name(algo_num)}
            Number of Classes: {self.nb_classes_var.get()}
            Epsilon: {self.epsilon_var.get() if self.epsilon_var.get().strip() else '0.1 (default)'}
            Time Limit: {self.time_limit_var.get() if self.time_limit_var.get().strip() else '3600 (default)'} seconds
            Number of Runs: {self.nb_runs_var.get() if self.nb_runs_var.get().strip() else '20 (default)'} (for Gradient only)
            Solution Folder: {folder_display}
            ====================
        """
        
        response = messagebox.askyesno("Confirm Execution", summary + "\n\nDo you want to proceed with execution?")
        
        if response:
            # Run the algorithm in a separate thread to keep GUI responsive
            thread = threading.Thread(target=self.execute_algorithm, daemon=True)
            thread.start()
            # Hide the main window instead of destroying it (keeps event loop alive for messages)
            self.root.withdraw()
    
    def execute_algorithm(self):
        try:            
            # Get parameters
            dataFilePath = self.data_file_var.get()
            algorithm = int(self.algo_var.get())
            nbClasses = int(self.nb_classes_var.get())
            epsilon = float(self.epsilon_var.get()) if self.epsilon_var.get().strip() else 0.1
            timeLimit = int(self.time_limit_var.get()) if self.time_limit_var.get().strip() else 3600
            nbRuns = int(self.nb_runs_var.get()) if self.nb_runs_var.get().strip() else 20
            solutionFolderPath = self.solution_folder_var.get().strip()
            
            # Handle placeholder text or empty folder path
            if not solutionFolderPath or solutionFolderPath == self.placeholder_text:
                solutionFolderPath = "outputs_exe"
                if not os.path.exists(solutionFolderPath):
                    os.makedirs(solutionFolderPath)
            
            # Build command to call solver.py
            solver_script = os.path.join(os.path.dirname(__file__), "solver.py")
            cmd = [
                sys.executable,
                solver_script,
                "-d", dataFilePath,
                "-a", str(algorithm),
                "-p", str(nbClasses),
                "-e", str(epsilon),
                "-t", str(timeLimit),
                "-f", solutionFolderPath,
                "-nb", str(nbRuns)
            ]
            
            print("----------- EXECUTING SOLVER -----------")
            print("Command:", " ".join(cmd))
            print("------------------------------------")
            
            # Run solver.py as a subprocess and capture output
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            # Check for errors
            if result.returncode != 0:
                error_msg = f"Solver execution failed with return code {result.returncode}\n\n{result.stderr}"
                self._show_message("Execution Error", error_msg, "error")
                return
            
            # Success message
            success_msg = f"""Solution execution completed successfully!

Output:
{result.stdout}"""
            
            self._show_message("Success", success_msg, "info")
                
        except Exception as e:
            error_msg = f"An error occurred during execution:\n\n{str(e)}"
            print(error_msg)
            self._show_message("Execution Error", error_msg, "error")
    
    def _show_message(self, title, message, msg_type):
        """Thread-safe way to show messages from worker threads"""
        def show_and_quit():
            try:
                if msg_type == "info":
                    messagebox.showinfo(title, message)
                elif msg_type == "warning":
                    messagebox.showwarning(title, message)
                elif msg_type == "error":
                    messagebox.showerror(title, message)
            except Exception as e:
                print(f"Failed to show message: {e}")
            finally:
                self.root.destroy()
                sys.exit(0)
        
        try:
            self.root.after(0, show_and_quit)
        except Exception as e:
            print(f"Failed to schedule message: {e}")
            sys.exit(0)
    
    def reset(self):
        self.data_file_var.set("")
        self.algo_var.set("1")
        self.nb_classes_var.set("2")
        self.solution_folder_var.set("")
        self.epsilon_var.set("0.1")
        self.time_limit_var.set("3600")
        self.nb_runs_var.set("20")
    
    def exit_app(self):
        self.root.quit()
        self.root.destroy()
        sys.exit(0)


def main():
    root = tk.Tk()
    gui = ParametersGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
