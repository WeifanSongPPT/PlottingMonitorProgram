import tkinter as tk
from tkinter import ttk, messagebox

from CalibrationWindow import pServer


class SampleSettingsWindow:
    def __init__(self, root: tk.Tk):
        self.root = tk.Toplevel(root) 
        self.root.title("Sample Settings")
        self.root.geometry("640x320") 
        self.root.configure(bg = "#0f172a") 

        self.create_widgets() 

    def create_widgets(self):
        #Createing the header 
        header = tk.Label(self.root, text="Sampling Settings", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 13, "bold"))
        header.pack(pady=15) 

        #creating container 
        frame = tk.Frame(self.root, bg="#1e293b", padx=20, pady=20, bd=1, relief=tk.SOLID, highlightbackground="#334155", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        #Sampling interval inputbox 
        tk.Label(frame, text="Sampling Interval:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 2))
        self.sampling_interval_entry = tk.Entry(frame, bg="#334155", fg="#f8fafc", insertbackground="white", font=("Segoe UI", 11))
        self.sampling_interval_entry.pack(anchor="w", pady=(0, 15), fill=tk.X)

        #Sample count interval inputbox 
        tk.Label(frame, text="Sample Count:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 2))
        self.sample_count_entry = tk.Entry(frame, bg="#334155", fg="#f8fafc", insertbackground="white", font=("Segoe UI", 11))
        self.sample_count_entry.pack(anchor="w", pady=(0, 20), fill=tk.X)

        #Buttons 
        btn_frame = tk.Frame(frame, bg="#1e293b")
        btn_frame.pack(fill=tk.X, pady=5)

        self.save_btn = tk.Button(
            btn_frame, 
            text="Save Settings", 
            bg="#0284c7", 
            fg="white", 
            activebackground="#0369a1",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=15, 
            pady=8,
            font=("Segoe UI", 10, "bold"),
            command=self.save_settings) 

        self.save_btn.pack(side=tk.LEFT, padx=(0, 15)) 

        self.close_btn = tk.Button(
            btn_frame, 
            text="Close Window", 
            bg="#475569", 
            fg="white", 
            activebackground="#64748b",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=15, 
            pady=8,
            font=("Segoe UI", 10, "bold"), 
            command=self.root.destroy)
        self.close_btn.pack(side = tk.LEFT, padx = (0,15)) 

        self.save_and_close_btn = tk.Button(
             btn_frame, 
            text="Save & Exit", 
            bg="#12AF22", 
            fg="black", 
            activebackground="#64748b",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=15, 
            pady=8,
            font=("Segoe UI", 10),)
        self.save_and_close_btn.pack(side = tk.RIGHT, padx = (0,15)) 


    def save_settings(self):
        try:
            sampingCount = int(self.sample_count_entry.get()) 
            sampingInterval = float(self.sampling_interval_entry.get()) 
            pServer.AddCommonParameters("SampleCount", sampingCount) 
            pServer.AddCommonParameters("SampleIntervalSecords", sampingInterval) 
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for P1 and P2.") 