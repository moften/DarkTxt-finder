# DarkTxt-finder

```
       ....                           s                      ...                                   ..      
   .xH888888Hx.                      :8                  .zf"` `"tu                          < .z@8"`      
 .H8888888888888:                   .88                 x88      '8N.                         !@88E        
 888*"""?""*88888X         u       :888ooo       u      888k     d88&      .u          u      '888E   u    
'f     d8x.   ^%88k     us888u.  -*8888888    us888u.   8888N.  @888F   ud8888.     us888u.    888E u@8NL  
'>    <88888X   '?8  .@88 "8888"   8888    .@88 "8888"  `88888 9888%  :888'8888. .@88 "8888"   888E`"88*"  
 `:..:`888888>    8> 9888  9888    8888    9888  9888     %888 "88F   d888 '88%" 9888  9888    888E .dN.   
        `"*88     X  9888  9888    8888    9888  9888      8"   "*h=~ 8888.+"    9888  9888    888E~8888   
   .xHHhx.."      !  9888  9888   .8888Lu= 9888  9888    z8Weu        8888L      9888  9888    888E '888&  
  X88888888hx. ..!   9888  9888   ^%888*   9888  9888   ""88888i.   Z '8888c. .+ 9888  9888    888E  9888. 
 !   "*888888888"    "888*""888"    'Y"    "888*""888" "   "8888888*   "88888%   "888*""888" '"888*" 4888" 
        ^"***"`       ^Y"   ^Y'             ^Y"   ^Y'        ^"**""      "YP'     ^Y"   ^Y'     ""    ""   
                                        
💀 fsantibanez@cqmrewards.com 💀
💀 Buscador de dominios ultra-rápido en grandes bases de datos 💀
💀 usando Aho-Corasick + Multiprocessing 💀

```

DarkTxt-finder es una herramienta en **Python** para buscar rápidamente coincidencias de **dominios** en grandes colecciones de archivos (`.txt`, `.csv`, `.log`, `.sql`, etc.) usando el algoritmo **Aho-Corasick** y procesamiento en paralelo (**multiprocessing**).

---

## Características

- **Búsqueda ultra-rápida** usando Aho-Corasick.
- **Multiproceso** para aprovechar todos los núcleos del CPU.
- Soporte para rutas con espacios y caracteres especiales.
- **Interfaz interactiva** o por **línea de comandos (CLI)**.
- Guarda resultados **por dominio o término de búsqueda** en la carpeta `Export/`.
- Permite **filtrar extensiones** de archivo a analizar.
- Compatible con macOS, Linux y Windows. (entorno Python)
- **Interfaz gráfica (GUI)** con Tkinter (`gui.py`), además del modo interactivo y CLI.
  - Panel de **configuración a la izquierda** y ejecución/registro a la derecha.
  - Términos escritos directamente **o** cargados desde un documento `.txt`/`.csv`
    con valores separados por **coma o por salto de línea**.
  - Selección por explorador de la **ruta de búsqueda** y de la **carpeta de salida**.
  - **Guarda la última configuración** (todos los parámetros, incluidos los términos)
    y la restaura en el siguiente arranque, para reutilizarla con datos nuevos.
  - **Máxima velocidad por defecto** (todos los núcleos, sin filtro de extensiones).
  - Barra de progreso, registro en vivo y botón **Cancelar**.

---

## Requisitos

Instala los requeriments:

```bash
pyahocorasick>=2.1.0
colorama>=0.4.6
PyYAML>=6.0.1
tqdm>=4.66.1
python-dotenv
```

Instálalo con:

```bash
pip3 install -r requirements.txt
```

> Todo lo demás usa bibliotecas estándar de Python 3.8+.

---

## Estructura de carpetas

```bash
DarkTxt-finder/
├── main.py              # Script principal
├── gui.py               # Interfaz gráfica (Tkinter)
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Este archivo
├── .gitignore           # Archivos/carpetas a ignorar en git
├── .gitattributes       # Configuración de codificación y saltos de línea
└── Export/              # Resultados generados (creada automáticamente)
└── .env                 # Variables para el envío de email a PM
```

---

## Instalación

1. Clona este repositorio:

   ```bash
   git clone https://fsantibanez1@bitbucket.org/cqm/leakmonitor.git
   cd leakmonitor
   ```

2. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Asegúrate de tener tu archivo de dominios (ej: `dominios.txt`), y opcionalmente el archivo de PMs, pero siempre puedes usar cualquier término

4. Recuerda tener a la mano una "base de datos" ;)

---

## Uso

### Ejecución interactiva
```bash
python3 main.py
```
El programa te pedirá paso a paso:
1. Ruta del archivo de dominios (`.txt`, un dominio por línea).
2. Carpeta donde buscar (bases de datos).
3. Extensiones de archivos a considerar (por default: txt).
4. Carpeta base para resultados.
5. Si quieres crear archivos vacíos cuando no haya coincidencias (por default: no).

### Ejecución por CLI
```bash
python3 main.py   --dominios ./dominios.txt   --db "/ruta/con bases de datos"   --ext txt,csv,log,sql   --out ./   --crear-vacios   --jobs 0 --pm-csv ./pm_map.csv
```

Parámetros:
- `--dominios` → Archivo con lista de dominios.
- `--db` → Carpeta raíz para escanear.
- `--ext` → Extensiones a considerar (coma-separadas).
- `--out` → Carpeta base donde se creará `Export/`.
- `--crear-vacios` → (opcional) Crea archivo aunque no haya coincidencias.
- `--jobs` → Número de procesos (0 = todos los núcleos).
- `--pm-csv ./pm_map.csv`  → usa la lista de PMs para generar la salida

---

## Interfaz gráfica (GUI)

Lanza la ventana con tu entorno virtual (que incluye `pyahocorasick`):

```bash
cd DarkTxt-finder
source .venv/bin/activate     # o: source venv/bin/activate
python3 gui.py
```

### Panel de configuración (izquierda)

1. **Términos / dominios** — escríbelos (uno por línea o separados por coma) o
   pulsa **Cargar archivo…** para importar un `.txt`/`.csv`. Se normalizan a
   minúsculas, se eliminan duplicados y se ignoran las líneas de comentario (`#`).
2. **Ruta de búsqueda** — carpeta raíz de las "bases de datos" (p. ej. la unidad
   de un **disco duro externo**: apunta a `/Volumes/TU_DISCO/...`).
3. **Carpeta de salida** — dentro se crea `Export/`, igual que en el CLI.
4. **PM CSV** (opcional) — etiqueta cada resultado con su responsable.
5. **Extensiones** — vacío = todos los archivos. Limita (p. ej. `txt,csv,log`)
   para acotar y acelerar en discos muy grandes.
6. **Procesos** — `0` = todos los núcleos (máxima velocidad).
7. Casillas: crear archivos sin coincidencias · inferir PM desde las líneas ·
   ignorar temporales/sistema.

### Panel de ejecución (derecha)

- Botón **Buscar**, barra de **progreso**, **registro** en vivo y **Cancelar**.
- **Abrir carpeta salida** abre `Export/` en el explorador del sistema.

### Configuración persistente

Al ejecutar (y al cerrar) se guarda la última configuración en
**`.darktxt_gui.json`** (junto al script). En el siguiente arranque se restaura
automáticamente, de modo que puedes repetir la misma búsqueda sobre **datos
nuevos** sin volver a rellenar los campos.

---

## Formato de resultados

En la carpeta `Export/` se genera **un archivo por dominio**:

```bash
Export/
├── emotivoo.com.txt
├── reale.es.txt
└── ...
```

Cada archivo contiene:

```bash
# Resultados para: google.com
# PM asignado: pm@cqmrewards.com
Coincidencia de ejemplo en algún archivo
Otra coincidencia más, emails, o plataformas
```

---

## Notas y consejos

- Puedes **arrastrar y soltar carpetas/archivos** en la consola para que la ruta salga exacta.
- Si tienes **millones de líneas**, la búsqueda seguirá siendo rápida gracias a Aho-Corasick (usando todos los hilos disponibles incluso con Apple Silicon).
- `Export/` está en `.gitignore` para no subir datos sensibles, estos archivos se envían directo su PM y a la carpeta de leaks asignados

---

## Créditos

🏴‍☠️ Desarrollado por m10sec (2025)
💻 Made with Python + Caffeine
🏴‍☠️ fsantibanez@cqmrewards.com