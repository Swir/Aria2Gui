import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

APP_NAME = "Aria2 Ultimate PRO by Swir"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2_gui_config.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class Aria2Downloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1200x880")
        self.minsize(1050, 800)
        
        # "Cyber Neon" Palette
        self.COLORS = {
            "bg": "#13131f",          
            "panel": "#1e1e2f",       
            "accent_cyan": "#00f0ff", 
            "accent_pink": "#ff007f", 
            "success": "#39ff14",     
            "text_main": "#e0e0ff",   
            "text_muted": "#6b6b8e"   
        }
        self.configure(fg_color=self.COLORS["bg"])

        self.process = None
        self.running = False
        self.paused = False
        self.log_queue = queue.Queue()
        self.queue_data = [] 
        self.session_start_time = None
        self.archive_links = []

        self.input_var = ctk.StringVar()
        self.save_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.connections_var = ctk.StringVar(value="16")
        self.segments_var = ctk.StringVar(value="16")
        self.chunk_var = ctk.StringVar(value="4M")
        self.max_concurrent_var = ctk.StringVar(value="5")
        self.dl_limit_var = ctk.StringVar(value="0")
        self.ul_limit_var = ctk.StringVar(value="1M") 
        
        # Security & Resuming Settings
        self.auto_resume_var = ctk.BooleanVar(value=True)
        self.auto_retry_var = ctk.BooleanVar(value=True)
        self.max_tries_var = ctk.StringVar(value="50")
        self.retry_wait_var = ctk.StringVar(value="5")
        
        self.status_var = ctk.StringVar(value="SYSTEM READY")
        self.speed_var = ctk.StringVar(value="DL: 0 B/s | UL: 0 B/s")
        self.size_var = ctk.StringVar(value="Size: -- / --")
        self.eta_var = ctk.StringVar(value="ETA: --:--:--")
        self.aria_var = ctk.StringVar(value="Initializing...")
        self.uptime_var = ctk.StringVar(value="Session time: 00:00:00")

        self.load_config()
        self.setup_ttk_styles_for_treeview()
        self.build_ui()
        self.find_aria2()
        
        self.after(50, self.process_log_queue)
        self.after(1000, self.update_uptime)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ttk_styles_for_treeview(self):
        style = ttk.Style(self)
        try: style.theme_use("default")
        except Exception: pass

        style.configure("Treeview", 
                        background=self.COLORS["panel"], 
                        fieldbackground=self.COLORS["panel"], 
                        foreground=self.COLORS["text_main"], 
                        rowheight=35, borderwidth=0, font=("Segoe UI", 10))
        style.map("Treeview", 
                  background=[("selected", self.COLORS["accent_pink"])], 
                  foreground=[("selected", "white")])
        style.configure("Treeview.Heading", 
                        background=self.COLORS["bg"], 
                        foreground=self.COLORS["accent_cyan"], 
                        font=("Segoe UI", 11, "bold"), borderwidth=0, padding=5)

    def build_ui(self):
        top_panel = ctk.CTkFrame(self, fg_color=self.COLORS["panel"], corner_radius=15)
        top_panel.pack(side="top", fill="x", padx=20, pady=(20, 10))
        
        header_wrap = ctk.CTkFrame(top_panel, fg_color="transparent")
        header_wrap.pack(fill="x", padx=20, pady=(20, 15))
        ctk.CTkLabel(header_wrap, text="🚀 ARIA2 ULTIMATE PRO", font=("Segoe UI Black", 24), text_color=self.COLORS["accent_cyan"]).pack(side="left")
        ctk.CTkLabel(header_wrap, textvariable=self.aria_var, font=("Segoe UI", 12), text_color=self.COLORS["text_muted"]).pack(side="right", anchor="s")

        input_grid = ctk.CTkFrame(top_panel, fg_color="transparent")
        input_grid.pack(fill="x", padx=20, pady=(0, 15))
        input_grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(input_grid, text="Save to:", font=("Segoe UI", 13, "bold"), text_color=self.COLORS["text_main"]).grid(row=0, column=0, sticky="w", pady=8)
        ctk.CTkEntry(input_grid, textvariable=self.save_var, font=("Consolas", 12), fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_cyan"], border_width=1).grid(row=0, column=1, sticky="ew", padx=15, pady=8, ipady=4)
        ctk.CTkButton(input_grid, text="📂 Browse", command=self.choose_folder, fg_color=self.COLORS["bg"], hover_color=self.COLORS["accent_pink"], border_color=self.COLORS["accent_cyan"], border_width=1).grid(row=0, column=2, padx=(0, 5))
        ctk.CTkButton(input_grid, text="📁 Open", command=self.open_folder, fg_color=self.COLORS["bg"], hover_color=self.COLORS["accent_cyan"], border_color=self.COLORS["accent_cyan"], border_width=1).grid(row=0, column=3)

        ctk.CTkLabel(input_grid, text="New task:", font=("Segoe UI", 13, "bold"), text_color=self.COLORS["text_main"]).grid(row=1, column=0, sticky="w", pady=8)
        
        self.input_entry = ctk.CTkEntry(input_grid, textvariable=self.input_var, placeholder_text="Paste link here (HTTP, HTTPS, FTP, Magnet, Metalink...)", font=("Consolas", 12), fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"], border_width=1)
        self.input_entry.grid(row=1, column=1, sticky="ew", padx=15, pady=(8, 2), ipady=4)
        
        btn_frame = ctk.CTkFrame(input_grid, fg_color="transparent")
        btn_frame.grid(row=1, column=2, columnspan=2, sticky="e")
        ctk.CTkButton(btn_frame, text="📋 Paste", width=80, command=self.paste_url, fg_color=self.COLORS["bg"], hover_color=self.COLORS["accent_cyan"]).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="➕ Add URL", width=100, command=self.add_url_to_queue, fg_color=self.COLORS["accent_pink"], hover_color="#d10068").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🧲 Add .torrent", width=120, command=self.add_torrent_to_queue, fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"], border_width=1, hover_color=self.COLORS["accent_pink"]).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(input_grid, text="💡 Supported types: HTTP, HTTPS, FTP, SFTP, Magnet Link, Metalink and local .torrent files", font=("Segoe UI", 10, "italic"), text_color=self.COLORS["text_muted"]).grid(row=2, column=1, sticky="w", padx=15, pady=(0, 5))

        bottom_panel = ctk.CTkFrame(self, fg_color=self.COLORS["panel"], corner_radius=15)
        bottom_panel.pack(side="bottom", fill="x", padx=20, pady=(10, 20))

        stats_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(stats_frame, textvariable=self.status_var, font=("Consolas", 15, "bold"), text_color=self.COLORS["success"]).pack(side="left")
        ctk.CTkLabel(stats_frame, textvariable=self.speed_var, font=("Consolas", 15, "bold"), text_color=self.COLORS["accent_cyan"]).pack(side="right")

        self.progress = ctk.CTkProgressBar(bottom_panel, progress_color=self.COLORS["success"], fg_color=self.COLORS["bg"], height=15)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=20, pady=10)

        substats_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        substats_frame.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(substats_frame, textvariable=self.size_var, font=("Consolas", 11), text_color=self.COLORS["text_main"]).pack(side="left")
        ctk.CTkLabel(substats_frame, textvariable=self.uptime_var, font=("Consolas", 11, "italic"), text_color=self.COLORS["text_muted"]).pack(side="left", padx=30)
        ctk.CTkLabel(substats_frame, textvariable=self.eta_var, font=("Consolas", 11), text_color=self.COLORS["accent_pink"]).pack(side="right")

        action_bar = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        action_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(action_bar, text="▶ START DOWNLOAD", font=("Segoe UI Black", 14), fg_color=self.COLORS["accent_cyan"], text_color="#000000", hover_color="#00c8d4", command=self.start_download, height=45).pack(side="left", padx=(0, 10))
        ctk.CTkButton(action_bar, text="⏸ Pause", font=("Segoe UI", 12, "bold"), fg_color=self.COLORS["bg"], border_width=1, border_color=self.COLORS["accent_cyan"], command=self.pause_download, height=45).pack(side="left", padx=4)
        ctk.CTkButton(action_bar, text="⏹ Stop", font=("Segoe UI", 12, "bold"), fg_color=self.COLORS["bg"], border_width=1, border_color=self.COLORS["accent_pink"], command=self.stop_download, height=45).pack(side="left", padx=4)
        ctk.CTkButton(action_bar, text="🗑 Clear Queue", font=("Segoe UI", 12, "bold"), fg_color="#cf0000", hover_color="#990000", command=self.clear_queue, height=45).pack(side="right")

        self.tabview = ctk.CTkTabview(self, fg_color=self.COLORS["panel"], segmented_button_fg_color=self.COLORS["bg"], segmented_button_selected_color=self.COLORS["accent_cyan"], segmented_button_selected_hover_color="#00c8d4", segmented_button_unselected_color=self.COLORS["bg"], text_color=self.COLORS["text_main"])
        self.tabview.pack(side="top", fill="both", expand=True, padx=20, pady=0)

        self.tab_queue = self.tabview.add(" 📥 QUEUE ")
        self.tab_logs = self.tabview.add(" 📜 TERMINAL ")
        self.tab_archive = self.tabview.add(" 🔍 ARCHIVE SCANNER ")
        self.tab_settings = self.tabview.add(" ⚙ SETTINGS ")

        self.build_queue_tab()
        self.build_logs_tab()
        self.build_archive_tab()
        self.build_settings_tab()

    def build_queue_tab(self):
        columns = ("type", "source")
        self.queue_tree = ttk.Treeview(self.tab_queue, columns=columns, show="headings", selectmode="extended")
        self.queue_tree.heading("type", text="FORMAT")
        self.queue_tree.heading("source", text="PATH / URL")
        self.queue_tree.column("type", width=120, anchor="center")
        self.queue_tree.column("source", width=700, anchor="w")
        self.queue_tree.pack(side="left", fill="both", expand=True, pady=10)
        
        scroll = ctk.CTkScrollbar(self.tab_queue, command=self.queue_tree.yview, fg_color="transparent", button_color=self.COLORS["bg"], button_hover_color=self.COLORS["accent_cyan"])
        scroll.pack(side="right", fill="y", pady=10)
        self.queue_tree.configure(yscrollcommand=scroll.set)
        
        self.queue_tree.bind("<Delete>", self.remove_selected_from_queue)
        
        self.context_menu = tk.Menu(self, tearoff=0, bg=self.COLORS["panel"], fg=self.COLORS["text_main"], activebackground=self.COLORS["accent_cyan"], activeforeground="#000", borderwidth=0)
        self.context_menu.add_command(label="🔄 Replace expired link (Resume with new)", command=self.update_expired_link)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Copy URL", command=self.copy_selected_url)
        self.context_menu.add_command(label="🗑 Remove from queue (Del)", command=self.remove_selected_from_queue)
        self.queue_tree.bind("<Button-3>", self.show_context_menu)

    def build_logs_tab(self):
        self.log = ctk.CTkTextbox(self.tab_logs, fg_color=self.COLORS["bg"], text_color=self.COLORS["accent_cyan"], font=("Consolas", 12), corner_radius=10)
        self.log.pack(fill="both", expand=True, pady=10)
        self.log.configure(state="disabled")

    def build_archive_tab(self):
        header_frame = ctk.CTkFrame(self.tab_archive, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_frame, text="Paste Archive.org link in the main bar, then click Scan.", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkButton(header_frame, text="🔍 SCAN ARCHIVE.ORG", font=("Segoe UI", 12, "bold"), fg_color=self.COLORS["accent_pink"], hover_color="#d10068", command=self.scan_archive).pack(side="right")
        
        columns = ("select", "name", "size")
        self.arc_tree = ttk.Treeview(self.tab_archive, columns=columns, show="headings", selectmode="extended")
        self.arc_tree.heading("select", text="[X]")
        self.arc_tree.heading("name", text="File name")
        self.arc_tree.heading("size", text="Size")
        self.arc_tree.column("select", width=60, anchor="center")
        self.arc_tree.column("name", width=600, anchor="w")
        self.arc_tree.column("size", width=150, anchor="e")
        self.arc_tree.pack(side="left", fill="both", expand=True)
        
        scroll = ctk.CTkScrollbar(self.tab_archive, command=self.arc_tree.yview, fg_color="transparent", button_color=self.COLORS["bg"], button_hover_color=self.COLORS["accent_pink"])
        scroll.pack(side="right", fill="y")
        self.arc_tree.configure(yscrollcommand=scroll.set)
        self.arc_tree.bind("<Double-1>", self.toggle_archive_selected)

        ctrl = ctk.CTkFrame(self.tab_archive, fg_color="transparent")
        ctrl.pack(fill="x", pady=(15, 0))
        ctk.CTkButton(ctrl, text="☑ Select All", command=lambda: self.set_all_archive(True), fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_cyan"], border_width=1).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="☐ Deselect All", command=lambda: self.set_all_archive(False), fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"], border_width=1).pack(side="left")
        ctk.CTkLabel(ctrl, text="💡 Selected files instantly jump to the Download Queue!", font=("Segoe UI", 11, "italic"), text_color=self.COLORS["accent_cyan"]).pack(side="right")

    def build_settings_tab(self):
        f = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        f.pack(fill="both", expand=True)

        ctk.CTkLabel(f, text="⚡ CORE DOWNLOAD OPTIONS", font=("Segoe UI Black", 14), text_color=self.COLORS["accent_cyan"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 15))
        ctk.CTkLabel(f, text="Max connections per server (-x):").grid(row=1, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.connections_var, values=["1", "2", "4", "8", "16", "32", "64"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_cyan"]).grid(row=1, column=1, sticky="w", padx=20)
        ctk.CTkLabel(f, text="Number of file segments (-s):").grid(row=2, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.segments_var, values=["1", "2", "4", "8", "16", "32", "64"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_cyan"]).grid(row=2, column=1, sticky="w", padx=20)
        ctk.CTkLabel(f, text="Chunk size (-k):").grid(row=3, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.chunk_var, values=["1M", "2M", "4M", "8M", "16M", "32M", "64M"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_cyan"]).grid(row=3, column=1, sticky="w", padx=20)

        ctk.CTkLabel(f, text="🛡️ SECURITY & RESUMING (ANTI-DISCONNECT)", font=("Segoe UI Black", 14), text_color=self.COLORS["success"]).grid(row=4, column=0, columnspan=2, sticky="w", pady=(35, 15))
        ctk.CTkCheckBox(f, text="Always append to file and resume session (.aria2)", variable=self.auto_resume_var, fg_color=self.COLORS["success"], hover_color="#2eb810").grid(row=5, column=0, columnspan=2, sticky="w", pady=8)
        ctk.CTkCheckBox(f, text="Auto-retry on network errors and timeouts", variable=self.auto_retry_var, fg_color=self.COLORS["success"], hover_color="#2eb810").grid(row=6, column=0, columnspan=2, sticky="w", pady=8)
        ctk.CTkLabel(f, text="Max retry attempts:").grid(row=7, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.max_tries_var, values=["5", "10", "20", "50", "0 (infinite)"], fg_color=self.COLORS["bg"], border_color=self.COLORS["success"]).grid(row=7, column=1, sticky="w", padx=20)
        ctk.CTkLabel(f, text="Retry wait time (sec.):").grid(row=8, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.retry_wait_var, values=["2", "5", "10", "15", "30"], fg_color=self.COLORS["bg"], border_color=self.COLORS["success"]).grid(row=8, column=1, sticky="w", padx=20)

        ctk.CTkLabel(f, text="🌐 BANDWIDTH LIMITS & MANAGEMENT", font=("Segoe UI Black", 14), text_color=self.COLORS["accent_pink"]).grid(row=9, column=0, columnspan=2, sticky="w", pady=(35, 15))
        ctk.CTkLabel(f, text="Concurrent downloads (-j):").grid(row=10, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.max_concurrent_var, values=["1", "2", "3", "5", "10", "20"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"]).grid(row=10, column=1, sticky="w", padx=20)
        ctk.CTkLabel(f, text="Max Download Limit (e.g. 5M, 0=none):").grid(row=11, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.dl_limit_var, values=["0", "500K", "1M", "2M", "5M", "10M"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"]).grid(row=11, column=1, sticky="w", padx=20)
        ctk.CTkLabel(f, text="Max Upload Limit (Torrent):").grid(row=12, column=0, sticky="w", pady=10)
        ctk.CTkComboBox(f, variable=self.ul_limit_var, values=["0", "100K", "500K", "1M", "5M"], fg_color=self.COLORS["bg"], border_color=self.COLORS["accent_pink"]).grid(row=12, column=1, sticky="w", padx=20)

    def show_context_menu(self, event):
        item = self.queue_tree.identify_row(event.y)
        if item:
            self.queue_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def update_expired_link(self):
        selected = self.queue_tree.selection()
        if not selected: return
        
        item = selected[0]
        vals = self.queue_tree.item(item, "values")
        old_url = vals[1]
        
        if vals[0] == "TORRENT":
            messagebox.showinfo(APP_NAME, "Torrent files resume automatically via trackers. This option is for HTTP/FTP broken links.")
            return

        dialog = ctk.CTkInputDialog(text="Paste new (regenerated) download link:\n\nThe system will use the .aria2 file in the destination folder\nto resume downloading exactly where it left off.", title="Replace Expired URL")
        new_url = dialog.get_input()
        
        if new_url and new_url.strip():
            new_url = new_url.strip()
            if old_url in self.queue_data:
                idx = self.queue_data.index(old_url)
                self.queue_data[idx] = new_url
            
            self.queue_tree.item(item, values=(vals[0], new_url))
            self.log_message(f"[INFO] 🔄 Link replaced successfully. You can resume downloading.")
            messagebox.showinfo(APP_NAME, "Link has been replaced!\n\nClick 'Start Download'. Aria2 will read the resume file (.aria2) and finish the download.")

    def copy_selected_url(self):
        selected = self.queue_tree.selection()
        if selected:
            vals = self.queue_tree.item(selected[0], "values")
            self.clipboard_clear()
            self.clipboard_append(vals[1])
            self.log_message(f"[INFO] Copied to clipboard: {vals[1]}")

    def update_uptime(self):
        if self.running and self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            self.uptime_var.set(f"Session time: {h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self.update_uptime)

    def paste_url(self):
        try: self.input_var.set(self.clipboard_get().strip())
        except tk.TclError: pass

    def add_url_to_queue(self):
        url = self.input_var.get().strip()
        if not url: return
        t = "MAGNET" if url.startswith("magnet:") else "HTTP/FTP"
        self.queue_tree.insert("", "end", values=(t, url))
        self.queue_data.append(url)
        self.input_var.set("")
        self.log_message(f"[+] Added: {url}")

    def add_torrent_to_queue(self):
        paths = filedialog.askopenfilenames(filetypes=[("Torrent Files", "*.torrent"), ("All Files", "*.*")])
        for p in paths:
            self.queue_tree.insert("", "end", values=("TORRENT", p))
            self.queue_data.append(p)
            self.log_message(f"[+] Added Torrent: {p}")

    def remove_selected_from_queue(self, event=None):
        for item in self.queue_tree.selection():
            vals = self.queue_tree.item(item, "values")
            if vals and vals[1] in self.queue_data: 
                self.queue_data.remove(vals[1])
                for arc_item in self.arc_tree.get_children():
                    arc_vals = list(self.arc_tree.item(arc_item, "values"))
                    link_url = next((l["url"] for l in self.archive_links if l["tree_id"] == arc_item), None)
                    if link_url == vals[1] and arc_vals[0] == "[X]":
                        arc_vals[0] = "[ ]"
                        self.arc_tree.item(arc_item, values=arc_vals)
            self.queue_tree.delete(item)

    def clear_queue(self):
        for i in self.queue_tree.get_children(): self.queue_tree.delete(i)
        self.queue_data.clear()
        for arc_item in self.arc_tree.get_children():
            arc_vals = list(self.arc_tree.item(arc_item, "values"))
            if arc_vals[0] == "[X]":
                arc_vals[0] = "[ ]"
                self.arc_tree.item(arc_item, values=arc_vals)
        self.log_message("[!] Queue cleared.")

    def scan_archive(self):
        url = self.input_var.get().strip()
        parsed = urllib.parse.urlparse(url)
        ident = None
        if "archive.org" in parsed.netloc:
            parts = [p for p in parsed.path.split("/") if p]
            if "details" in parts: ident = parts[parts.index("details")+1]
            elif "download" in parts: ident = parts[parts.index("download")+1]
        
        if not ident:
            messagebox.showwarning(APP_NAME, "Enter a valid Archive.org link in the top bar.")
            return

        self.status_var.set("SCANNING ARCHIVE.ORG...")
        threading.Thread(target=self._scan_worker, args=(ident,), daemon=True).start()

    def _scan_worker(self, ident):
        try:
            req = urllib.request.Request(f"https://archive.org/metadata/{ident}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            
            files = [(f.get("name", ""), f.get("size", "0")) for f in data.get("files", []) if f.get("name") and not f.get("name").startswith("__ia_thumb")]
            self.after(0, lambda: self.populate_archive(ident, files))
        except Exception:
            self.after(0, lambda: self.status_var.set("ARCHIVE SCAN ERROR"))

    def populate_archive(self, ident, files):
        for i in self.arc_tree.get_children(): self.arc_tree.delete(i)
        self.archive_links = []
        base = f"https://archive.org/download/{ident}/"
        for name, size in files:
            sz = f"{float(size)/1024/1024:.2f} MB" if size.isdigit() else size
            item = self.arc_tree.insert("", "end", values=("[ ]", name, sz))
            self.archive_links.append({"tree_id": item, "url": base + urllib.parse.quote(name, safe="/")})
        self.status_var.set(f"FOUND {len(files)} FILES")

    def toggle_archive_selected(self, event=None):
        item = self.arc_tree.focus()
        if not item: return
        v = list(self.arc_tree.item(item, "values"))
        is_checked = v[0] == "[X]"
        new_val = "[ ]" if is_checked else "[X]"
        v[0] = new_val
        self.arc_tree.item(item, values=v)

        link_url = next((l["url"] for l in self.archive_links if l["tree_id"] == item), None)
        if link_url:
            if new_val == "[X]" and link_url not in self.queue_data:
                self.queue_tree.insert("", "end", values=("ARCHIVE", link_url))
                self.queue_data.append(link_url)
            elif new_val == "[ ]" and link_url in self.queue_data:
                self.queue_data.remove(link_url)
                for child in self.queue_tree.get_children():
                    if self.queue_tree.item(child, "values")[1] == link_url:
                        self.queue_tree.delete(child)

    def set_all_archive(self, state):
        chk = "[X]" if state else "[ ]"
        for i in self.arc_tree.get_children():
            v = list(self.arc_tree.item(i, "values"))
            if v[0] != chk:
                v[0] = chk
                self.arc_tree.item(i, values=v)
                
                link_url = next((l["url"] for l in self.archive_links if l["tree_id"] == i), None)
                if link_url:
                    if state and link_url not in self.queue_data:
                        self.queue_tree.insert("", "end", values=("ARCHIVE", link_url))
                        self.queue_data.append(link_url)
                    elif not state and link_url in self.queue_data:
                        self.queue_data.remove(link_url)
                        for child in self.queue_tree.get_children():
                            if self.queue_tree.item(child, "values")[1] == link_url:
                                self.queue_tree.delete(child)

    def find_aria2(self):
        cands = [shutil.which("aria2c"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2c.exe"), "aria2c.exe"]
        for p in cands:
            if p and os.path.isfile(p):
                self.aria_path = p
                self.aria_var.set(f"🟢 Engine: Active")
                return
        self.aria_path = None
        self.aria_var.set("🔴 ERROR: aria2c.exe missing!")

    def start_download(self):
        if self.running: return messagebox.showinfo(APP_NAME, "Tasks are already running!")
        if not self.aria_path: return messagebox.showerror(APP_NAME, "Aria2c.exe engine missing.")
        if not self.queue_data: return messagebox.showwarning(APP_NAME, "Queue is empty!")

        folder = self.save_var.get().strip()
        os.makedirs(folder, exist_ok=True)
        self.save_config()

        self.running = True
        self.paused = False
        self.session_start_time = time.time()
        self.status_var.set("DOWNLOAD IN PROGRESS...")
        self.title(f"{APP_NAME} - Downloading...")
        self.tabview.set(" 📜 TERMINAL ")

        threading.Thread(target=self._download_worker, args=(folder,), daemon=True).start()

    def _download_worker(self, folder):
        cmd = [
            self.aria_path,
            "--dir", folder,
            "-x", self.connections_var.get(),
            "-s", self.segments_var.get(),
            "-k", self.chunk_var.get(),
            "-j", self.max_concurrent_var.get(),
            f"--max-overall-download-limit={self.dl_limit_var.get()}",
            f"--max-overall-upload-limit={self.ul_limit_var.get()}",
            "--bt-save-metadata=true", 
            "--seed-time=0",
            "--console-log-level=notice", 
            "--summary-interval=1",
            "--timeout=30",
            "--connect-timeout=15"
        ]

        if self.auto_resume_var.get():
            cmd.append("--continue=true")
            cmd.append("--always-resume=true")
            cmd.append("--auto-file-renaming=false")

        if self.auto_retry_var.get():
            tries = self.max_tries_var.get().split()[0]
            cmd.append(f"--max-tries={tries if tries.isdigit() else '0'}")
            cmd.append(f"--retry-wait={self.retry_wait_var.get()}")

        cmd.extend(self.queue_data)
        
        self.log_message(f"[{time.strftime('%H:%M:%S')}] 🔥 ARIA2 ENGINE START (Safeguards enabled)")
        
        try:
            cflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=cflags
            )

            for line in iter(self.process.stdout.readline, ""):
                if not line: break
                line = line.rstrip()
                if line:
                    self.log_message(line)
                    self.parse_aria_line(line)

            rc = self.process.wait()
            msg = "COMPLETED SUCCESSFULLY" if rc == 0 else ("PAUSED (STATE SAVED)" if self.paused else f"FINISHED WITH CODE {rc}")
            self.after(0, lambda r=rc, m=msg: self.finish_download(r == 0, m))

        except Exception as e:
            self.log_message(f"[FATAL ERROR] {e}")
            self.after(0, lambda: self.finish_download(False, "Critical process error"))
        finally:
            self.process = None

    def parse_aria_line(self, line):
        m_full = re.search(r"(?:\[#\w+\s+)?(?P<done>[0-9KMGTPEZYbBi\.]+)/(?P<total>[0-9KMGTPEZYbBi\.]+)\((?P<pct>\d+)%\).*?DL:(?P<speed>[0-9KMGTPEZYbBi\.]+)(?:.*?ETA:(?P<eta>[0-9a-z]+))?", line)
        if m_full:
            p = int(m_full.group("pct"))
            d, t, s = m_full.group("done"), m_full.group("total"), m_full.group("speed")
            e = m_full.group("eta") if m_full.group("eta") else "--:--"
            ul_match = re.search(r"UL:([0-9KMGTPEZYbBi\.]+)", line)
            ul = ul_match.group(1) if ul_match else "0 B"
            self.after(0, lambda pct=p, done=d, total=t, speed=s, ul=ul, eta=e: self.update_progress_values(pct, done, total, speed, ul, eta))
            return
            
        m_part = re.search(r"(?:\[#\w+\s+)?(?P<done>[0-9KMGTPEZYbBi\.]+).*?DL:(?P<speed>[0-9KMGTPEZYbBi\.]+)", line)
        if m_part:
            self.after(0, lambda d=m_part.group("done"), s=m_part.group("speed"): self.update_progress_values(0, d, "?", s, "0 B", "Calculating..."))

    def update_progress_values(self, pct, done, total, speed, upload, eta):
        self.progress.set(pct / 100.0)
        self.size_var.set(f"Size: {done} / {total} ({pct}%)")
        self.speed_var.set(f"DL: ▼ {speed}/s  |  UL: ▲ {upload}/s")
        self.eta_var.set(f"ETA: {eta}")
        self.title(f"{APP_NAME} - {pct}% | ▼ {speed}/s")

    def finish_download(self, success, msg):
        self.running = False
        self.paused = False
        self.session_start_time = None
        self.status_var.set(msg)
        self.speed_var.set("DL: 0 B/s | UL: 0 B/s")
        self.title(APP_NAME)
        if success:
            self.progress.set(1.0)
            self.eta_var.set("ETA: FINISHED")
        self.log_message(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f: cfg = json.load(f)
                self.save_var.set(cfg.get("save_folder", self.save_var.get()))
                self.connections_var.set(str(cfg.get("connections", "16")))
                self.segments_var.set(str(cfg.get("segments", "16")))
                self.chunk_var.set(cfg.get("chunk", "4M"))
                self.max_concurrent_var.set(str(cfg.get("max_concurrent", "5")))
                self.dl_limit_var.set(cfg.get("dl_limit", "0"))
                self.ul_limit_var.set(cfg.get("ul_limit", "1M"))
                self.auto_resume_var.set(bool(cfg.get("auto_resume", True)))
                self.auto_retry_var.set(bool(cfg.get("auto_retry", True)))
                self.max_tries_var.set(str(cfg.get("max_tries", "50")))
                self.retry_wait_var.set(str(cfg.get("retry_wait", "5")))
        except: pass

    def save_config(self):
        try:
            cfg = {
                "save_folder": self.save_var.get(), "connections": self.connections_var.get(),
                "segments": self.segments_var.get(), "chunk": self.chunk_var.get(),
                "max_concurrent": self.max_concurrent_var.get(),
                "dl_limit": self.dl_limit_var.get(), "ul_limit": self.ul_limit_var.get(),
                "auto_resume": self.auto_resume_var.get(), "auto_retry": self.auto_retry_var.get(),
                "max_tries": self.max_tries_var.get(), "retry_wait": self.retry_wait_var.get()
            }
            with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)
        except: pass

    def choose_folder(self):
        f = filedialog.askdirectory(initialdir=self.save_var.get())
        if f: self.save_var.set(f)

    def open_folder(self):
        f = self.save_var.get()
        if os.path.isdir(f): os.startfile(f)

    def log_message(self, text):
        self.log_queue.put(("log", str(text)))

    def process_log_queue(self):
        try:
            while True:
                kind, val = self.log_queue.get_nowait()
                if kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", val + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
        except queue.Empty: pass
        self.after(50, self.process_log_queue)

    def pause_download(self):
        if not self.process: return
        try:
            if os.name == "nt": self.process.send_signal(subprocess.signal.CTRL_BREAK_EVENT)
            else: self.process.terminate()
            self.paused = True
            self.status_var.set("PAUSED")
            self.log_message("[PAUSE] Progress flushed to disk (.aria2).")
        except Exception as e: self.log_message(f"Pause error: {e}")

    def stop_download(self):
        if not self.process: return
        try: self.process.kill()
        except: pass
        self.running = False
        self.status_var.set("STOPPED")
        self.log_message("[STOP] Engine terminated.")

    def on_close(self):
        self.save_config()
        if self.process and self.process.poll() is None:
            if messagebox.askyesno("Exit", "Download in progress. Interrupt and exit? (State will be saved)"):
                try: self.process.kill()
                except: pass
            else: return
        self.destroy()

if __name__ == "__main__":
    app = Aria2Downloader()
    app.mainloop()