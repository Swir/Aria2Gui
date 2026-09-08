<div align="center">

# 🚀 ARIA2 Ultimate PRO

### Modern Cyber-Neon GUI for aria2c on Windows

**HTTP • HTTPS • FTP • SFTP • Torrents • Magnet Links • Metalink • Archive.org**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![aria2](https://img.shields.io/badge/Engine-aria2c-00b894)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-8A2BE2)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Languages](https://img.shields.io/badge/Languages-EN%20%7C%20PL-ff4fa3)

</div>

---

## ⚡ About

**ARIA2 Ultimate PRO** is a modern desktop download manager built in Python around the powerful `aria2c` engine. It gives Windows users a graphical interface for fast multi-connection downloads, torrents, magnet links, Metalink files and resumable transfer workflows.

The project is designed for people searching for an **aria2 GUI**, **aria2c frontend**, **Windows download manager**, **Python download manager**, **torrent downloader**, **magnet link downloader** or a modern graphical alternative to running aria2 from the command line.

Two complete application variants are included: **English** and **Polish**.

---

## ✨ Features

| Feature | Description |
|---|---|
| ⚡ aria2c engine | Uses the high-performance aria2 download backend |
| 🌐 Multiple protocols | HTTP, HTTPS, FTP and SFTP |
| 🧲 Magnet links | Open and download magnet links |
| 🌊 Torrent support | Work with `.torrent` files |
| 📦 Metalink | Supports Metalink download sources |
| 🔁 Resume | Continue interrupted downloads using aria2 session data |
| 🧵 Multi-connection | Configure connections, segments and chunk sizes |
| 🚦 Bandwidth controls | Set transfer limits and connection parameters |
| 🔄 Retry logic | Automatic retry and timeout handling |
| 🗂️ Archive.org tools | Includes Archive.org file-scanning workflow |
| 🌍 Two languages | Separate English and Polish versions |
| 🎨 Cyber-Neon UI | Modern CustomTkinter desktop interface |

---

## Velocity interface refresh

The Polish and English launchers now share `aria2_velocity_ui.py`. Keep this module beside both launchers.

- Queue-first workspace with quieter graphite surfaces and cyan accents.
- Dedicated Transfers, Archive.org, Engine Log and Settings pages.
- Independent Archive.org URL field, keyboard selection and a consistently placed results toolbar.
- Visible queue actions, empty state and engine controls on every page.
- Starting a download keeps the queue visible; the full engine output remains available in Engine Log.

The progress strip reflects the latest aria2 console progress message. It is not a per-file or aggregate progress tracker when several files download concurrently. Existing aria2 process, pause/resume and configuration behavior is retained.

Windows: install the Python dependency using `INSTALUJ.bat`, place `aria2c.exe` beside the program (or on PATH), then run `START_PL.bat` or `START_EN.bat`. The aria2 executable is not bundled.

## 🌍 Language Versions

| Language | File |
|---|---|
| 🇬🇧 English | `aria2_gui_downloader_ENG.py` |
| 🇵🇱 Polski | `aria2_gui_downloader_PL.py` |

---

## 📋 Requirements

- Windows 10 / 11
- Python 3.8+
- `aria2c.exe`
- `customtkinter`

Install the Python dependency:

```bash
pip install customtkinter
```

Make sure `aria2c.exe` is available next to the script or in your system `PATH`.

---

## 📦 Installation

```bash
git clone https://github.com/Swir/Aria2Gui.git
cd Aria2Gui
pip install customtkinter
```

Run the English version:

```bash
python aria2_gui_downloader_ENG.py
```

Run the Polish version:

```bash
python aria2_gui_downloader_PL.py
```

---

## 🧩 Project Structure

```text
Aria2Gui/
├── aria2_gui_downloader_ENG.py   # English GUI
├── aria2_gui_downloader_PL.py    # Polish GUI
└── README.md
```

---

## 🔍 Discoverability

`aria2 gui` • `aria2c gui windows` • `aria2 frontend` • `windows download manager` • `python download manager` • `torrent downloader gui` • `magnet downloader` • `metalink downloader` • `archive.org downloader` • `customtkinter downloader` • `multi connection downloader`

---

## ⚖️ Responsible Use

Use the application only to download content you are authorized to access. Torrent and magnet support are general-purpose transfer technologies; users are responsible for complying with applicable law and source terms.

---

## 👨‍💻 Author

Developed by **Swir** — [@Swir](https://github.com/Swir)

<div align="center">

### ⚡ aria2c power without living in the terminal

⭐ **Star the repository if you find it useful!**

</div>

