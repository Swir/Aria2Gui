"""Shared, bilingual presentation layer for the existing aria2 CLI frontends."""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class VelocityUI:
    """Keep queue values and engine callbacks compatible with both launchers."""

    def tr(self, pl, en):
        return pl if self.UI_LANGUAGE == "pl" else en

    def setup_ttk_styles_for_treeview(self):
        self.COLORS.update({
            "bg": "#0B111B", "panel": "#131D2B", "accent_cyan": "#38D9E6",
            "accent_pink": "#DFA0C7", "success": "#78DAB0",
            "text_main": "#EDF2FA", "text_muted": "#A1B1C8",
            "border": "#2A3A50", "hover": "#21344A",
        })
        self.configure(fg_color=self.COLORS["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")
        scale = self._get_window_scaling()
        style.configure("Velocity.Treeview", background=self.COLORS["panel"],
                        fieldbackground=self.COLORS["panel"], foreground=self.COLORS["text_main"],
                        rowheight=round(44 * scale), borderwidth=0, relief="flat", font=("Segoe UI", 11))
        style.map("Velocity.Treeview", background=[("selected", "#204657")],
                  foreground=[("selected", "#EFFFFF")])
        style.configure("Velocity.Treeview.Heading", background="#172538", foreground="#B6C7DF",
                        font=("Segoe UI", 10, "bold"), padding=10, relief="flat")
        style.map("Velocity.Treeview.Heading", background=[("active", "#21344A")])

    def button(self, parent, text, command, primary=False, danger=False, **kwargs):
        return ctk.CTkButton(
            parent, text=text, command=command, height=36, corner_radius=8,
            fg_color=self.COLORS["accent_cyan"] if primary else ("#361F30" if danger else "#1A2B40"),
            hover_color="#70EAF2" if primary else ("#552E44" if danger else "#29415D"),
            text_color="#06212B" if primary else ("#FFBED2" if danger else self.COLORS["text_main"]),
            font=("Segoe UI", 12, "bold" if primary else "normal"), **kwargs)

    def build_ui(self):
        self.geometry("1180x780")
        self.minsize(1000, 700)
        self._velocity_job = None
        self._last_queue_count = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="#101A29", corner_radius=0, height=90)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=24, pady=16)
        ctk.CTkLabel(brand, text="ARIA2", text_color=self.COLORS["accent_cyan"],
                     font=("Segoe UI", 26, "bold")).pack(side="left")
        ctk.CTkLabel(brand, text=" / VELOCITY", text_color="#D0DEEF",
                     font=("Segoe UI", 15)).pack(side="left", padx=(6, 0), pady=(7, 0))
        ctk.CTkLabel(header, text=self.tr("Twoje pliki. W dobrym tempie.", "Your files. At a better pace."),
                     text_color=self.COLORS["text_muted"], font=("Segoe UI", 12)).grid(row=0, column=1, sticky="w", padx=26)
        ctk.CTkLabel(header, textvariable=self.aria_var, text_color=self.COLORS["text_muted"],
                     font=("Segoe UI", 11)).grid(row=0, column=2, sticky="e", padx=24)

        sidebar = ctk.CTkFrame(self, width=178, fg_color="#0E1725", corner_radius=0)
        sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(6, weight=1)
        ctk.CTkLabel(sidebar, text="WORKSPACE", text_color="#8295B0", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=19, pady=(24, 12))
        self.nav_buttons = {}
        for i, (key, label) in enumerate([
            ("queue", self.tr("Transfery", "Transfers")),
            ("archive", "Archive.org"), ("logs", self.tr("Dziennik silnika", "Engine log")),
            ("settings", self.tr("Ustawienia", "Settings")),
        ], 1):
            b = self.button(sidebar, label, lambda k=key: self.show_page(k), width=150)
            b.grid(row=i, column=0, sticky="ew", padx=12, pady=5)
            self.nav_buttons[key] = b
        ctk.CTkLabel(sidebar, text="ULTIMATE PRO\nby Swir", justify="left", text_color="#8295B0",
                     font=("Segoe UI", 11)).grid(row=7, column=0, sticky="sw", padx=20, pady=22)

        self.page_host = ctk.CTkFrame(self, fg_color="transparent")
        self.page_host.grid(row=1, column=1, sticky="nsew", padx=22, pady=(20, 10))
        self.page_host.grid_rowconfigure(0, weight=1)
        self.page_host.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for key in ("queue", "logs", "archive", "settings"):
            page = ctk.CTkFrame(self.page_host, fg_color="transparent")
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page
        self.tab_queue, self.tab_logs = self.pages["queue"], self.pages["logs"]
        self.tab_archive, self.tab_settings = self.pages["archive"], self.pages["settings"]
        self.build_queue_tab()
        self.build_logs_tab()
        self.build_archive_tab()
        self.build_settings_tab()
        self.build_transport()
        self.show_page("queue")
        self.refresh_velocity_ui()

    def show_page(self, key):
        self.pages[key].tkraise()
        for name, button in self.nav_buttons.items():
            button.configure(fg_color="#1B3446" if name == key else "transparent",
                             text_color=self.COLORS["accent_cyan"] if name == key else "#B5C5DA")

    def title_block(self, parent, title, subtitle):
        titlebox = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(titlebox, text=title, text_color=self.COLORS["text_main"], font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ctk.CTkLabel(titlebox, text=subtitle, text_color=self.COLORS["text_muted"], font=("Segoe UI", 11)).pack(anchor="w", pady=(1, 10))
        return titlebox

    def make_tree(self, parent, columns):
        host = ctk.CTkFrame(parent, fg_color=self.COLORS["panel"], corner_radius=10,
                            border_width=1, border_color=self.COLORS["border"])
        host.grid_columnconfigure(0, weight=1)
        host.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(host, columns=columns, show="headings", selectmode="extended", style="Velocity.Treeview")
        tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        vs = ctk.CTkScrollbar(host, command=tree.yview, button_color="#3A4D65", button_hover_color="#577493")
        vs.grid(row=0, column=1, sticky="ns", pady=8, padx=(0, 4))
        hs = ctk.CTkScrollbar(host, orientation="horizontal", command=tree.xview,
                             button_color="#3A4D65", button_hover_color="#577493")
        hs.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        return host, tree

    def build_queue_tab(self):
        p = self.tab_queue
        p.grid_columnconfigure(0, weight=1)
        p.grid_rowconfigure(4, weight=1)
        self.title_block(p, self.tr("Twoje transfery", "Your transfers"),
                         self.tr("Dodaj pliki do kolejki, potem rozpocznij pobieranie.", "Add files to the queue, then start downloading.")).grid(row=0, column=0, sticky="ew")
        add = ctk.CTkFrame(p, fg_color="transparent")
        add.grid(row=1, column=0, sticky="ew", pady=(3, 12))
        add.grid_columnconfigure(0, weight=1)
        self.input_entry = ctk.CTkEntry(add, textvariable=self.input_var, height=40,
            placeholder_text=self.tr("Wklej URL, magnet lub metalink…", "Paste a URL, magnet or metalink…"),
            fg_color="#111D2D", border_color="#344C67", font=("Segoe UI", 12))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.input_entry.bind("<Return>", lambda _e: self.add_url_to_queue())
        self.button(add, self.tr("Wklej", "Paste"), self.paste_url, width=66).grid(row=0, column=1, padx=(0, 8))
        self.button(add, self.tr("Dodaj", "Add"), self.add_url_to_queue, primary=True, width=76).grid(row=0, column=2, padx=(0, 8))
        self.button(add, ".torrent", self.add_torrent_to_queue, width=82).grid(row=0, column=3)
        folder = ctk.CTkFrame(p, fg_color="transparent")
        folder.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        folder.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(folder, text=self.tr("Zapisz do", "Save to"), text_color=self.COLORS["text_muted"], font=("Segoe UI", 11)).grid(row=0, column=0, padx=(0, 10))
        ctk.CTkEntry(folder, textvariable=self.save_var, fg_color=self.COLORS["bg"], border_color=self.COLORS["border"],
                     font=("Segoe UI", 11)).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.button(folder, self.tr("Zmień", "Change"), self.choose_folder, width=72).grid(row=0, column=2, padx=(0, 8))
        self.button(folder, self.tr("Otwórz", "Open"), self.open_folder, width=72).grid(row=0, column=3)
        bar = ctk.CTkFrame(p, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.queue_count_label = ctk.CTkLabel(bar, text="", text_color="#D2DEED", font=("Segoe UI", 12, "bold"))
        self.queue_count_label.pack(side="left")
        self.selection_buttons = []
        for text, command in [(self.tr("Usuń", "Remove"), self.remove_selected_from_queue),
                              (self.tr("Podmień link", "Replace URL"), self.update_expired_link),
                              (self.tr("Kopiuj URL", "Copy URL"), self.copy_selected_url)]:
            b = self.button(bar, text, command, width=90)
            b.pack(side="right", padx=(6, 0))
            self.selection_buttons.append(b)
        host, self.queue_tree = self.make_tree(p, ("type", "source"))
        host.grid(row=4, column=0, sticky="nsew")
        self.queue_tree.heading("type", text=self.tr("TYP", "TYPE"))
        self.queue_tree.heading("source", text=self.tr("PLIK / ADRES", "FILE / URL"))
        self.queue_tree.column("type", width=90, minwidth=75, stretch=False, anchor="center")
        self.queue_tree.column("source", width=560, minwidth=350)
        self.queue_empty = ctk.CTkLabel(host, text=self.tr("Kolejka jest pusta\nDodaj pierwszy link lub plik .torrent.",
            "Your queue is empty\nAdd your first link or .torrent file."), text_color="#B4C6DD", fg_color=self.COLORS["panel"], font=("Segoe UI", 14), justify="center")
        self.queue_tree.bind("<Delete>", self.remove_selected_from_queue)
        self.context_menu = tk.Menu(self, tearoff=False, bg="#18283B", fg="#EDF2FA", activebackground="#24536A",
                                    activeforeground="#FFFFFF", borderwidth=0)
        for text, command in [(self.tr("Podmień wygasły link", "Replace expired URL"), self.update_expired_link),
                              (self.tr("Kopiuj URL", "Copy URL"), self.copy_selected_url),
                              (self.tr("Usuń z kolejki", "Remove from queue"), self.remove_selected_from_queue)]:
            self.context_menu.add_command(label=text, command=command)
        self.queue_tree.bind("<Button-3>", self.show_context_menu)
        end = ctk.CTkFrame(p, fg_color="transparent")
        end.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkLabel(end, text=self.tr("HTTP · HTTPS · FTP · SFTP · Magnet · Metalink", "HTTP · HTTPS · FTP · SFTP · Magnet · Metalink"),
                     text_color=self.COLORS["text_muted"], font=("Segoe UI", 10)).pack(side="left")
        self.button(end, self.tr("Wyczyść kolejkę", "Clear queue"), self.clear_queue, danger=True, width=130).pack(side="right")

    def build_logs_tab(self):
        p = self.tab_logs
        self.title_block(p, self.tr("Dziennik silnika", "Engine log"),
                         self.tr("Pełne komunikaty aria2, wyniki i błędy.", "Full aria2 output, results and errors.")).pack(fill="x")
        self.log = ctk.CTkTextbox(p, fg_color="#0D1724", border_color=self.COLORS["border"], border_width=1,
                                 text_color="#BBCDE3", font=("Consolas", 12), corner_radius=10)
        self.log.pack(fill="both", expand=True, pady=(6, 0))
        self.log.configure(state="disabled")

    def build_archive_tab(self):
        p = self.tab_archive
        p.grid_columnconfigure(0, weight=1)
        p.grid_rowconfigure(2, weight=1)
        self.title_block(p, "Archive.org", self.tr("Wybierz pliki z kolekcji i dodaj je do kolejki.",
                         "Choose collection files and add them to the queue.")).grid(row=0, column=0, sticky="ew")
        header = ctk.CTkFrame(p, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", pady=(3, 14))
        header.grid_columnconfigure(0, weight=1)
        self.archive_input_var = ctk.StringVar()
        archive_input = ctk.CTkEntry(header, textvariable=self.archive_input_var,
            placeholder_text="https://archive.org/details/…", height=40, fg_color="#111D2D", border_color="#344C67")
        archive_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        archive_input.bind("<Return>", lambda _e: self.scan_archive_from_page())
        self.button(header, self.tr("Skanuj", "Scan"), self.scan_archive_from_page, primary=True, width=100).grid(row=0, column=1)
        host, self.arc_tree = self.make_tree(p, ("select", "name", "size"))
        host.grid(row=2, column=0, sticky="nsew")
        for key, title, width, anchor in [("select", self.tr("WYBÓR", "SELECT"), 70, "center"),
            ("name", self.tr("NAZWA PLIKU", "FILE NAME"), 470, "w"), ("size", self.tr("ROZMIAR", "SIZE"), 110, "e")]:
            self.arc_tree.heading(key, text=title)
            self.arc_tree.column(key, width=width, minwidth=width if key != "name" else 250, anchor=anchor, stretch=key == "name")
        self.arc_tree.bind("<Double-1>", self.toggle_archive_selected)
        self.arc_tree.bind("<space>", self.toggle_archive_selected)
        ctrl = ctk.CTkFrame(p, fg_color="transparent")
        ctrl.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.button(ctrl, self.tr("Zaznacz wszystko", "Select all"), lambda: self.set_all_archive(True), width=130).pack(side="left", padx=(0, 8))
        self.button(ctrl, self.tr("Odznacz wszystko", "Deselect all"), lambda: self.set_all_archive(False), width=130).pack(side="left")
        self.button(ctrl, self.tr("Przejdź do kolejki", "Open queue"), lambda: self.show_page("queue"), width=145).pack(side="right")
        ctk.CTkLabel(p, text=self.tr("Dwuklik lub spacja przełącza wybór. Zaznaczone pliki trafiają do kolejki.",
                     "Double-click or Space toggles a file. Selected files are added to the queue."),
                     text_color=self.COLORS["text_muted"], font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", pady=(8, 0))

    def scan_archive_from_page(self):
        # The existing scanner reads input_var. Restore the transfer draft afterwards.
        previous = self.input_var.get()
        try:
            self.input_var.set(self.archive_input_var.get())
            self.scan_archive()
        finally:
            self.input_var.set(previous)

    def build_settings_tab(self):
        self.title_block(self.tab_settings, self.tr("Ustawienia pobierania", "Download settings"),
                         self.tr("Parametry stosowane przy kolejnym uruchomieniu silnika.",
                                 "These options apply the next time the engine starts.")).pack(fill="x")
        f = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        f.pack(fill="both", expand=True)
        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=0)
        row = 0
        sections = [
            (self.tr("Połączenia", "Connections"), [
                (self.tr("Połączenia na serwer", "Connections per server"), self.connections_var, ["1", "2", "4", "8", "16", "32", "64"]),
                (self.tr("Segmenty pliku", "File segments"), self.segments_var, ["1", "2", "4", "8", "16", "32", "64"]),
                (self.tr("Rozmiar segmentu", "Segment size"), self.chunk_var, ["1M", "2M", "4M", "8M", "16M", "32M", "64M"]),
                (self.tr("Równoczesne pobierania", "Concurrent downloads"), self.max_concurrent_var, ["1", "2", "3", "5", "10", "20"]),
            ]),
            (self.tr("Limity prędkości", "Speed limits"), [
                (self.tr("Pobieranie · 0 = bez limitu", "Download · 0 = unlimited"), self.dl_limit_var, ["0", "500K", "1M", "2M", "5M", "10M"]),
                (self.tr("Wysyłanie · 0 = bez limitu", "Upload · 0 = unlimited"), self.ul_limit_var, ["0", "100K", "500K", "1M", "5M"]),
            ]),
            (self.tr("Ponawianie", "Retries"), [
                (self.tr("Liczba prób · 0 = bez limitu", "Attempts · 0 = unlimited"), self.max_tries_var, ["5", "10", "20", "50", "0"]),
                (self.tr("Odstęp między próbami (sekundy)", "Delay between retries (seconds)"), self.retry_wait_var, ["2", "5", "10", "15", "30"]),
            ]),
        ]
        for title, fields in sections:
            ctk.CTkLabel(f, text=title, text_color=self.COLORS["accent_cyan"], font=("Segoe UI", 14, "bold")).grid(row=row, column=0, sticky="w", pady=(18, 8))
            row += 1
            for label, var, values in fields:
                ctk.CTkLabel(f, text=label, text_color="#C4D0E2", font=("Segoe UI", 12)).grid(row=row, column=0, sticky="w", pady=7)
                ctk.CTkComboBox(f, variable=var, values=values, width=170, fg_color="#111D2D",
                    border_color="#344C67", button_color="#263F58", button_hover_color="#355B7B").grid(row=row, column=1, padx=(18, 14), pady=7, sticky="e")
                row += 1
        for label, var in [(self.tr("Wznawiaj nieukończone pliki (.aria2)", "Resume unfinished files (.aria2)"), self.auto_resume_var),
                           (self.tr("Ponawiaj po błędzie lub przekroczeniu czasu", "Retry after errors or timeouts"), self.auto_retry_var)]:
            ctk.CTkCheckBox(f, text=label, variable=var, fg_color="#208D9A", hover_color="#2BACB9",
                            text_color="#D5E1F1", font=("Segoe UI", 12)).grid(row=row, column=0, columnspan=2, sticky="w", pady=12)
            row += 1
        actions = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        self.button(actions, self.tr("Zapisz ustawienia", "Save settings"), self.save_config, primary=True, width=160).pack(side="left")

    def build_transport(self):
        panel = ctk.CTkFrame(self, fg_color="#131E2D", corner_radius=12, border_width=1, border_color="#2A3A50")
        panel.grid(row=2, column=1, sticky="ew", padx=22, pady=(0, 18))
        panel.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 0))
        ctk.CTkLabel(top, textvariable=self.status_var, text_color="#C6D9EB", font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkLabel(top, textvariable=self.speed_var, text_color=self.COLORS["accent_cyan"], font=("Consolas", 11)).pack(side="right")
        self.progress = ctk.CTkProgressBar(panel, height=5, progress_color=self.COLORS["accent_cyan"], fg_color="#2A384C")
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", padx=16, pady=7)
        stats = ctk.CTkFrame(panel, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=16)
        ctk.CTkLabel(stats, textvariable=self.size_var, text_color=self.COLORS["text_muted"], font=("Segoe UI", 10)).pack(side="left")
        ctk.CTkLabel(stats, textvariable=self.eta_var, text_color=self.COLORS["text_muted"], font=("Segoe UI", 10)).pack(side="right")
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.grid(row=3, column=0, sticky="ew", padx=16, pady=(6, 12))
        self.start_button = self.button(controls, self.tr("Rozpocznij pobieranie", "Start downloads"), self.start_download, primary=True, width=185)
        self.start_button.pack(side="left", padx=(0, 8))
        self.pause_button = self.button(controls, self.tr("Pauza", "Pause"), self.pause_download, width=78)
        self.pause_button.pack(side="left", padx=(0, 8))
        self.stop_button = self.button(controls, "Stop", self.stop_download, danger=True, width=78)
        self.stop_button.pack(side="left")
        ctk.CTkLabel(controls, textvariable=self.uptime_var, text_color=self.COLORS["text_muted"], font=("Segoe UI", 10)).pack(side="right")

    def refresh_velocity_ui(self):
        count = len(self.queue_data)
        if count != self._last_queue_count:
            self.queue_count_label.configure(text=self.tr(f"KOLEJKA · {count}", f"QUEUE · {count}"))
            if count:
                self.queue_empty.place_forget()
            else:
                self.queue_empty.place(relx=.5, rely=.5, anchor="center")
            self._last_queue_count = count
        self.start_button.configure(state="disabled" if self.running else "normal")
        process_active = self.process is not None and self.running
        self.pause_button.configure(state="normal" if process_active else "disabled")
        self.stop_button.configure(state="normal" if process_active else "disabled")
        selected = bool(self.queue_tree.selection())
        for button in self.selection_buttons:
            button.configure(state="normal" if selected else "disabled")
        self._velocity_job = self.after(250, self.refresh_velocity_ui)
