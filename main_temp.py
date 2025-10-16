#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import multiprocessing as mp
import unicodedata
import csv
import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import urlparse

# --- dependencias opcionales / progreso ---
try:
    import ahocorasick  # pyahocorasick
except Exception:
    print("[X] Falta el paquete 'pyahocorasick'. Instálalo con: pip install pyahocorasick", file=sys.stderr)
    sys.exit(1)

try:
    from tqdm import tqdm
    _HAS_TQDM = True
except Exception:
    _HAS_TQDM = False

try:
    from dotenv import load_dotenv  # pip install python-dotenv
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False

from colorama import Fore, Style, init as colorama_init
colorama_init(autoreset=True)

# --- configuración por defecto de extensiones y filtros ---
DEF_EXTS = ["txt","csv","log","json","sql","tsv","xml","yml","yaml","ndjson"]

IGNORE_DIRNAMES = {
    # macOS / sistema
    ".Spotlight-V100", ".Trashes", ".Trash", ".fseventsd", ".TemporaryItems",
    ".DocumentRevisions-V100", ".AppleDouble", ".AppleDesktop", ".AppleDB",
    # comunes de desarrollo
    "__pycache__", ".git", ".hg", ".svn", ".idea", ".vscode", ".cache",
    "node_modules", "build", "dist", "target"
}

IGNORE_FILENAMES = {
    ".DS_Store", "Icon\r",
    "Thumbs.db", "desktop.ini",
}

IGNORE_FILE_PREFIXES = ("._", "~$", ".#", "#")
IGNORE_FILE_SUFFIXES = ("~",)
IGNORE_FILE_EXTS = (
    ".tmp", ".temp", ".swp", ".swo", ".swx",
    ".bak", ".old", ".orig", ".part", ".crdownload", ".download",
)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# --- tipos de datos ---
@dataclass
class EmailConfig:
    host: str
    port: int
    user: str
    password: str
    sender: str

# --- banner ---
def mostrar_banner():
    banner_ascii = f'''
{Fore.RED}       ....                           s                      ...                                   ..      {Style.RESET_ALL}
{Fore.RED}   .xH888888Hx.                      :8                  .zf"` `"tu                          < .z@8"`      {Style.RESET_ALL}
{Fore.RED} .H8888888888888:                   .88                 x88      '8N.                         !@88E        {Style.RESET_ALL}
{Fore.RED} 888*"""?""*88888X         u       :888ooo       u      888k     d88&      .u          u      '888E   u    {Style.RESET_ALL}
{Fore.MAGENTA}'f     d8x.   ^%88k     us888u.  -*8888888    us888u.   8888N.  @888F   ud8888.     us888u.    888E u@8NL  {Style.RESET_ALL}
{Fore.MAGENTA}'>    <88888X   '?8  .@88 "8888"   8888    .@88 "8888"  `88888 9888%  :888'8888. .@88 "8888"   888E`"88*"  {Style.RESET_ALL}
{Fore.BLUE} `:..:`888888>    8> 9888  9888    8888    9888  9888     %888 "88F   d888 '88%" 9888  9888    888E .dN.   {Style.RESET_ALL}
{Fore.BLUE}        `"*88     X  9888  9888    8888    9888  9888      8"   "*h=~ 8888.+"    9888  9888    888E~8888   {Style.RESET_ALL}
{Fore.CYAN}   .xHHhx.."      !  9888  9888   .8888Lu= 9888  9888    z8Weu        8888L      9888  9888    888E '888&  {Style.RESET_ALL}
{Fore.CYAN}  X88888888hx. ..!   9888  9888   ^%888*   9888  9888   ""88888i.   Z '8888c. .+ 9888  9888    888E  9888. {Style.RESET_ALL}
{Fore.YELLOW} !   "*888888888"    "888*""888"    'Y"    "888*""888" "   "8888888*   "88888%   "888*""888" '"888*" 4888" {Style.RESET_ALL}
{Fore.YELLOW}        ^"***"`       ^Y"   ^Y'             ^Y"   ^Y'        ^"**""      "YP'     ^Y"   ^Y'     ""    ""   {Style.RESET_ALL}
    '''
    print(f"{Fore.CYAN}============================================================================{Style.RESET_ALL}")
    print(banner_ascii)
    print(f"{Fore.CYAN}============================================================================{Style.RESET_ALL}\n")
    print(f"{Fore.GREEN}         by m10sec (2025){Style.RESET_ALL} - {Fore.CYAN}Flipador de Tools{Style.RESET_ALL} - {Fore.MAGENTA}m10sec@proton.me{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}        Buscador de dominios ultra-rápido en grandes bases de datos{Style.RESET_ALL}")
    print(f"{Fore.CYAN}                usando Aho-Corasick + Multiprocessing{Style.RESET_ALL}\n")
    print(f"{Style.BRIGHT}{Fore.YELLOW}=== Instrucciones de uso rápido ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}1){Style.RESET_ALL} Prepara un archivo TXT con un dominio (o lo que sea) por línea (sin http://).")
    print(f"{Fore.GREEN}2){Style.RESET_ALL} Coloca todas las 'bases de datos' (txt, csv, sql, logs, etc.) en una carpeta.")
    print(f"{Fore.GREEN}3){Style.RESET_ALL} Ejecuta el script y responde las preguntas o usa parámetros por CLI.\n")
    print(f"{Fore.CYAN}Ejemplo CLI:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python3 main.py --dominios ./dominios.txt --db /ruta/bases --ext txt,csv,log --out ./salida --pm-csv ./pm_map.csv --jobs 0{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}Por defecto:{Style.RESET_ALL}")
    print(f" - Extensiones: {Fore.GREEN}{','.join(DEF_EXTS)}{Style.RESET_ALL}")
    print(f" - Carpeta salida: {Fore.GREEN}carpeta actual{Style.RESET_ALL}")
    print(f" - jobs=0 usa {Fore.GREEN}todos los núcleos disponibles{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

# --- Aho-Corasick globals para los workers ---
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
        automaton.add_word(d, (idx, d))
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

# --- utilidades ---
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
    name = p.name
    for part in p.parts:
        if part in IGNORE_DIRNAMES:
            return True
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
    for p in raiz.rglob("*"):
        try:
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

def normalizar_dominio(valor: str) -> str:
    s = (valor or "").strip().lower()
    if not s:
        return ""
    if "://" in s or "/" in s:
        try:
            if "://" not in s:
                s = "http://" + s
            host = urlparse(s).hostname or ""
            s = host
        except Exception:
            pass
    if s.startswith("www."):
        s = s[4:]
    return s

# --- PM / owners ---
def cargar_pm_map(pm_csv_path: Path) -> Dict[str, str]:
    pm_map: Dict[str, str] = {}
    if not pm_csv_path or not pm_csv_path.exists() or not pm_csv_path.is_file():
        return pm_map

    def detectar_delimitador(sample: str) -> str:
        for d in [",", ";", ":"]:
            if d in sample:
                return d
        return ","

    def es_fila_encabezado(row: List[str]) -> bool:
        if not row:
            return False
        cells = [c.strip().lower() for c in row]
        dom_like = {"dominio", "domain", "host", "url"}
        pm_like  = {"pm", "owner", "responsable", "manager", "contacto", "contact", "mail", "email", "correo"}
        return any(c in dom_like or c in pm_like for c in cells)

    try:
        with pm_csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            sample = f.read(4096); f.seek(0)
            delim = detectar_delimitador(sample)
            reader = csv.reader(f, delimiter=delim)
            rows = [r for r in reader if any(c.strip() for c in r)]
        if not rows:
            return pm_map

        header = rows[0]
        has_header = es_fila_encabezado(header)

        dom_idx = 0; pm_idx = 1; url_idx = None
        if has_header:
            cols = [c.strip().lower() for c in header]
            dom_candidates = ["dominio", "domain", "host", "url"]
            pm_candidates  = ["pm", "owner", "responsable", "manager", "contacto", "contact", "mail", "email", "correo"]
            for name in dom_candidates:
                if name in cols: dom_idx = cols.index(name); break
            for name in pm_candidates:
                if name in cols: pm_idx = cols.index(name); break
            if "url" in cols:
                url_idx = cols.index("url")
            data_rows = rows[1:]
        else:
            first = rows[0]; n = len(first)
            if n >= 3: dom_idx, pm_idx, url_idx = 0, 2, 1
            elif n == 2: dom_idx, pm_idx = 0, 1
            else: dom_idx, pm_idx = 0, n-1
            data_rows = rows

        for row in data_rows:
            while len(row) <= max(dom_idx, pm_idx):
                row.append("")
            dom_raw = row[dom_idx].strip()
            pm_raw  = row[pm_idx].strip()
            if not dom_raw and url_idx is not None and url_idx < len(row):
                dom_raw = row[url_idx].strip()

            dom_key = normalizar_dominio(dom_raw)
            if not dom_key or not pm_raw:
                continue
            pm_map[dom_key] = pm_raw
            www_key = "www." + dom_key
            if www_key not in pm_map:
                pm_map[www_key] = pm_raw

    except Exception as e:
        sys.stderr.write(f"[!] No se pudo cargar PM map desde {pm_csv_path}: {e}\n")

    return pm_map

def _domain_from_urlish(urlish: str) -> Optional[str]:
    s = (urlish or "").strip()
    if not s: return None
    s = s.split()[0]
    s_test = "http://" + s if "://" not in s else s
    try:
        host = urlparse(s_test).hostname
        if host:
            return normalizar_dominio(host)
    except Exception:
        return None
    return None

def _find_suffix_match(domain: str, pm_map: Dict[str, str]) -> Optional[str]:
    d = normalizar_dominio(domain)
    if not d: return None
    if d in pm_map: return pm_map[d]
    if ("www." + d) in pm_map: return pm_map["www." + d]
    parts = d.split(".")
    for i in range(1, len(parts) - 1):
        cand = ".".join(parts[i:])
        if cand in pm_map: return pm_map[cand]
        if ("www." + cand) in pm_map: return pm_map[cand]
    return None

def _infer_pm_from_lines(lines: List[str], pm_map: Dict[str, str]) -> Optional[str]:
    for line in lines:
        candidate = line.split()[0] if line.strip() else ""
        host = _domain_from_urlish(candidate.split(":")[0] if "://" not in candidate and ":" in candidate else candidate)
        if not host:
            first_field = line.split(":", 1)[0].strip()
            host = _domain_from_urlish(first_field)
        if host:
            pm = _find_suffix_match(host, pm_map)
            if pm:
                return pm
    return None

def extract_first_email(text: str) -> Optional[str]:
    m = EMAIL_REGEX.search(text or "")
    return m.group(0) if m else None

def parse_email_from_pm(pm_info: str) -> Optional[str]:
    if not pm_info: return None
    m = re.search(r"<([^>]+)>", pm_info)
    if m and EMAIL_REGEX.fullmatch(m.group(1).strip()):
        return m.group(1).strip()
    m = re.search(r"$begin:math:text$([^)]+)$end:math:text$", pm_info)
    if m and EMAIL_REGEX.fullmatch(m.group(1).strip()):
        return m.group(1).strip()
    return extract_first_email(pm_info)

def _clean_pm_display(pm_info: Optional[str]) -> Optional[str]:
    return pm_info.replace("<", "").replace(">", "") if pm_info else None

def escribir_resultados(
    agg: Dict[str, List[str]],
    out_dir: Path,
    crear_archivo_vacio: bool,
    pm_map: Optional[Dict[str, str]] = None,
    infer_pm_from_urls: bool = True
) -> Dict[str, Dict[str, Optional[str]]]:
    pm_map = pm_map or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    meta: Dict[str, Dict[str, Optional[str]]] = {}
    for dominio, lines in agg.items():
        safe = dominio.replace("/", "_")
        out_path = out_dir / f"{safe}.txt"
        if not lines and not crear_archivo_vacio:
            continue

        pm_info = _find_suffix_match(dominio, pm_map)
        if not pm_info and infer_pm_from_urls and lines:
            pm_info = _infer_pm_from_lines(lines, pm_map)

        email = parse_email_from_pm(pm_info) if pm_info else None
        if not email and lines:
            for ln in lines:
                email = extract_first_email(ln)
                if email: break

        with out_path.open("w", encoding="utf-8") as f:
            f.write(f"# Resultados para: {dominio}\n")
            if pm_info:
                if parse_email_from_pm(pm_info):
                    f.write(f"# PM asignado: {pm_info}\n")
                else:
                    f.write(f"# PM asignado: {_clean_pm_display(pm_info)}\n")
            if not lines:
                f.write("(Sin coincidencias)\n")
            else:
                f.write("\n".join(lines) + "\n")

        meta[dominio] = {"path": str(out_path), "email": email, "pm": pm_info}
    return meta

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
                try: print(f"     Normalizado: {p}")
                except Exception: pass
                print("     Sugerencia: arrastra la carpeta desde Finder aquí o pégala entre comillas.")
                continue
            if es_directorio and not p.is_dir():
                print("   → No es un directorio, intenta de nuevo."); continue
            if not es_directorio and not p.is_file():
                print("   → No es un archivo, intenta de nuevo."); continue
        return p

# --- SMTP helpers ---
def load_env_file(env_path: Optional[str]) -> None:
    if env_path and Path(env_path).expanduser().is_file() and _HAS_DOTENV:
        load_dotenv(dotenv_path=str(Path(env_path).expanduser()))
    elif env_path and not _HAS_DOTENV:
        print("[!] Aviso: especificaste --env-file pero falta 'python-dotenv'. Instálalo con: pip install python-dotenv")

def get_email_config_from_env() -> Optional[EmailConfig]:
    host = os.environ.get("SMTP_HOST", "")
    port = os.environ.get("SMTP_PORT", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    sender = os.environ.get("SMTP_SENDER", "")
    if not (host and port and user and password and sender):
        return None
    try:
        port_i = int(port)
    except Exception:
        print("[!] SMTP_PORT no es un entero válido.")
        return None
    return EmailConfig(host=host, port=port_i, user=user, password=password, sender=sender)

def _smtp_missing_fields() -> List[str]:
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_SENDER"]
    return [k for k in required if not os.environ.get(k)]

def build_ssl_context(ca_file: Optional[str] = None, skip_verify: bool = False) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if ca_file and Path(ca_file).is_file():
        try:
            ctx.load_verify_locations(cafile=ca_file)
        except Exception as e:
            print(f"[!] No se pudo cargar CA_FILE {ca_file}: {e}")
    if skip_verify:
        # ⚠️ SOLO para pruebas
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        print("[!] Advertencia: verificación TLS desactivada (SMTP_SKIP_VERIFY=true)")
    return ctx

def send_leak_email(cfg: EmailConfig, to_addr: str, subject: str, body: str, attachments: List[Path] = None) -> bool:
    """
    Envía email soportando:
      - SMTP_TLS_MODE=starttls (por defecto) → típico en puerto 587 (o 25 STARTTLS si el server lo soporta)
      - SMTP_TLS_MODE=ssl                    → SSL implícito (465)
      - SMTP_TLS_MODE=none                   → sin TLS (25)  **no recomendado para producción**
    Soporta:
      - SMTP_CA_FILE  → ruta a PEM de cadena/CA
      - SMTP_SKIP_VERIFY=true → desactiva verificación TLS (solo pruebas)
    """
    tls_mode = (os.environ.get("SMTP_TLS_MODE", "starttls") or "starttls").lower()
    ca_file = os.environ.get("SMTP_CA_FILE") or None
    skip_verify = (os.environ.get("SMTP_SKIP_VERIFY", "false").strip().lower() in ("1","true","yes","y","si","sí"))

    msg = EmailMessage()
    msg["From"] = cfg.sender
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    for ap in attachments or []:
        try:
            data = ap.read_bytes()
            msg.add_attachment(data, maintype="text", subtype="plain", filename=ap.name)
        except Exception as e:
            print(f"[!] No se pudo adjuntar {ap}: {e}")

    ctx = build_ssl_context(ca_file, skip_verify)

    try:
        if tls_mode == "ssl":
            # SSL implícito (465)
            with smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=20, context=ctx) as server:
                server.login(cfg.user, cfg.password)
                server.send_message(msg)
        else:
            # starttls o none
            with smtplib.SMTP(cfg.host, cfg.port, timeout=20) as server:
                server.ehlo()
                if tls_mode == "starttls":
                    server.starttls(context=ctx)
                    server.ehlo()
                # En modo "none", no TLS: no llamar starttls
                server.login(cfg.user, cfg.password)
                server.send_message(msg)
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[!] Autenticación SMTP fallida: {e}")
    except smtplib.SMTPResponseException as e:
        print(f"[!] Servidor SMTP respondió {e.smtp_code} {e.smtp_error}")
    except ssl.SSLError as e:
        print(f"[!] Error TLS/SSL: {e}")
        print("    Sugerencias: verifica fecha/hora del sistema, usa SMTP_TLS_MODE apropiado,"
              " ajusta SMTP_CA_FILE a la cadena PEM o actualiza certificados del sistema.")
    except Exception as e:
        print(f"[!] Error genérico SMTP: {e}")

    return False

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
    ap.add_argument("--pm-csv", type=str, help="CSV (dominio,pm o dominio,url,pm) para etiquetar a quién pertenecen los leaks")
    ap.add_argument("--no-infer-pm", action="store_true",
                    help="No inferir PM desde hostnames reales en líneas url:user:pass")

    # Notificación por correo
    ap.add_argument("--env-file", type=str, help="Ruta de un .env externo con credenciales SMTP (opcional)")
    ap.add_argument("--auto-notify", action="store_true",
                    help="No preguntar y enviar correo automáticamente si hay destinatario y SMTP configurado")
    return ap.parse_args()

def _ask_yes(prompt: str, default: bool = False) -> bool:
    resp = input(prompt).strip().lower()
    if not resp:
        return default
    return resp in ("s", "si", "sí", "y", "yes", "true", "1")

# --- main ---
def main():
    mostrar_banner()
    args = parse_args()

    # 1) dominios / término
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

    # 2) carpeta DB
    if not args.db:
        db_root = pedir_ruta("2) Ruta de la carpeta con las 'bases de datos': ", True, True)
    else:
        db_root = Path(args.db).expanduser()

    # 3) extensiones
    if not args.ext:
        exts_input = input(f"3) Extensiones [por defecto: {','.join(DEF_EXTS)}]: ").strip()
        extensiones = [e.strip().lstrip(".") for e in exts_input.split(",")] if exts_input else DEF_EXTS
    else:
        extensiones = [e.strip().lstrip(".") for e in args.ext.split(",")]

    # 4) salida
    if not args.out:
        base_dir = pedir_ruta("4) Carpeta base de salida (Enter=actual): ", False, True, Path.cwd())
    else:
        base_dir = Path(args.out).expanduser()
    out_dir = base_dir / "Export"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 5) crear vacíos
    if not args.dominios or not args.db or not args.out or not args.ext:
        crear_vacios = _ask_yes("5) ¿Crear archivos sin coincidencias? [s/N]: ", default=False)
    else:
        crear_vacios = bool(args.crear_vacios)

    # PM map (opcional)
    pm_map: Dict[str, str] = {}
    if getattr(args, "pm_csv", None):
        pm_csv_path = Path(args.pm_csv).expanduser()
        pm_map = cargar_pm_map(pm_csv_path)
        if pm_map:
            print(f"→ Mapa de PMs cargado: {len(pm_map)} dominios con responsable.")
        else:
            print("→ No se cargó información de PMs o está vacía (continuando sin etiquetas).")

    infer_pm_from_urls = not args.no_infer_pm

    print(f"\n→ {len(dominios)} término(s) cargado(s).")
    print("→ Listando archivos...")
    archivos = listar_archivos(db_root, extensiones, ignore_trash=not args.no_ignore)
    print(f"   {len(archivos)} archivos para analizar.\n")

    # Nº de procesos
    jobs = args.jobs if args.jobs > 0 else (os.cpu_count() or 1)
    print(f"→ Escaneando con {jobs} proceso(s)...")

    # Agregador de resultados
    agg: Dict[str, List[str]] = {d: [] for d in dominios}

    # Barra de progreso
    use_pbar = _HAS_TQDM and (not args.no_progress)
    pbar = tqdm(total=len(archivos), unit="file", desc="Escaneando", smoothing=0.1) if use_pbar else None

    # Pool
    try:
        with mp.Pool(processes=jobs, initializer=_init_worker, initargs=(dominios,)) as pool:
            for result in pool.imap_unordered(_process_file, archivos, chunksize=10):
                for d, line in result:
                    agg[d].append(line)
                if pbar: pbar.update(1)
    finally:
        if pbar: pbar.close()

    # Guardar + meta para notificaciones
    print("→ Guardando resultados...")
    meta = escribir_resultados(agg, out_dir, crear_vacios, pm_map, infer_pm_from_urls)

    total_hits = sum(len(v) for v in agg.values())
    con_hits = sum(1 for v in agg.values() if v)
    print(f"\n✅ Completado. {con_hits}/{len(dominios)} términos con coincidencias. Total líneas: {total_hits}.")
    print(f"📂 Archivos guardados en: {out_dir}")

    # --- Envío por correo (opcional) ---
    load_env_file(args.env_file)
    smtp_cfg = get_email_config_from_env()
    dominios_con_dest = {d: m for d, m in meta.items() if m.get("email")}
    hay_destinatarios = bool(dominios_con_dest)

    # Validaciones previas
    if not smtp_cfg:
        faltan = _smtp_missing_fields()
        print("ℹ️ SMTP no configurado en entorno/.env. No se enviarán correos.")
        if faltan:
            print(f"   → Faltan variables: {', '.join(faltan)}")
        return
    if not hay_destinatarios:
        print("ℹ️ No se encontraron correos destino en PMs ni en los leaks. No se enviarán correos.")
        return

    # Confirmación
    if not args.auto_notify:
        if not _ask_yes("¿Quieres informar de los leaks por correo ahora? [s/N]: ", default=False):
            print("ℹ️ Envío por correo cancelado por el usuario.")
            return

    print("→ Enviando notificaciones de leaks por correo...")
    enviados, fallidos = 0, 0
    for dominio, info in dominios_con_dest.items():
        to_addr = info["email"]
        if not to_addr:  # redundante, pero seguro
            continue
        attachment = Path(info["path"])
        pm_info = info.get("pm") or "(desconocido)"
        subject = f"[Leak] Resultados para {dominio}"
        body = (
            f"Hola,\n\n"
            f"Se han encontrado posibles coincidencias para el término/dominio: {dominio}\n"
            f"PM asignado: {pm_info}\n\n"
            f"Adjunto el archivo con el detalle de líneas encontradas.\n\n"
            f"— Enviado automáticamente por DarkTxt-finder\n"
        )
        ok = send_leak_email(
            smtp_cfg,
            to_addr=to_addr,
            subject=subject,
            body=body,
            attachments=[attachment] if attachment.exists() else []
        )
        if ok:
            enviados += 1
            print(f"   ✔ Enviado a {to_addr} ({dominio})")
        else:
            fallidos += 1
            print(f"   ✖ Falló envío a {to_addr} ({dominio})")

    print(f"→ Notificaciones completadas. Éxitos: {enviados}, Fallos: {fallidos}")

if __name__ == "__main__":
    try:
        mp.freeze_support()
        main()
    except KeyboardInterrupt:
        print("\n[!] Proceso interrumpido.")