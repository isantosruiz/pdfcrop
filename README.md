# pdfcrop

Aplicación web en Python para recortar márgenes vacíos (sin contenido) en páginas PDF.

## Qué hace

- Permite subir un archivo PDF desde el navegador.
- Detecta el área con contenido en cada página.
- Ajusta el PDF eliminando márgenes vacíos.
- Descarga automáticamente un nuevo archivo con sufijo `_cropped.pdf`.

## Stack

- Python + Flask
- PyMuPDF (`fitz`) para análisis y recorte de páginas PDF
- Preparado para despliegue en Vercel

## Ejecutar en local

1. Crear entorno e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Levantar servidor:

```bash
flask --app api/index.py run --debug
```

3. Abrir:

```text
http://127.0.0.1:5000
```

## Despliegue en Vercel

1. Sube este proyecto a un repositorio Git.
2. Importa el repositorio en Vercel.
3. Vercel detectará `vercel.json` y desplegará `api/index.py` como función Python.

## Notas técnicas

- Primero intenta detectar contenido por objetos PDF (texto, imágenes, trazos y anotaciones).
- Si no encuentra contenido por objetos, usa fallback rasterizado en escala de grises para detectar píxeles no blancos.
- Tamaño máximo de subida configurado: 40 MB.
