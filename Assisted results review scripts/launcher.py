import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import webbrowser
import sys
import tempfile
from pathlib import Path

class CSVAnalysisLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Analysis Launcher")
        self.root.geometry("550x300")
        self.root.resizable(False, False)
        
        # Get the directory where this script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Variables
        self.mode = tk.StringVar(value="single")
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        
        # Set default output directory to a subfolder in the launcher's directory
        default_output = os.path.join(self.script_dir, "output")
        self.output_dir = tk.StringVar(value=default_output)
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="CSV Analysis Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Mode selection
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(fill="x", padx=20, pady=5)
        
        mode_label = tk.Label(mode_frame, text="Analysis Type:", font=("Arial", 10, "bold"))
        mode_label.pack(side="left", padx=5)
        
        single_radio = tk.Radiobutton(mode_frame, text="Single CSV (Results.py)", 
                                      variable=self.mode, value="single",
                                      command=self.update_ui)
        single_radio.pack(side="left", padx=10)
        
        compare_radio = tk.Radiobutton(mode_frame, text="Compare Two CSVs (Match.py)", 
                                       variable=self.mode, value="compare",
                                       command=self.update_ui)
        compare_radio.pack(side="left", padx=10)
        
        # File selection frames
        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(fill="x", padx=20, pady=10)
        
        # First file
        file1_frame = tk.Frame(self.file_frame)
        file1_frame.pack(fill="x", pady=5)
        
        file1_label = tk.Label(file1_frame, text="CSV File:", width=10, anchor="w")
        file1_label.pack(side="left", padx=5)
        
        file1_entry = tk.Entry(file1_frame, textvariable=self.file1_path, width=50)
        file1_entry.pack(side="left", padx=5)
        
        file1_button = tk.Button(file1_frame, text="Browse...", command=self.browse_file1)
        file1_button.pack(side="left", padx=5)
        
        # Second file (for compare mode)
        self.file2_frame = tk.Frame(self.file_frame)
        
        file2_label = tk.Label(self.file2_frame, text="Second CSV:", width=10, anchor="w")
        file2_label.pack(side="left", padx=5)
        
        file2_entry = tk.Entry(self.file2_frame, textvariable=self.file2_path, width=50)
        file2_entry.pack(side="left", padx=5)
        
        file2_button = tk.Button(self.file2_frame, text="Browse...", command=self.browse_file2)
        file2_button.pack(side="left", padx=5)
        
        # Output directory
        output_frame = tk.Frame(self.root)
        output_frame.pack(fill="x", padx=20, pady=5)
        
        output_label = tk.Label(output_frame, text="Output Dir:", width=10, anchor="w")
        output_label.pack(side="left", padx=5)
        
        output_entry = tk.Entry(output_frame, textvariable=self.output_dir, width=50)
        output_entry.pack(side="left", padx=5)
        
        output_button = tk.Button(output_frame, text="Browse...", command=self.browse_output)
        output_button.pack(side="left", padx=5)
        
        # Run button
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)
        
        run_button = tk.Button(button_frame, text="Run Analysis", 
                              command=self.run_analysis,
                              bg="#4CAF50", fg="white",
                              font=("Arial", 12, "bold"),
                              width=15, height=1)
        run_button.pack()
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(self.root, textvariable=self.status_var, 
                               font=("Arial", 9), fg="#666666")
        status_label.pack(side="bottom", pady=5)
        
        # Set initial UI state
        self.update_ui()
        
    def update_ui(self):
        # Show/hide second file input based on mode
        if self.mode.get() == "compare":
            self.file2_frame.pack(fill="x", pady=5)
        else:
            self.file2_frame.pack_forget()
            
    def browse_file1(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.file1_path.set(filename)
            
    def browse_file2(self):
        filename = filedialog.askopenfilename(
            title="Select Second CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.file2_path.set(filename)
            
    def browse_output(self):
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if directory:
            self.output_dir.set(directory)
    
    def run_analysis(self):
        # Validate inputs
        if not self.file1_path.get():
            messagebox.showerror("Error", "Please select a CSV file")
            return
            
        if self.mode.get() == "compare" and not self.file2_path.get():
            messagebox.showerror("Error", "Please select a second CSV file")
            return
            
        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir.get(), exist_ok=True)
        except PermissionError:
            # If default location fails, try user's documents folder
            import pathlib
            docs_dir = os.path.join(pathlib.Path.home(), "Documents", "CSV_Analysis_Output")
            try:
                os.makedirs(docs_dir, exist_ok=True)
                self.output_dir.set(docs_dir)
                messagebox.showinfo("Output Directory Changed", 
                                   f"Cannot write to the original output directory due to permission issues.\n\n"
                                   f"Output will be saved to:\n{docs_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output directory:\n{str(e)}\n\nPlease select a different output directory.")
                return
        
        # Set status
        self.status_var.set("Running analysis...")
        self.root.update()
        
        try:
            # Determine which script to run
            if self.mode.get() == "single":
                # Run Results.py
                self.status_var.set("Running Results.py...")
                self.root.update()
                
                # Full path to the Results.py script
                results_script = os.path.join(self.script_dir, "Results.py")
                
                if not os.path.exists(results_script):
                    messagebox.showerror("Error", f"Cannot find Results.py script at:\n{results_script}\n\nMake sure the script is in the same directory as the launcher.")
                    self.status_var.set("Error: Script not found")
                    return
                
                process = subprocess.Popen([
                    sys.executable, 
                    results_script,
                    self.file1_path.get()
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.script_dir)
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    messagebox.showerror("Error", f"Error running Results.py:\n{stderr.decode()}")
                    self.status_var.set("Error occurred")
                    return
                    
                # Get input filename for output HTML filename
                input_filename = os.path.basename(self.file1_path.get())
                input_filename_no_ext = os.path.splitext(input_filename)[0]
                html_filename = f"{input_filename_no_ext} results.html"
                html_file = os.path.join(self.script_dir, "output", html_filename)
                
                # Try to open the file
                if os.path.exists(html_file):
                    # Use subprocess.Popen to open the file without waiting
                    if sys.platform == 'win32':
                        # On Windows, use 'start' command to open file
                        subprocess.Popen(['start', '', html_file], shell=True)
                    else:
                        # On Linux/Mac use xdg-open or open
                        cmd = 'open' if sys.platform == 'darwin' else 'xdg-open'
                        subprocess.Popen([cmd, html_file])
                    
                    self.status_var.set(f"Analysis complete. HTML file opened: {html_filename}")
                else:
                    self.status_var.set(f"Analysis complete, but HTML file not found.")
                    messagebox.showwarning("File Not Found", 
                                          f"The HTML file could not be found at:\n{html_file}")
                
            else:
                # Run Match.py
                self.status_var.set("Running Match.py...")
                self.root.update()
                
                # Full path to the Match.py script
                match_script = os.path.join(self.script_dir, "Match.py")
                
                if not os.path.exists(match_script):
                    messagebox.showerror("Error", f"Cannot find Match.py script at:\n{match_script}\n\nMake sure the script is in the same directory as the launcher.")
                    self.status_var.set("Error: Script not found")
                    return
                
                process = subprocess.Popen([
                    sys.executable,
                    match_script,
                    self.file1_path.get(),
                    self.file2_path.get()
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.script_dir)
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    messagebox.showerror("Error", f"Error running Match.py:\n{stderr.decode()}")
                    self.status_var.set("Error occurred")
                    return
                    
                # Get input filenames for output HTML filename
                file1_name = os.path.basename(self.file1_path.get())
                file2_name = os.path.basename(self.file2_path.get())
                file1_name_no_ext = os.path.splitext(file1_name)[0]
                file2_name_no_ext = os.path.splitext(file2_name)[0]
                html_filename = f"{file1_name_no_ext} {file2_name_no_ext} match.html"
                html_file = os.path.join(self.script_dir, "output", html_filename)
                
                # Try to open the file
                if os.path.exists(html_file):
                    # Use subprocess.Popen to open the file without waiting
                    if sys.platform == 'win32':
                        # On Windows, use 'start' command to open file
                        subprocess.Popen(['start', '', html_file], shell=True)
                    else:
                        # On Linux/Mac use xdg-open or open
                        cmd = 'open' if sys.platform == 'darwin' else 'xdg-open'
                        subprocess.Popen([cmd, html_file])
                    
                    self.status_var.set(f"Analysis complete. HTML file opened: {html_filename}")
                else:
                    self.status_var.set(f"Analysis complete, but HTML file not found.")
                    messagebox.showwarning("File Not Found", 
                                          f"The HTML file could not be found at:\n{html_file}")
                
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")
            self.status_var.set("Error occurred")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalysisLauncher(root)
    root.mainloop()
