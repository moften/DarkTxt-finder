#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buscador de dominios rápido (Aho-Corasick + multiprocessing)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import multiprocessing as mp
import unicodedata

# --- dependencias ---
try:
    import ahocorasick  # pyahocorasick
except Exception:
    print("[X] Falta el paquete 'pyahocorasick'. Instálalo con: pip install pyahocorasick", file=sys.stderr)
    sys.exit(1)

# --- barra de progreso opcional ---
try:
    from tqdm import tqdm
    _HAS_TQDM = True
except Exception:
    _HAS_TQDM = False

# --- config por defecto ---
DEF_EXTS = ["txt","csv","log","json","sql","tsv","xml","yml","yaml","ndjson"]

# --- Ignorar temporales/sistema (macOS, comunes y dev) ---
IGNORE_DIRNAMES = {
    # macOS / sistema
    ".Spotlight-V100", ".Trashes", ".Trash", ".fseventsd", ".TemporaryItems",
    ".DocumentRevisions-V100", ".AppleDouble", ".AppleDesktop", ".AppleDB",
    # comunes de desarrollo
    "__pycache__", ".git", ".hg", ".svn", ".idea", ".vscode", ".cache",
    "node_modules", "build", "dist", "target"
}

IGNORE_FILENAMES = {
    ".DS_Store", "Icon\r",  # volúmenes macOS
    "Thumbs.db", "desktop.ini",
}

IGNORE_FILE_PREFIXES = (
    "._",   # macOS resource forks "AppleDouble"
    "~$",   # MS Office temporales
    ".#",   # Emacs lockfiles
    "#",    # Emacs autosave (combinado con sufijo ~)
)

IGNORE_FILE_SUFFIXES = (
    "~",            
)

IGNORE_FILE_EXTS = (
    ".tmp", ".temp", ".swp", ".swo", ".swx",  # vim
    ".bak", ".old", ".orig", ".part", ".crdownload", ".download",
)

from colorama import Fore, Style, init as colorama_init
colorama_init(autoreset=True)

# --- banner / UI ---
def mostrar_banner():
    banner = (
        f"{Fore.CYAN}============================================================================{Style.RESET_ALL}\n\n"
        f"{Fore.BLUE}                ░  ░░░░░░░░        ░░░      ░░░  ░░░░  ░{Style.RESET_ALL}\n"
        f"{Fore.BLUE}                ▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒  ▒▒{Style.RESET_ALL}\n"
        f"{Fore.MAGENTA}                ▓  ▓▓▓▓▓▓▓▓      ▓▓▓▓  ▓▓▓▓  ▓▓     ▓▓▓▓{Style.RESET_ALL}\n"
        f"{Fore.MAGENTA}                █  ████████  ████████        ██  ███  ██{Style.RESET_ALL}\n"
        f"{Fore.RED}                █        ██        ██  ████  ██  ████  █{Style.RESET_ALL}\n"
        f"{Fore.YELLOW}                                        {Style.RESET_ALL}\n"
        f"{Fore.GREEN}         by m10sec (2025){Style.RESET_ALL} - {Fore.CYAN}Flipador de Tools{Style.RESET_ALL} - {Fore.MAGENTA}m10sec@proton.me{Style.RESET_ALL}\n"
        f"{Fore.YELLOW}        Buscador de dominios ultra-rápido en grandes bases de datos{Style.RESET_ALL}\n"
        f"{Fore.CYAN}                usando Aho-Corasick + Multiprocessing{Style.RESET_ALL}\n\n"
        f"{Fore.CYAN}============================================================================{Style.RESET_ALL}\n"
    )
    print(banner)

    print(f"{Style.BRIGHT}{Fore.YELLOW}=== Instrucciones de uso rápido ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}1){Style.RESET_ALL} Prepara un archivo TXT con un dominio (o lo que sea) por línea (sin http://).")
    print(f"{Fore.GREEN}2){Style.RESET_ALL} Coloca todas las 'bases de datos' (txt, csv, sql, logs, etc.) en una carpeta.")
    print(f"{Fore.GREEN}3){Style.RESET_ALL} Ejecuta el script y responde las preguntas o usa parámetros por CLI.\n")

    print(f"{Fore.CYAN}Ejemplo CLI:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python3 buscar_dominios_fast.py --dominios ./dominios.txt --db /ruta/bases "
          f"--ext txt,csv,log --out ./salida --crear-vacios --jobs 0{Style.RESET_ALL}\n")

    print(f"{Fore.CYAN}Por defecto:{Style.RESET_ALL}")
    print(f" - Extensiones: {Fore.GREEN}{','.join(DEF_EXTS)}{Style.RESET_ALL}")
    print(f" - Carpeta salida: {Fore.GREEN}carpeta actual{Style.RESET_ALL}")
    print(f" - jobs=0 usa {Fore.GREEN}todos los núcleos disponibles{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

# --- globals para workers ---
_G_DOMINIOS: List[str] = []
_G_AUTOMATON = None

def _init_worker(domains: List[str]):
    global _G_DOMINIOS, _G_AUTOMATON
    _G_DOMINIOS = domains

    automaton = ahocorasick.Automaton(
        store=ahocorasick.STORE_ANY,
        key_type=ahocorasick.KEY_STRING
    )
    for idx, d in enumerate(_G_DOMINIOS):
        automaton.add_word(d, (idx, d))  # value: (idx, dominio)
    automaton.make_automaton()
    _G_AUTOMATON = automaton

def _process_file(path: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for i, raw in enumerate(f, start=1):
                line = raw.rstrip("\n")
                low = line.lower()
                hits = set()
                for _, val in _G_AUTOMATON.iter(low):
                    hits.add(val[1])
                if hits:
                    for d in hits:
                        out.append((d, line))
    except Exception as e:
        sys.stderr.write(f"[!] No se pudo leer {p}: {e}\n")
    return out

# --- helpers de IO ---
def leer_dominios(path_lista: Path) -> List[str]:
    dominios = []
    with path_lista.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip().lower()
            if not s or s.startswith("#"):
                continue
            dominios.append(s)
    vistos = set()
    limpios = []
    for d in dominios:
        if d not in vistos:
            vistos.add(d)
            limpios.append(d)
    return limpios

def _is_ignored_path(p: Path) -> bool:
    """True si el archivo/directorio debe ignorarse por temporal/sistema."""
    name = p.name

    # ¿Algún directorio del path está en la lista?
    for part in p.parts:
        if part in IGNORE_DIRNAMES:
            return True

    # Reglas de archivo
    if p.is_file():
        if name in IGNORE_FILENAMES:
            return True
        for pref in IGNORE_FILE_PREFIXES:
            if name.startswith(pref):
                return True
        for suf in IGNORE_FILE_SUFFIXES:
            if name.endswith(suf):
                return True
        low = name.lower()
        for ext in IGNORE_FILE_EXTS:
            if low.endswith(ext):
                return True

    return False

def listar_archivos(raiz: Path, exts: List[str], ignore_trash: bool = True) -> List[str]:
    s_exts = set(e.lower().lstrip(".") for e in exts)
    archivos: List[str] = []
    ignorados = 0

    # rglob puede toparse con permisos/enlaces; protegemos
    for p in raiz.rglob("*"):
        try:
            # Salta directorios basura completos (acelera)
            if p.is_dir() and ignore_trash and p.name in IGNORE_DIRNAMES:
                continue

            if p.is_file():
                if ignore_trash and _is_ignored_path(p):
                    ignorados += 1
                    continue

                if not s_exts or p.suffix.lower().lstrip(".") in s_exts:
                    archivos.append(str(p))
        except Exception:
            ignorados += 1
            continue

    print(f"   (Ignorados {ignorados} temporales/sistema)")
    return archivos

def escribir_resultados(agg: Dict[str, List[str]], out_dir: Path, crear_archivo_vacio: bool):
    out_dir.mkdir(parents=True, exist_ok=True)
    for dominio, lines in agg.items():
        safe = dominio.replace("/", "_")
        out_path = out_dir / f"{safe}.txt"
        if lines or crear_archivo_vacio:
            with out_path.open("w", encoding="utf-8") as f:
                f.write(f"# Resultados para: {dominio}\n")
                if not lines:
                    f.write("(Sin coincidencias)\n")
                else:
                    f.write("\n".join(lines) + "\n")

def _normaliza_path_input(raw: str) -> Path:
    s = raw.strip().strip('"').strip("'")
    s = s.replace(r"\ ", " ")
    s = unicodedata.normalize("NFC", s)
    p = Path(os.path.expandvars(s)).expanduser()
    return p

def pedir_ruta(mensaje: str, debe_existir: bool = True, es_directorio: bool = False, por_defecto: Path | None = None) -> Path:
    while True:
        raw = input(mensaje)
        if not raw and por_defecto is not None:
            return por_defecto
        p = _normaliza_path_input(raw)

        if debe_existir:
            if not p.exists():
                print(f"   → La ruta no existe. Leí: {repr(raw)}")
                try:
                    print(f"     Normalizado: {p}")
                except Exception:
                    pass
                print("     Sugerencia: arrastra la carpeta desde Finder aquí o pégala entre comillas.")
                continue
            if es_directorio and not p.is_dir():
                print("   → No es un directorio, intenta de nuevo.")
                continue
            if not es_directorio and not p.is_file():
                print("   → No es un archivo, intenta de nuevo.")
                continue
        return p

# --- CLI ---
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Buscador de dominios rápido (Aho-Corasick + multiprocessing)")
    ap.add_argument("--dominios", type=str, help="Ruta del archivo de dominios (uno por línea)")
    ap.add_argument("--db", type=str, help="Carpeta raíz con las bases de datos")
    ap.add_argument("--ext", type=str, help=f"Extensiones (coma-separadas). Por defecto: {','.join(DEF_EXTS)}")
    ap.add_argument("--out", type=str, help="Carpeta de salida (por defecto: carpeta actual)")
    ap.add_argument("--crear-vacios", action="store_true", help="Crear archivos aunque no haya coincidencias")
    ap.add_argument("--jobs", type=int, default=0, help="Nº de procesos (0 = cpu_count)")
    ap.add_argument("--no-ignore", action="store_true",
                    help="No ignorar archivos temporales/sistema (por defecto se ignoran)")
    ap.add_argument("--no-progress", action="store_true",
                    help="Desactivar barra de progreso (tqdm)")
    return ap.parse_args()

# --- main ---
def main():
    mostrar_banner()
    args = parse_args()

    # dominios / término único
    if not args.dominios:
        entrada = input("1) Ruta del archivo de dominios (.txt) o término único a buscar: ").strip()
        if entrada and Path(entrada).expanduser().exists():
            lista_path = Path(entrada).expanduser()
            dominios = leer_dominios(lista_path)
        else:
            dominios = [entrada.lower()]
    else:
        lista_path = Path(args.dominios).expanduser()
        if lista_path.exists():
            dominios = leer_dominios(lista_path)
        else:
            dominios = [args.dominios.lower()]

    if not dominios or all(not d.strip() for d in dominios):
        print("[X] No se ha especificado dominio o término válido.")
        sys.exit(1)

    # carpeta DB
    if not args.db:
        db_root = pedir_ruta("2) Ruta de la carpeta con las 'bases de datos': ", True, True)
    else:
        db_root = Path(args.db).expanduser()

    # extensiones
    if not args.ext:
        exts_input = input(f"3) Extensiones [por defecto: {','.join(DEF_EXTS)}]: ").strip()
        extensiones = [e.strip().lstrip(".") for e in exts_input.split(",")] if exts_input else DEF_EXTS
    else:
        extensiones = [e.strip().lstrip(".") for e in args.ext.split(",")]

    # salida
    if not args.out:
        base_dir = pedir_ruta("4) Carpeta base de salida (Enter=actual): ", False, True, Path.cwd())
    else:
        base_dir = Path(args.out).expanduser()
    out_dir = base_dir / "Export"
    out_dir.mkdir(parents=True, exist_ok=True)

    # crear vacíos
    if not args.dominios or not args.db or not args.out or not args.ext:
        crear_vacios = input("5) ¿Crear archivos sin coincidencias? [s/N]: ").strip().lower().startswith("s")
    else:
        crear_vacios = args.crear_vacios

    jobs = args.jobs if args.jobs > 0 else os.cpu_count() or 1

    print(f"\n→ {len(dominios)} término(s) cargado(s).")
    print("→ Listando archivos...")
    archivos = listar_archivos(db_root, extensiones, ignore_trash=not args.no_ignore)
    print(f"   {len(archivos)} archivos para analizar.\n")

    print(f"→ Escaneando con {jobs} procesos...")
    agg: Dict[str, List[str]] = {d: [] for d in dominios}

    use_pbar = _HAS_TQDM and (not args.no_progress)
    if use_pbar:
        pbar = tqdm(total=len(archivos), unit="file", desc="Escaneando", smoothing=0.1)

    try:
        with mp.Pool(processes=jobs, initializer=_init_worker, initargs=(dominios,)) as pool:
            for result in pool.imap_unordered(_process_file, archivos, chunksize=10):
                for d, line in result:
                    agg[d].append(line)
                if use_pbar:
                    pbar.update(1)
    finally:
        if use_pbar:
            pbar.close()

    print("→ Guardando resultados...")
    escribir_resultados(agg, out_dir, crear_vacios)

    total_hits = sum(len(v) for v in agg.values())
    con_hits = sum(1 for v in agg.values() if v)
    print(f"\n✅ Completado. {con_hits}/{len(dominios)} términos con coincidencias. Total líneas: {total_hits}.")
    print(f"📂 Archivos guardados en: {out_dir}")

if __name__ == "__main__":
    try:
        mp.freeze_support()
        main()
    except KeyboardInterrupt:
        print("\n[!] Proceso interrumpido.")