import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

class ChannelHistoryWindow:
    def __init__(self, parent_root, channel_data):
        self.top = tk.Toplevel(parent_root)
        self.ch_data = channel_data
        
        title_name = self.ch_data.get("title", "Channel")
        self.top.title(f"Channel History - {title_name}")
        self.top.geometry("480x580")
        self.top.configure(bg="#0f172a")

        self.create_widgets() 
        self.setup_table_styling() 
        self.populate_table()

    
    def create_widgets(self):
        # Header Label
        ch_title = self.ch_data.get("title", "Channel")
        header = tk.Label(self.top, text=f"Newest History Readings: {ch_title}", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 12, "bold"))
        header.pack(pady=15) 
        self.pack_bottom_buttons() 
        self.pack_tables() 

        


    def pack_tables(self):
        # Table Container Frame with Scrollbar
        table_frame = tk.Frame(self.top, bg="#1e293b", padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Treeview Table Setup
        columns = ("index", "value", "unit")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        
        self.tree.heading("index", text="Sequence / Index")
        self.tree.heading("value", text="Reading Value")
        self.tree.heading("unit", text="Unit")

        self.tree.column("index", width=110, anchor="center")
        self.tree.column("value", width=150, anchor="center")
        self.tree.column("unit", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y) 


        

    def pack_bottom_buttons(self):
        # Bottom Action Buttons Frame
        btn_frame = tk.Frame(self.top, bg="#0f172a")
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # --- EXPORT TO CSV BUTTON ---
        tk.Button(
            btn_frame, 
            text="Export to CSV", 
            bg="#0284c7", 
            fg="white", 
            activebackground="#0369a1",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=12, 
            pady=6,
            font=("Segoe UI", 9, "bold"),
            command=self.export_to_csv
        ).pack(side=tk.LEFT)

        # Close Button
        tk.Button(
            btn_frame, 
            text="Close Window", 
            bg="#475569", 
            fg="white", 
            activebackground="#64748b",
            activeforeground="white",
            relief=tk.FLAT, 
            padx=12, 
            pady=6,
            font=("Segoe UI", 9),
            command=self.top.destroy
        ).pack(side=tk.RIGHT) 


    def populate_table(self):
        # Clear existing rows if any
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Get data buffer and slice the newest 30
        newest_count = 30 
        data_buffer = self.ch_data.get("data", [])
        newest_30 = data_buffer[-newest_count:]
        unit = self.ch_data.get("unit", "mm")

        # Insert items into the table in reverse chronological order (newest first)
        for i, val in enumerate(reversed(newest_30)):
            seq_num = newest_count - i
            self.tree.index = self.tree.insert("", tk.END, values=(f"#{seq_num}", f"{val:.2f}", unit)) 

    def setup_table_styling(self):
        style = ttk.Style()
        style.theme_use("clam") # 'clam' allows full color customization of ttk widgets
        
        # Configure Table Header styling (Dark grey background, yellow text)
        style.configure(
            "Treeview.Heading",
            background="#1e293b",
            foreground="#facc15", # Yellow heading text
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview.Heading", background=[('active', '#334155')])

        # Configure Table Body row styling (Pure black background `#000000`, yellow text `#facc15`)
        style.configure(
            "Treeview",
            background="#000000",          # Black row background
            fieldbackground="#000000",      # Black field background
            foreground="#facc15",          # Yellow text letters
            font=("Segoe UI", 10),
            rowheight=25
        )
        
        # Configure row selection color (Dark blue highlight when clicking a row, keeping text readable)
        style.map("Treeview", background=[('selected', '#1e3a8a')], foreground=[('selected', '#ffffff')])

    def export_to_csv(self):
        # Open save file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export Channel History"
        )
        if not file_path:
            return # User cancelled dialog

        try:
            unit = self.ch_data.get("unit", "mm")
            data_buffer = self.ch_data.get("data", [])
            newest_30 = data_buffer[-30:]

            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write CSV Header
                writer.writerow(["Sequence Index", f"Reading Value ({unit})", "Unit"])
                
                # Write rows matching the table view
                for i, val in enumerate(reversed(newest_30)):
                    seq_num = len(data_buffer) - i
                    writer.writerow([f"#{seq_num}", f"{val:.2f}", unit])

            messagebox.showinfo("Export Successful", f"History data successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save CSV file:\n{str(e)}")
