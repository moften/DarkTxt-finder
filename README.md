# 🕵️‍♂️ DarkTxt-finder

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
                                        
by m10sec m10sec@proton.me
  🔍 Buscador de dominios ultra-rápido en grandes bases de datos
     usando Aho-Corasick + Multiprocessing
```

DarkTxt-finder es una herramienta en **Python** para buscar rápidamente coincidencias de **dominios** en grandes colecciones de archivos (`.txt`, `.csv`, `.log`, `.sql`, etc.) usando el algoritmo **Aho-Corasick** y procesamiento en paralelo (**multiprocessing**).

---

## 🚀 Características

- **Búsqueda ultra-rápida** usando Aho-Corasick.
- **Multiproceso** para aprovechar todos los núcleos del CPU.
- Soporte para rutas con espacios y caracteres especiales.
- **Interfaz interactiva** o por **línea de comandos (CLI)**.
- Guarda resultados **por dominio** en la carpeta `Export/`.
- Permite **filtrar extensiones** de archivo a analizar.
- Compatible con macOS, Linux y Windows. (entorno python)

---

## 📦 Requisitos

Instala los requeriments

```txt
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

## 📂 Estructura de carpetas

```
DarkTxt-finder/
├── main.py              # Script principal
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Este archivo
├── .gitignore           # Archivos/carpetas a ignorar en git
├── .gitattributes       # Configuración de codificación y saltos de línea
└── Export/              # Resultados generados (creada automáticamente)
```

---

## 🛠 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/moften/DarkTxt-finder.git
   cd DarkTxt-finder
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Asegúrate de tener tu archivo de dominios (ejemplo: `dominios.txt`).

---

## 💻 Uso

### Ejecución interactiva
```bash
python3 main.py
```
El programa te pedirá paso a paso:
1. Ruta del archivo de dominios (`.txt`, un dominio por línea).
2. Carpeta donde buscar (bases de datos).
3. Extensiones de archivos a considerar.
4. Carpeta base para resultados.
5. Si quieres crear archivos vacíos cuando no haya coincidencias.

### Ejecución por CLI
```bash
python3 main.py   --dominios ./dominios.txt   --db "/ruta/con bases de datos"   --ext txt,csv,log,sql   --out ./   --crear-vacios   --jobs 0
```

Parámetros:
- `--dominios` → Archivo con lista de dominios.
- `--db` → Carpeta raíz para escanear.
- `--ext` → Extensiones a considerar (coma-separadas).
- `--out` → Carpeta base donde se creará `Export/`.
- `--crear-vacios` → (opcional) Crea archivo aunque no haya coincidencias.
- `--jobs` → Número de procesos (0 = todos los núcleos).

---

## 📜 Formato de resultados

En la carpeta `Export/` se genera **un archivo por dominio**:
```
Export/
├── google.com.txt
├── facebook.com.txt
└── ...
```

Cada archivo contiene:
```txt
# Resultados para: google.com
Coincidencia de ejemplo en algún archivo
Otra coincidencia más
```

---

## ⚠️ Notas y consejos

- Puedes **arrastrar y soltar carpetas/archivos** en la consola para que la ruta salga exacta.
- Si tienes **millones de líneas**, la búsqueda seguirá siendo rápida gracias a Aho-Corasick.
- `Export/` está en `.gitignore` para no subir datos sensibles a GitHub.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

---

## 🤝 Contribuciones

¡Las PRs son bienvenidas!  
Puedes proponer mejoras, optimizaciones de rendimiento o nuevos formatos de salida.

---
 