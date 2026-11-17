#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DarkTxt-finder — Interfaz gráfica (GUI)
=======================================
Envoltura gráfica sobre el motor de búsqueda de main.py
(Aho-Corasick + multiprocessing). Reutiliza EXACTAMENTE las mismas
funciones de búsqueda, así que los resultados son idénticos al CLI.

Características pedidas:
  - Panel de configuración a la izquierda.
  - Términos: texto directo O documento (.txt/.csv) con valores
    separados por coma o por salto de línea.
  - Ruta de búsqueda (carpeta de "bases de datos").
  - Carpeta de salida configurable (se crea Export/ dentro).
  - Guarda la última configuración (parámetros) en un JSON para
    reutilizarla con datos nuevos en la siguiente ejecución.
  - Máxima velocidad por defecto (todos los núcleos, sin filtro de ext.).

Autor base del motor: m10sec (2025-2026)
"""

import json
import os
import queue
import sys
import threading
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# --- Motor de búsqueda: reutilizamos main.py tal cual ---
sys.path.insert(0, str(Path(__file__).resolve().parent))
import main as engine  # noqa: E402  (listar_archivos, cargar_pm_map, escribir_resultados, _init_worker, _process_file)

APP_TITLE = "DarkTxt-finder — GUI"
CONFIG_PATH = Path(__file__).resolve().parent / ".darktxt_gui.json"


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def parse_terms(text: str) -> List[str]:
    """Separa por salto de línea O por coma. Limpia, pasa a minúsculas,
    ignora comentarios (#) y elimina duplicados conservando el orden."""
    if not text:
        return []
    bruto = text.replace("\r", "\n").replace(",", "\n")
    vistos = set()
    limpios: List[str] = []
    for linea in bruto.split("\n"):
        s = linea.strip().strip('"').strip("'").lower()
        if not s or s.startswith("#"):
            continue
        if s not in vistos:
            vistos.add(s)
            limpios.append(s)
    return limpios


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[!] No se pudo guardar config: {e}\n")


# ----------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------
class DarkTxtGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1040x660")
        root.minsize(900, 560)

        self.msg_q: "queue.Queue[tuple]" = queue.Queue()
        self.worker: threading.Thread | None = None
        self.cancel_flag = threading.Event()

        self._build_style()
        self._build_layout()
        self._load_last_config()
        self.root.after(120, self._drain_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- estilo ----
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        bg = "#0d1117"
        panel = "#161b22"
        fg = "#c9d1d9"
        acc = "#2ea043"
        self.colors = dict(bg=bg, panel=panel, fg=fg, acc=acc)
        self.root.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg,
                        fieldbackground=panel, bordercolor="#30363d")
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=panel, foreground=fg)
        style.configure("Head.TLabel", background=panel, foreground=acc,
                        font=("TkDefaultFont", 11, "bold"))
        style.configure("TButton", background="#21262d", foreground=fg,
                        padding=5)
        style.map("TButton", background=[("active", "#30363d")])
        style.configure("Run.TButton", background=acc, foreground="#06230f",
                        font=("TkDefaultFont", 11, "bold"), padding=8)
        style.map("Run.TButton", background=[("active", "#3fb950")])
        style.configure("TCheckbutton", background=panel, foreground=fg)
        style.configure("TEntry", fieldbackground="#0d1117", foreground=fg)
        style.configure("TSpinbox", fieldbackground="#0d1117", foreground=fg)
        style.configure("Horizontal.TProgressbar", background=acc,
                        troughcolor=panel)

    # ---- layout ----
    def _build_layout(self):
        # ====== PANEL IZQUIERDO: CONFIGURACIÓN ======
        left = ttk.Frame(self.root, style="Panel.TFrame", padding=12)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="⚙  Configuración", style="Head.TLabel").pack(
            anchor="w", pady=(0, 8))

        # --- Términos ---
        ttk.Label(left, text="Términos / dominios").pack(anchor="w")
        ttk.Label(left, text="(uno por línea o separados por coma)",
                  foreground="#8b949e").pack(anchor="w")
        self.terms_txt = tk.Text(left, height=8, width=42, wrap="none",
                                 bg="#0d1117", fg=self.colors["fg"],
                                 insertbackground=self.colors["fg"],
                                 relief="flat", highlightthickness=1,
                                 highlightbackground="#30363d")
        self.terms_txt.pack(anchor="w", pady=(2, 4))
        row = ttk.Frame(left, style="Panel.TFrame")
        row.pack(anchor="w", fill="x")
        ttk.Button(row, text="Cargar archivo…",
                   command=self._load_terms_file).pack(side="left")
        ttk.Button(row, text="Limpiar",
                   command=lambda: self.terms_txt.delete("1.0", "end")
                   ).pack(side="left", padx=4)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        # --- Ruta de búsqueda ---
        self.var_db = tk.StringVar()
        self._path_row(left, "Ruta de búsqueda (bases de datos)",
                       self.var_db, self._browse_db)

        # --- Carpeta de salida ---
        self.var_out = tk.StringVar(value=str(Path.cwd()))
        self._path_row(left, "Carpeta de salida (crea Export/)",
                       self.var_out, self._browse_out)

        # --- PM CSV (opcional) ---
        self.var_pm = tk.StringVar()
        self._path_row(left, "PM CSV (opcional)", self.var_pm,
                       self._browse_pm, is_file=True)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        # --- Opciones de velocidad / filtros ---
        adv = ttk.Frame(left, style="Panel.TFrame")
        adv.pack(anchor="w", fill="x")

        ttk.Label(adv, text="Extensiones (vacío = todos)").grid(
            row=0, column=0, sticky="w", pady=2)
        self.var_ext = tk.StringVar()
        ttk.Entry(adv, textvariable=self.var_ext, width=22).grid(
            row=0, column=1, sticky="w", padx=4)

        ttk.Label(adv, text="Procesos (0 = todos)").grid(
            row=1, column=0, sticky="w", pady=2)
        self.var_jobs = tk.IntVar(value=0)
        ttk.Spinbox(adv, from_=0, to=(os.cpu_count() or 8), width=6,
                    textvariable=self.var_jobs).grid(
            row=1, column=1, sticky="w", padx=4)

        self.var_empty = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Crear archivos sin coincidencias",
                        variable=self.var_empty).pack(anchor="w", pady=(6, 0))
        self.var_infer = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Inferir PM desde las líneas",
                        variable=self.var_infer).pack(anchor="w")
        self.var_ignore = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Ignorar temporales/sistema (rápido)",
                        variable=self.var_ignore).pack(anchor="w")

        ttk.Label(left, text="⚡ Por defecto = máxima velocidad "
                             "(todos los núcleos).", foreground="#8b949e"
                  ).pack(anchor="w", pady=(10, 0))

        # ====== PANEL DERECHO: EJECUCIÓN ======
        right = ttk.Frame(self.root, padding=12)
        right.pack(side="left", fill="both", expand=True)

        topbar = ttk.Frame(right)
        topbar.pack(fill="x")
        self.run_btn = ttk.Button(topbar, text="▶  Buscar", style="Run.TButton",
                                  command=self._start)
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(topbar, text="■ Cancelar",
                                     command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        ttk.Button(topbar, text="Abrir carpeta salida",
                   command=self._open_out).pack(side="right")

        self.progress = ttk.Progressbar(right, mode="determinate",
                                        style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(10, 2))
        self.status_var = tk.StringVar(value="Listo.")
        ttk.Label(right, textvariable=self.status_var,
                  background=self.colors["bg"]).pack(anchor="w")

        ttk.Label(right, text="Registro", background=self.colors["bg"],
                  foreground=self.colors["acc"],
                  font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w", pady=(10, 2))
        self.log = scrolledtext.ScrolledText(
            right, bg="#010409", fg="#c9d1d9", relief="flat",
            insertbackground="#c9d1d9", highlightthickness=1,
            highlightbackground="#30363d", wrap="word")
        self.log.pack(fill="both", expand=True)
        self._log("Interfaz lista. Configura a la izquierda y pulsa Buscar.")

    def _path_row(self, parent, label, var, cmd, is_file=False):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(4, 0))
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(anchor="w", fill="x")
        ttk.Entry(row, textvariable=var, width=30).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row, text="…", width=3, command=cmd).pack(
            side="left", padx=3)

    # ---- acciones de archivo ----
    def _load_terms_file(self):
        path = filedialog.askopenfilename(
            title="Selecciona archivo de términos",
            filetypes=[("Texto/CSV", "*.txt *.csv *.lst"), ("Todos", "*.*")])
        if not path:
            return
        try:
            data = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
            return
        terms = parse_terms(data)
        self.terms_txt.delete("1.0", "end")
        self.terms_txt.insert("1.0", "\n".join(terms))
        self._log(f"Cargados {len(terms)} término(s) desde {Path(path).name}.")

    def _browse_db(self):
        d = filedialog.askdirectory(title="Carpeta con las bases de datos")
        if d:
            self.var_db.set(d)

    def _browse_out(self):
        d = filedialog.askdirectory(title="Carpeta de salida")
        if d:
            self.var_out.set(d)

    def _browse_pm(self):
        f = filedialog.askopenfilename(title="CSV de PMs",
                                       filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if f:
            self.var_pm.set(f)

    def _open_out(self):
        out = Path(self.var_out.get() or ".").expanduser() / "Export"
        if not out.exists():
            messagebox.showinfo("Salida", "Aún no existe la carpeta Export/.")
            return
        try:
            if sys.platform == "darwin":
                os.system(f'open "{out}"')
            elif os.name == "nt":
                os.startfile(str(out))  # type: ignore
            else:
                os.system(f'xdg-open "{out}"')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- config persistente ----
    def _collect_config(self) -> dict:
        return {
            "terms": self.terms_txt.get("1.0", "end").strip(),
            "db": self.var_db.get(),
            "out": self.var_out.get(),
            "pm": self.var_pm.get(),
            "ext": self.var_ext.get(),
            "jobs": self.var_jobs.get(),
            "empty": self.var_empty.get(),
            "infer": self.var_infer.get(),
            "ignore": self.var_ignore.get(),
        }

    def _load_last_config(self):
        cfg = load_config()
        if not cfg:
            return
        self.terms_txt.insert("1.0", cfg.get("terms", ""))
        self.var_db.set(cfg.get("db", ""))
        self.var_out.set(cfg.get("out", str(Path.cwd())))
        self.var_pm.set(cfg.get("pm", ""))
        self.var_ext.set(cfg.get("ext", ""))
        self.var_jobs.set(int(cfg.get("jobs", 0)))
        self.var_empty.set(bool(cfg.get("empty", False)))
        self.var_infer.set(bool(cfg.get("infer", True)))
        self.var_ignore.set(bool(cfg.get("ignore", True)))
        self._log("Última configuración restaurada.")

    # ---- logging / cola ----
    def _log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.msg_q.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "status":
                    self.status_var.set(payload)
                elif kind == "progress_max":
                    self.progress.configure(maximum=max(1, payload), value=0)
                elif kind == "progress":
                    self.progress.configure(value=payload)
                elif kind == "done":
                    self._finish(payload)
        except queue.Empty:
            pass
        self.root.after(120, self._drain_queue)

    # ---- ejecución ----
    def _start(self):
        if self.worker and self.worker.is_alive():
            return
        terms = parse_terms(self.terms_txt.get("1.0", "end"))
        if not terms:
            messagebox.showwarning("Faltan términos",
                                   "Escribe o carga al menos un término.")
            return
        db = Path(self.var_db.get()).expanduser()
        if not db.is_dir():
            messagebox.showwarning("Ruta inválida",
                                   "La ruta de búsqueda no es una carpeta válida.")
            return
        out_base = Path(self.var_out.get() or ".").expanduser()

        save_config(self._collect_config())  # guarda última config

        params = dict(
            terms=terms,
            db=str(db),
            out=str(out_base),
            pm=self.var_pm.get().strip(),
            exts=[e.strip().lstrip(".") for e in self.var_ext.get().split(",")
                  if e.strip()],
            jobs=int(self.var_jobs.get()),
            empty=bool(self.var_empty.get()),
            infer=bool(self.var_infer.get()),
            ignore=bool(self.var_ignore.get()),
        )

        self.cancel_flag.clear()
        self.run_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.log.delete("1.0", "end")
        self.progress.configure(value=0)
        self._log(f"Iniciando búsqueda de {len(terms)} término(s)…")

        self.worker = threading.Thread(target=self._run_search, args=(params,),
                                       daemon=True)
        self.worker.start()

    def _cancel(self):
        self.cancel_flag.set()
        self.msg_q.put(("status", "Cancelando…"))

    def _run_search(self, p: dict):
        q = self.msg_q
        try:
            terms: List[str] = p["terms"]
            out_dir = Path(p["out"]) / "Export"
            out_dir.mkdir(parents=True, exist_ok=True)

            pm_map: Dict[str, str] = {}
            if p["pm"]:
                pm_map = engine.cargar_pm_map(Path(p["pm"]).expanduser())
                q.put(("log", f"Mapa de PMs: {len(pm_map)} entradas."))

            q.put(("status", "Listando archivos…"))
            archivos = engine.listar_archivos(Path(p["db"]), p["exts"],
                                              ignore_trash=p["ignore"])
            q.put(("log", f"{len(archivos)} archivo(s) para analizar."))
            if not archivos:
                q.put(("done", {"con": 0, "tot": 0, "terms": len(terms),
                                "out": str(out_dir), "cancel": False}))
                return

            q.put(("progress_max", len(archivos)))
            jobs = p["jobs"] if p["jobs"] > 0 else (os.cpu_count() or 1)
            q.put(("status", f"Escaneando con {jobs} proceso(s)…"))

            agg: Dict[str, List[str]] = {d: [] for d in terms}
            ctx = mp.get_context("spawn")
            done = 0
            pool = ctx.Pool(processes=jobs, initializer=engine._init_worker,
                            initargs=(terms,))
            try:
                for result in pool.imap_unordered(engine._process_file,
                                                  archivos, chunksize=10):
                    if self.cancel_flag.is_set():
                        pool.terminate()
                        break
                    for d, line in result:
                        agg[d].append(line)
                    done += 1
                    if done % 5 == 0 or done == len(archivos):
                        q.put(("progress", done))
            finally:
                pool.close()
                pool.join()

            q.put(("progress", done))
            if self.cancel_flag.is_set():
                q.put(("done", {"con": 0, "tot": 0, "terms": len(terms),
                                "out": str(out_dir), "cancel": True}))
                return

            q.put(("status", "Guardando resultados…"))
            engine.escribir_resultados(agg, out_dir, p["empty"], pm_map,
                                       p["infer"])
            total = sum(len(v) for v in agg.values())
            con = sum(1 for v in agg.values() if v)
            q.put(("done", {"con": con, "tot": total, "terms": len(terms),
                            "out": str(out_dir), "cancel": False}))
        except Exception as e:
            q.put(("log", f"[X] Error: {e}"))
            q.put(("done", {"con": 0, "tot": 0, "terms": 0,
                            "out": "", "cancel": False, "error": str(e)}))

    def _finish(self, info: dict):
        self.run_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        if info.get("error"):
            self.status_var.set("Error en la búsqueda.")
            return
        if info.get("cancel"):
            self.status_var.set("Búsqueda cancelada.")
            self._log("[!] Búsqueda cancelada por el usuario.")
            return
        self.status_var.set(
            f"✅ {info['con']}/{info['terms']} con coincidencias · "
            f"{info['tot']} líneas.")
        self._log(f"✅ Completado. {info['con']}/{info['terms']} términos con "
                  f"coincidencias. Total líneas: {info['tot']}.")
        self._log(f"📂 Guardado en: {info['out']}")

    def _on_close(self):
        try:
            save_config(self._collect_config())
        except Exception:
            pass
        self.root.destroy()


def main_gui():
    root = tk.Tk()
    DarkTxtGUI(root)
    root.mainloop()


if __name__ == "__main__":
    mp.freeze_support()
    main_gui()
