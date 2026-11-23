import os
import http.server
import socketserver
import socket
import json
import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib

from CalibrationWindow import CalibrateSettingsWindow 
from ChannelHistoryWindow import ChannelHistoryWindow 
from SocketDataAcquire import ChannelDef, SocketDataAcquire
from TCPIPReader import TelemetryServer 
from WebUIHelpers import ReusableTCPServer,ProjectorRequestHandler 
from SampleSettingsWindow import SampleSettingsWindow 


matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TelemetryMonitorApp:
    def __init__(self, root):
        self.projection_thr_lock = threading.Lock() 
        self.root = root
        self.root.title("Axis Monitoring V1.01")
        self.root.geometry("1500x1050")
        self.root.configure(bg="#0f172a")

        # Configuration variables
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="40001")
        self.sim_mode_var = tk.BooleanVar(value=True) 
        self.show_extreme_var = tk.BooleanVar(value=False) 
        self.connected = False
        self.socket_thread = None
        self.stop_event = threading.Event()
        self.data_acquire_handle = SocketDataAcquire(self.host_var.get(), int(self.port_var.get()), self.data_plotting_from_socket)  

        self.acquire_chn1 = ChannelDef("R - AXIS", "mm", 80, "#06b6d4")
        self.acquire_chn2 = ChannelDef("T - AXIS", "mm", 80, "#06b6d4")
        self.acquire_chn3 = ChannelDef("Z - AXIS", "mm", 80, "#06b6d4")

        

        # Channel Data Models
        self.channels = [
            {
                "id": 1,
                "title": self.acquire_chn1.ChannelName,
                "unit": self.acquire_chn1.ChannelUnit,
                "color": self.acquire_chn1.ChannelColor, # Cyan
                "data_buffer": self.acquire_chn1.DataScale,
                "current": 0.0,
                "prev": 0.0,
                "highest": float('-inf') ,
                "lowest": float('-inf') ,
                "max_limit": self.acquire_chn1.ChannelMax, 
                "data_body": self.acquire_chn1,
                "violation_count": 0,        # <--- ADD THIS
                "chn_vp1": 0.0,    # <--- ADD THIS DEFAULT P1
                "chn_vp2": 100.0,  # <--- ADD THIS DEFAULT P2
                "x_counter": 0,
                "x_data": [],
                "data": [],
                "was_out_of_range": False
            },
            {
                "id": 2,
                "title": self.acquire_chn2.ChannelName,
                "unit": self.acquire_chn2.ChannelUnit,
                "color": self.acquire_chn2.ChannelColor, # Emerald
                "data_buffer": self.acquire_chn2.DataScale, 
                "current": 0.0,
                "prev": 0.0,
                "highest": float('-inf') ,
                "lowest": float('-inf') ,
                "max_limit": self.acquire_chn2.ChannelMax, 
                "data_body": self.acquire_chn2,
                "violation_count": 0,        # <--- ADD THIS
                "chn_vp1": 0.0,    # <--- ADD THIS DEFAULT P1
                "chn_vp2": 100.0,  # <--- ADD THIS DEFAULT P2
                "x_counter": 0,
                "x_data": [],
                "data": [],
                "was_out_of_range": False,
            },
            {
                "id": 3,
                "title": self.acquire_chn3.ChannelName,
                "unit": self.acquire_chn3.ChannelUnit,
                "color": self.acquire_chn3.ChannelColor, 
                "data_buffer": self.acquire_chn3.DataScale, 
                "current": 0.0,
                "prev": 0.0,
                "highest": float('-inf') ,
                "lowest": float('-inf') ,
                "max_limit": self.acquire_chn3.ChannelMax,
                "data_body": self.acquire_chn3,
                "violation_count": 0,        # <--- ADD THIS
                "chn_vp1": 0.0,    # <--- ADD THIS DEFAULT P1
                "chn_vp2": 100.0,  # <--- ADD THIS DEFAULT P2
                "x_counter": 0,
                "x_data": [],
                "data": [],
                "was_out_of_range": False,
            }
        ]

        self.setup_styles()
        self.create_widgets()
        
        # Start data acquisition loop
        self.running = True
        self.update_thread = threading.Thread(target=self.data_acquisition_loop, daemon=True)
        self.open_online_monitor() 
        self.update_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#0f172a", foreground="#f8fafc")
        style.configure("TLabel", background="#1e293b", foreground="#f8fafc", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))

    def create_widgets(self):
        # Top Control Bar
        control_frame = tk.Frame(self.root, bg="#1e293b", padx=15, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Label(control_frame, text="Host:", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        tk.Entry(control_frame, textvariable=self.host_var, width=15, bg="#334155", fg="#ffffff", insertbackground="white", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(control_frame, text="Port:", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        tk.Entry(control_frame, textvariable=self.port_var, width=8, bg="#334155", fg="#ffffff", insertbackground="white", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 15))

        self.connect_btn = tk.Button(control_frame, 
                                     text="Connect Socket", 
                                     bg="#0284c7", 
                                     fg="white", 
                                     activebackground="#0369a1", 
                                     activeforeground="white", 
                                     relief=tk.FLAT, 
                                     padx=12, 
                                     pady=5, 
                                     command=self.toggle_connection)

        self.connect_btn.pack(side=tk.LEFT, padx=(0, 15))

        self.calibrate_btn = tk.Button(
            control_frame, 
            text="Teaching & Calibrate", 
            bg="#475569", 
            fg="white", 
            activebackground="#64748b", 
            activeforeground="white", 
            relief=tk.FLAT, 
            padx=10, 
            pady=5, 
            command=self.open_calibration_window
        ) 

        self.calibrate_btn.pack(side = tk.LEFT, padx = (0,12)) 

        self.samplesettings_btn = tk.Button(
            control_frame,
            text = "Sample Settings", 
            bg = "#12DA55", 
            fg = "black", 
            relief = tk.FLAT, 
            padx = 10, 
            pady= 5,
            command = self.open_sample_settings_window)  
        self. samplesettings_btn.pack(side = tk.LEFT, padx = (0,15)) 


        sim_check = tk.Checkbutton(control_frame, text="Simulator Mode (Fallback)", variable=self.sim_mode_var, bg="#1e293b", fg="#38bdf8", selectcolor="#334155", activebackground="#1e293b", activeforeground="#38bdf8", font=("Segoe UI", 10, "bold"))
        sim_check.pack(side=tk.LEFT, padx=(0, 15))

        tk.Button(control_frame, text="Reset Peaks", bg="#475569", fg="white", activebackground="#64748b", activeforeground="white", relief=tk.FLAT, padx=10, pady=5, command=self.reset_peaks).pack(side=tk.RIGHT)


        self.extreme_btn = tk.Button(control_frame, text="Show Extreme", bg="#475569", fg="white", activebackground="#64748b", activeforeground="white", relief=tk.FLAT, padx=10, pady=5, command=self.toggle_extreme)
        self.extreme_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Main Content Grid for 3 Channels
        channels_container = tk.Frame(self.root, bg="#0f172a")
        channels_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        channels_container.columnconfigure(0, weight=1)
        channels_container.rowconfigure((0,1,2), weight=1, uniform="row") 

        self.channel_uis = []
        for i, ch in enumerate(self.channels):
            frame = self.create_channel_card_optimized(channels_container, ch)
            frame.grid(row=i, column=0, sticky="nsew", pady=5, padx = 0) 


    def create_channel_card_optimized(self, parent, ch_data):
        card = tk.Frame(parent, bg="#1e293b", bd=1, relief=tk.SOLID, highlightbackground="#334155", highlightthickness=1)
        card.pack_propagate(False)

        # Top Control & Metrics Bar (Single compact strip to save vertical space for the plot)
        top_bar = tk.Frame(card, bg="#1e293b", padx=10, pady=5)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        # Left side: Title & Unit entries
        left_info = tk.Frame(top_bar, bg="#1e293b")
        left_info.pack(side=tk.LEFT, anchor="w")

        title_entry = tk.Entry(left_info, font=("Segoe UI", 10, "bold"), bg="#1e293b", fg=ch_data["color"], bd=0, insertbackground="white", width=16)
        title_entry.insert(0, ch_data["title"])
        title_entry.pack(side=tk.LEFT, padx=(0, 10))
        title_entry.bind("<FocusOut>", lambda e, c=ch_data, te=title_entry: self.update_channel_title(c, te))

        unit_entry = tk.Entry(left_info, font=("Segoe UI", 9, "bold"), width=5, bg="#334155", fg="#cbd5e1", bd=0, justify="center", insertbackground="white")
        unit_entry.insert(0, ch_data["unit"])
        unit_entry.pack(side=tk.LEFT)
        unit_entry.bind("<FocusOut>", lambda e, c=ch_data, ue=unit_entry: self.update_channel_unit(c, ue)) 

        redraw_btn = tk.Button(top_bar, text="Redraw", bg="#334155", fg="#cbd5e1", activebackground="#475569", activeforeground="white", relief=tk.FLAT, padx=6, pady=2, font=("Segoe UI", 8), command=lambda c=ch_data: self.redraw_channel_plot(c))
        redraw_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Right side: History button & Compact Horizontal Metrics
        right_metrics = tk.Frame(top_bar, bg="#1e293b")
        right_metrics.pack(side=tk.RIGHT, anchor="e")

        # History Button
        history_btn = tk.Button(
            right_metrics, 
            text="History", 
            bg="#334155", 
            fg="#38bdf8", 
            activebackground="#475569", 
            activeforeground="#38bdf8", 
            relief=tk.FLAT, 
            padx=8, 
            pady=2,
            font=("Segoe UI", 8, "bold"),
            command=lambda c=ch_data: self.open_history_window(c)
        )
        history_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Compact metrics container frame
        metrics_box = tk.Frame(right_metrics, bg="#0f172a", padx=8, pady=3)
        metrics_box.pack(side=tk.RIGHT)

        # Helper function to create clean horizontal metric items
        def add_metric_item(parent_f, label_text, default_val, val_color, is_entry=False):
            f = tk.Frame(parent_f, bg="#0f172a")
            f.pack(side=tk.LEFT, padx=6)
            tk.Label(f, text=label_text, fg="#64748b", bg="#0f172a", font=("Segoe UI", 7, "bold")).pack(anchor="w")
            if is_entry:
                ent = tk.Entry(f, width=5, bg="#334155", fg=val_color, insertbackground="white", font=("Segoe UI", 9, "bold"), justify="center", bd=0)
                ent.insert(0, str(default_val))
                ent.pack(anchor="w")
                return ent
            else:
                lbl = tk.Label(f, text=str(default_val), fg=val_color, bg="#0f172a", font=("Segoe UI", 9, "bold"))
                lbl.pack(anchor="w")
                return lbl

        lbl_live = add_metric_item(metrics_box, "LIVE", "0.00", ch_data["color"])
        lbl_high = add_metric_item(metrics_box, "HIGH", "--", "#10b981")
        lbl_low = add_metric_item(metrics_box, "LOW", "--", "#ef4444")
        limit_entry = add_metric_item(metrics_box, "LIMIT", ch_data["max_limit"], "#f59e0b", is_entry=True)
        limit_entry.bind("<FocusOut>", lambda e, c=ch_data, le=limit_entry: self.update_channel_limit(c, le))
        lbl_faults = add_metric_item(metrics_box, "FAULTS", "0", "#ef4444")

        # --- MAXIMIZED PLOTTING PANEL ---
        plot_frame = tk.Frame(card, bg="#1e293b")
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        fig = Figure(figsize=(10, 2.2), dpi=100) # Expanded plot height
        fig.patch.set_facecolor('#1e293b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f172a')
        ax.tick_params(colors='#94a3b8', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#334155')
        
        line, = ax.plot(ch_data["data"], color=ch_data["color"], linewidth=0.5) 
        high_line = ax.axhline(y=0, color='#22c55e', linestyle='--', linewidth=0.4, alpha=0)
        low_line = ax.axhline(y=0, color='#22c55e', linestyle='--', linewidth=0.4, alpha=0)
        ax.set_ylim(-10, 110)
        ax.set_xlim(1, 10)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Store UI references
        ch_data["ui"] = {
            "card": card,
            "lbl_live": lbl_live,
            "lbl_high": lbl_high,
            "lbl_low": lbl_low,
            "lbl_faults": lbl_faults,
            "limit_entry": limit_entry,
            "fig": fig,
            "ax": ax,
            "line": line,
            "canvas": canvas,
            "high_line": high_line,
            "low_line": low_line 
        }

        return card


    def update_channel_title(self, ch, entry):
        ch["title"] = entry.get()

    def update_channel_unit(self, ch, entry):
        ch["unit"] = entry.get()

    def update_channel_limit(self, ch, entry):
        try:
            ch["max_limit"] = float(entry.get())
        except ValueError:
            entry.delete(0, tk.END)
            entry.insert(0, str(ch["max_limit"]))

    def reset_peaks(self):
        with self.projection_thr_lock:
            for ch in self.channels:
                ch["highest"] = float('-inf')
                ch["lowest"] = float('inf') 
                current_value = ch["current"] 
                ch["ui"]["lbl_high"].config(text='----')
                ch["ui"]["lbl_low"].config(text='----') 

    def redraw_channel_plot(self,data):
        ui = data["ui"]
        # Re-apply current refresh state to ensure clean redraw
        self.refresh_channel_ui(data)
        # Force canvas redraw backend call
        ui["canvas"].draw()
        ui["canvas"].flush_events() 

 
    def toggle_extreme(self):
        active = not self.show_extreme_var.get()
        self.show_extreme_var.set(active)
        
        if active:
            self.extreme_btn.config(bg="#10b981", fg="white") # Green highlight when active
        else:
            self.extreme_btn.config(bg="#475569", fg="white")
            
        # Refresh all channels immediately
        for ch in self.channels:
            self.refresh_channel_ui(ch) 

    def toggle_connection(self):
        if not self.connected:
            host = self.host_var.get()
            try:
                port = int(self.port_var.get())
            except ValueError:
                messagebox.showerror("Invalid Port", "Please enter a valid integer port number.")
                return

            self.sim_mode_var.set(False)
            self.stop_event.clear()
            self.socket_thread = threading.Thread(target=self.socket_client_worker, args=(host, port), daemon=True)
            self.socket_thread.start()
            self.connect_btn.config(text="Disconnect", bg="#ef4444")
            self.connected = True
        else:
            self.stop_event.set()
            self.connect_btn.config(text="Connect Socket", bg="#0284c7")
            self.connected = False

    def open_calibration_window(self):
        # Opens the external window class, optionally passing references like self.channels or self.root
        CalibrateSettingsWindow(self.root, self.channels) 

    def open_history_window(self, current_channel):
        ChannelHistoryWindow(self.root, current_channel)  

    def open_sample_settings_window(self):
        SampleSettingsWindow(self.root) 

    def socket_client_worker(self, host, port):
        self.data_acquire_handle.AcquireDataEvent(self.stop_event) 

    def data_plotting_from_socket(self, data):
        try:
            parsed = json.loads(data.decode('utf-8').strip())
            # Expecting format: {"ch1": 45.2, "ch2": 52.1, "ch3": 12.4}
            for i, ch_key in enumerate(["ch1", "ch2", "ch3"]):
                if ch_key in parsed:
                    val = float(parsed[ch_key])
                    self.push_data(self.channels[i], val)
        except Exception:
            pass

    


    def data_acquisition_loop(self):
        t = 0.0
        while self.running:
            if self.sim_mode_var.get():
                # Generate realistic simulation waveforms in mm
                val1 = 50.0 + 25.0 * (time.time() % 10 / 10.0) + random.uniform(-1.5, 1.5)
                val2 = 30.0 + 15.0 * ((time.time() * 1.5) % 6 / 6.0) + random.uniform(-1.0, 1.0)
                val3 = 55.0 + 20.0 * ((time.time() * 0.8) % 8 / 8.0) + random.uniform(-2.0, 2.0)

                self.push_data(self.channels[0], val1)
                self.push_data(self.channels[1], val2)
                self.push_data(self.channels[2], val3)

            time.sleep(0.1) # 10 updates per second

    def push_data(self, ch, val):
        with self.projection_thr_lock:
            ch["prev"] = ch["current"]
            ch["current"] = val

            # Update high/low
            if val > ch["highest"]:
                ch["highest"] = val
            if val < ch["lowest"]:
                ch["lowest"] = val

            # Append to plot buffer
            ch["data_buffer"].pop(0)
            ch["data_buffer"].append(val) 
            ch["data_body"].EmplaceDataScale(val) 

            if ch["x_counter"] >= 10000:
                ch["x_data"].clear()
                ch["data"].clear()
                ch["x_counter"] = 0

            ch["x_counter"] += 1
            ch["x_data"].append(ch["x_counter"])
            ch["data"].append(val)

            # Schedule UI update on main thread
            self.root.after(0, lambda: self.refresh_channel_ui(ch))

    def redraw_channel(self,ch):
        with self.projection_thr_lock:
            # Clear current plot and restart X count from 1 on next incoming point
            ch["x_data"].clear()
            ch["data"].clear()
            ch["x_counter"] = 0
            self.refresh_channel_ui(ch)

    def refresh_channel_ui(self, ch):
        ui = ch["ui"]
        unit = ch["unit"]
        
        # Update text metrics
        ui["lbl_live"].config(text=f"{ch['current']:.2f} {unit}")
        ui["lbl_high"].config(text=f"{ch['highest']:.2f} {unit}")
        ui["lbl_low"].config(text=f"{ch['lowest']:.2f} {unit}")

        is_out_of_range = ch["current"] > ch["max_limit"]

        if is_out_of_range:
            # Trigger warning highlight
            ui["card"].config(highlightbackground="#ef4444", highlightthickness=2)
            ui["lbl_live"].config(fg="#ef4444")
            
            # Count only on the rising edge (when it first exceeds the limit)
            if not ch["was_out_of_range"]:
                ch["violation_count"] += 1
                ch["was_out_of_range"] = True
        else:
            # Revert to normal state
            ui["card"].config(highlightbackground="#334155", highlightthickness=1)
            ui["lbl_live"].config(fg=ch["color"])
            ch["was_out_of_range"] = False

        # Update violation counter label text
        ui["lbl_faults"].config(text=str(ch["violation_count"]))

        # --- HIGHLIGHT CHECK ---
        if ch["current"] > ch["max_limit"]:
            # Trigger warning highlight (Red border & slight red tint or warning look)
            ui["card"].config(highlightbackground="#ef4444", highlightthickness=2)
            ui["lbl_live"].config(fg="#ef4444") # highlight live text red
        else:
            # Revert to normal state
            ui["card"].config(highlightbackground="#334155", highlightthickness=1)
            ui["lbl_live"].config(fg=ch["color"])

        # Update plot data
        if ch["data"]:
            ui["line"].set_data(ch["x_data"], ch["data"])

            # Scale X-axis from 1 up to current point count (with a small right pad)
            x_max = max(10, ch["x_counter"] + 1)
            ui["ax"].set_xlim(1, x_max)

            # Show Extreme lines & Y-axis scaling
            if self.show_extreme_var.get() and ch["highest"] != float('inf') and ch["lowest"] != float('-inf'):
                ui["high_line"].set_ydata([ch["highest"], ch["highest"]])
                ui["high_line"].set_alpha(0.85)
                ui["low_line"].set_ydata([ch["lowest"], ch["lowest"]])
                ui["low_line"].set_alpha(0.85)

                ymin, ymax = ch["lowest"], ch["highest"]
                span = max(2.0, ymax - ymin)
                ui["ax"].set_ylim(ymin - span * 0.25, ymax + span * 0.25)
            else:
                ui["high_line"].set_alpha(0)
                ui["low_line"].set_alpha(0)

                ymin, ymax = min(ch["data"]), max(ch["data"])
                margin = max(2.0, (ymax - ymin) * 0.2)
                ui["ax"].set_ylim(ymin - margin, ymax + margin)
        else:
            # Cleared state before next point arrives
            ui["line"].set_data([], [])
            ui["ax"].set_xlim(1, 10)

        ui["canvas"].draw_idle() 

    def open_online_monitor(self):
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channel_monitor.html")
        self.web_server = self.start_web_projector(html_path, host="127.0.0.1", port=8080) 

    def get_serialized_state(self):
        with self.projection_thr_lock:
            payload = {
                "show_extreme": bool(self.show_extreme_var.get()),
                "channels": [
                    {
                        "id": ch["id"],
                        "title": ch["title"],
                        "unit": ch["unit"],
                        "color": ch["color"],
                        "max_limit": ch["max_limit"],
                        "current": ch["current"],
                        "highest": None if ch["highest"] == float("-inf") else ch["highest"],
                        "lowest": None if ch["lowest"] == float("inf") else ch["lowest"],
                        "x_counter": ch["x_counter"],
                        "x_data": list(ch["x_data"]),
                        "data": list(ch["data"]),
                    }
                    for ch in self.channels
                ],
            }
        return json.dumps(payload).encode("utf-8")

    def start_web_projector(self, html_file_path, host="127.0.0.1", port=8080):
        app_ref = self 


        class ProjectorRequestHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/", "/index.html", "/channel_plot_projector.html","/channel_monitor.html"):
                    try:
                        with open(html_file_path, "rb") as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                    except FileNotFoundError:
                        self.send_error(404, "channel_plot_projector.html not found") 
                elif self.path.startswith("/api/state"):
                    body = app_ref.get_serialized_state()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404, "Not Found")

            def log_message(self, format, *args):
                # Suppress noisy console HTTP logs
                pass

        class ReusableTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            allow_reuse_address = True
            daemon_threads = True

        server = ReusableTCPServer((host, port), ProjectorRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        return server

    def on_close(self):
        self.running = False
        self.stop_event.set()
        self.root.destroy() 

def startTelemetryServer():
    server = TelemetryServer("127.0.0.1",40001) 
    t1 = threading.Thread(target = server.RunTelemetryServer) 
    t1.start() 


if __name__ == "__main__":
    startTelemetryServer() 
    root = tk.Tk()
    app = TelemetryMonitorApp(root)
    root.mainloop()
