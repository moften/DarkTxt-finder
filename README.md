# 🕵️‍♂️ DarkTxt-finder

```
░  ░░░░░░░░        ░░░      ░░░  ░░░░  ░
▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒  ▒▒
▓  ▓▓▓▓▓▓▓▓      ▓▓▓▓  ▓▓▓▓  ▓▓     ▓▓▓▓
█  ████████  ████████        ██  ███  ██
█        ██        ██  ████  ██  ████  █
                                        
by m10sec m10sec@proton.mx
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
- Compatible con macOS, Linux y Windows.

---

## 📦 Requisitos

El único paquete externo necesario es:

```txt
pyahocorasick>=2.0.0
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
