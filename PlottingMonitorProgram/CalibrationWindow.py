import tkinter as tk
from tkinter import ttk, messagebox
from ParameterServer import pServer 

class CalibrateSettingsWindow:
    def __init__(self, parent_root, channels_data):
        self.top = tk.Toplevel(parent_root)
        self.top.title("Teaching & Calibration Settings")
        self.top.geometry("650x480")
        self.top.configure(bg="#0f172a")
        
        # Reference to the main app's channels list of dicts
        self.channels = channels_data 

        self.create_widgets()
        self.load_channel_calibration_values(0) # Load Channel 1 by default 

    def init_values(self, channel_data): 
       values = [] 
       for chn_data in channel_data:
           data_name = chn_data["title"] 
           values.append(data_name)

       return values 



    def create_widgets(self):
        # Header
        header = tk.Label(self.top, text="Channel Teaching & Calibration (P1 / P2)", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 13, "bold"))
        header.pack(pady=15)

        # Main Frame Container
        frame = tk.Frame(self.top, bg="#1e293b", padx=20, pady=20, bd=1, relief=tk.SOLID, highlightbackground="#334155", highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Channel Selector
        tk.Label(frame, text="Select Channel:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.ch_combo = ttk.Combobox(frame, values=self.init_values(self.channels), state="readonly", font=("Segoe UI", 10))
        self.ch_combo.current(0)
        self.ch_combo.pack(anchor="w", pady=(0, 15), fill=tk.X)
        self.ch_combo.bind("<<ComboboxSelected>>", self.on_channel_selected)

        # Input Field: Channel Value P1
        tk.Label(frame, text="Channel Value P1 (chn_vp1):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 2))
        self.p1_entry = tk.Entry(frame, bg="#334155", fg="#f8fafc", insertbackground="white", font=("Segoe UI", 11))
        self.p1_entry.pack(anchor="w", pady=(0, 15), fill=tk.X)

        # Input Field: Channel Value P2
        tk.Label(frame, text="Channel Value P2 (chn_vp2):", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 2))
        self.p2_entry = tk.Entry(frame, bg="#334155", fg="#f8fafc", insertbackground="white", font=("Segoe UI", 11))
        self.p2_entry.pack(anchor="w", pady=(0, 20), fill=tk.X)

        # Action Buttons Frame
        btn_frame = tk.Frame(frame, bg="#1e293b")
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            btn_frame, 
            text="Save Calibration", 
            bg="#0284c7", 
            fg="white", 
            activebackground="#0369a1",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=15, 
            pady=8,
            font=("Segoe UI", 10, "bold"),
            command=self.save_calibration).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            btn_frame, 
            text="Close Window", 
            bg="#475569", 
            fg="white", 
            activebackground="#64748b",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=15, 
            pady=8,
            font=("Segoe UI", 10),
            command=self.top.destroy
        ).pack(side=tk.RIGHT)

    def on_channel_selected(self, event):
        idx = self.ch_combo.current()
        self.load_channel_calibration_values(idx)

    def load_channel_calibration_values(self, index):
        ch = self.channels[index]
        # Ensure keys exist with defaults
        if "chn_vp1" not in ch:
            ch["chn_vp1"] = 0.0
        if "chn_vp2" not in ch:
            ch["chn_vp2"] = 100.0

        # Populate entry fields from channel reference dict
        self.p1_entry.delete(0, tk.END)
        self.p1_entry.insert(0, str(ch["chn_vp1"]))

        self.p2_entry.delete(0, tk.END)
        self.p2_entry.insert(0, str(ch["chn_vp2"]))

    def save_calibration(self):
        try:
            idx = self.ch_combo.current()
            val_p1 = float(self.p1_entry.get())
            val_p2 = float(self.p2_entry.get())

            # Store back into the channel reference dicts
            self.channels[idx]["chn_vp1"] = val_p1
            self.channels[idx]["chn_vp2"] = val_p2 

            pServer.AddInServer(idx,"ReferenceValue",val_p2) 

            messagebox.showinfo("Success", f"Calibration saved for Channel {idx + 1}!\nchn_vp1: {val_p1}\nchn_vp2: {val_p2}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for P1 and P2.")