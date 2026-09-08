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
from aria2_velocity_ui import VelocityUI

APP_NAME = "Aria2 Ultimate PRO by Swir"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria2_gui_config.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class Aria2Downloader(VelocityUI, ctk.CTk):
    UI_LANGUAGE = 'pl'

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1200x880")
        self.minsize(1050, 800)
        
        # Paleta "Cyber Neon"
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
        
        # Zabezpieczenia i wznawianie
        self.auto_resume_var = ctk.BooleanVar(value=True)
        self.auto_retry_var = ctk.BooleanVar(value=True)
        self.max_tries_var = ctk.StringVar(value="50")
        self.retry_wait_var = ctk.StringVar(value="5")
        
        self.status_var = ctk.StringVar(value="SYSTEM GOTOWY")
        self.speed_var = ctk.StringVar(value="DL: 0 B/s | UL: 0 B/s")
        self.size_var = ctk.StringVar(value="Rozmiar: -- / --")
        self.eta_var = ctk.StringVar(value="ETA: --:--:--")
        self.aria_var = ctk.StringVar(value="Inicjalizacja...")
        self.uptime_var = ctk.StringVar(value="Czas sesji: 00:00:00")

        self.load_config()
        self.setup_ttk_styles_for_treeview()
        self.build_ui()
        self.find_aria2()
        
        self.after(50, self.process_log_queue)
        self.after(1000, self.update_uptime)
        self.protocol("WM_DELETE_WINDOW", self.on_close)







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
            messagebox.showinfo(APP_NAME, "Pliki Torrent wznawiają się automatycznie za pomocą trackerów. Ta opcja służy do odnawiania zerwanych adresów HTTP/FTP.")
            return

        dialog = ctk.CTkInputDialog(text="Wklej nowy (wygenerowany na nowo) link pobierania:\n\nSystem użyje pliku .aria2 w folderze docelowym,\naby wznowić pobieranie dokładnie od momentu przerwania.", title="Podmiana wygasłego adresu URL")
        new_url = dialog.get_input()
        
        if new_url and new_url.strip():
            new_url = new_url.strip()
            if old_url in self.queue_data:
                idx = self.queue_data.index(old_url)
                self.queue_data[idx] = new_url
            
            self.queue_tree.item(item, values=(vals[0], new_url))
            self.log_message(f"[INFO] 🔄 Link podmieniony pomyślnie. Możesz wznowić pobieranie.")
            messagebox.showinfo(APP_NAME, "Link został podmieniony!\n\nKliknij 'Rozpocznij Pobieranie'. Aria2 odczyta plik wznawiania (.aria2) z dysku i dokończy pobieranie.")

    def copy_selected_url(self):
        selected = self.queue_tree.selection()
        if selected:
            vals = self.queue_tree.item(selected[0], "values")
            self.clipboard_clear()
            self.clipboard_append(vals[1])
            self.log_message(f"[INFO] Skopiowano do schowka: {vals[1]}")

    def update_uptime(self):
        if self.running and self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            self.uptime_var.set(f"Czas sesji: {h:02d}:{m:02d}:{s:02d}")
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
        self.log_message(f"[+] Dodano: {url}")

    def add_torrent_to_queue(self):
        paths = filedialog.askopenfilenames(filetypes=[("Pliki Torrent", "*.torrent"), ("Wszystkie pliki", "*.*")])
        for p in paths:
            self.queue_tree.insert("", "end", values=("TORRENT", p))
            self.queue_data.append(p)
            self.log_message(f"[+] Dodano Torrent: {p}")

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
        self.log_message("[!] Kolejka wyczyszczona.")

    def scan_archive(self):
        url = self.input_var.get().strip()
        parsed = urllib.parse.urlparse(url)
        ident = None
        if "archive.org" in parsed.netloc:
            parts = [p for p in parsed.path.split("/") if p]
            if "details" in parts: ident = parts[parts.index("details")+1]
            elif "download" in parts: ident = parts[parts.index("download")+1]
        
        if not ident:
            messagebox.showwarning(APP_NAME, "Wprowadź prawidłowy link do Archive.org w górnym pasku.")
            return

        self.status_var.set("SKANOWANIE ARCHIVE.ORG...")
        threading.Thread(target=self._scan_worker, args=(ident,), daemon=True).start()

    def _scan_worker(self, ident):
        try:
            req = urllib.request.Request(f"https://archive.org/metadata/{ident}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            
            files = [(f.get("name", ""), f.get("size", "0")) for f in data.get("files", []) if f.get("name") and not f.get("name").startswith("__ia_thumb")]
            self.after(0, lambda: self.populate_archive(ident, files))
        except Exception:
            self.after(0, lambda: self.status_var.set("BŁĄD SKANOWANIA ARCHIVE"))

    def populate_archive(self, ident, files):
        for i in self.arc_tree.get_children(): self.arc_tree.delete(i)
        self.archive_links = []
        base = f"https://archive.org/download/{ident}/"
        for name, size in files:
            sz = f"{float(size)/1024/1024:.2f} MB" if size.isdigit() else size
            item = self.arc_tree.insert("", "end", values=("[ ]", name, sz))
            self.archive_links.append({"tree_id": item, "url": base + urllib.parse.quote(name, safe="/")})
        self.status_var.set(f"ZNALEZIONO {len(files)} PLIKÓW")

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
                self.aria_var.set(f"🟢 Silnik: Aktywny")
                return
        self.aria_path = None
        self.aria_var.set("🔴 BŁĄD: Brak aria2c.exe!")

    def start_download(self):
        if self.running: return messagebox.showinfo(APP_NAME, "Zadania już działają!")
        if not self.aria_path: return messagebox.showerror(APP_NAME, "Brak silnika aria2c.exe.")
        if not self.queue_data: return messagebox.showwarning(APP_NAME, "Kolejka jest pusta!")

        folder = self.save_var.get().strip()
        os.makedirs(folder, exist_ok=True)
        self.save_config()

        self.running = True
        self.paused = False
        self.session_start_time = time.time()
        self.status_var.set("POBIERANIE W TOKU...")
        self.title(f"{APP_NAME} - Pobieranie...")
        self.show_page("queue")

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
        
        self.log_message(f"[{time.strftime('%H:%M:%S')}] 🔥 START SILNIKA ARIA2 (Zabezpieczenia włączone)")
        
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
            msg = "ZAKOŃCZONO SUKCESEM" if rc == 0 else ("WSTRZYMANO (ZAPISANO STAN)" if self.paused else f"ZAKOŃCZONO Z KODEM {rc}")
            self.after(0, lambda r=rc, m=msg: self.finish_download(r == 0, m))

        except Exception as e:
            self.log_message(f"[FATAL ERROR] {e}")
            self.after(0, lambda: self.finish_download(False, "Błąd krytyczny procesu"))
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
            self.after(0, lambda d=m_part.group("done"), s=m_part.group("speed"): self.update_progress_values(0, d, "?", s, "0 B", "Obliczanie..."))

    def update_progress_values(self, pct, done, total, speed, upload, eta):
        self.progress.set(pct / 100.0)
        self.size_var.set(f"Rozmiar: {done} / {total} ({pct}%)")
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
            self.eta_var.set("ETA: ZAKOŃCZONO")
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
            self.status_var.set("WSTRZYMANO")
            self.log_message("[PAUZA] Postęp zrzucony na dysk (.aria2).")
        except Exception as e: self.log_message(f"Błąd pauzy: {e}")

    def stop_download(self):
        if not self.process: return
        try: self.process.kill()
        except: pass
        self.running = False
        self.status_var.set("ZATRZYMANO")
        self.log_message("[STOP] Silnik przerwany.")

    def on_close(self):
        self.save_config()
        if self.process and self.process.poll() is None:
            if messagebox.askyesno("Wyjście", "Pobieranie trwa. Przerwać i wyjść? (Stan zostanie zapisany)"):
                try: self.process.kill()
                except: pass
            else: return
        self.destroy()

if __name__ == "__main__":
    app = Aria2Downloader()
    app.mainloop()
