# pdfcrop
Recorta los márgenes en blanco de archivos PDF

Herramienta de línea de comandos para recortar automáticamente los márgenes en blanco de documentos PDF, página por página, conservando un margen configurable alrededor del contenido real.

Ideal para limpiar escaneos, ajustar documentos con márgenes excesivos o preparar PDFs para impresión o lectura en dispositivos con pantallas pequeñas.

---

## Características

- **Detección inteligente de contenido**: rasteriza cada página y encuentra el cuadro delimitador del contenido no blanco.
- **Margen personalizable**: define el espacio adicional a conservar alrededor del contenido (admite unidades: `pt`, `mm`, `cm`, `in`, `px`).
- **Resolución ajustable**: controla la precisión del análisis mediante DPI (por defecto: 200).
- **Umbral configurable**: ajusta la sensibilidad para distinguir entre "contenido" y "fondo blanco".
- **No modifica páginas en blanco**: las deja intactas.
- **Salida optimizada**: guarda el PDF resultante con compresión y limpieza de recursos no usados.

---

## Requisitos

- Python 3.7+
- Dependencias:
  - [`PyMuPDF`](https://pymupdf.readthedocs.io/) (`fitz`)
  - [`NumPy`](https://numpy.org/)

Instálalas con:

```bash
pip install PyMuPDF numpy```

 Nota: `PyMuPDF` es el nombre del paquete en PyPI, pero se importa como `fitz`.

## Uso

```python pdfcrop.py input.pdf [opciones]```

# Uso básico
`python pdf_crop_margins.py documento.pdf`

# Personalizar margen y umbral
`python pdf_crop_margins.py escaneo.pdf --margin "10px" --threshold 230 --dpi 300`

# Guardar con nombre específico
`python pdf_crop_margins.py libro.pdf -o libro_limpio.pdf --margin "0.2in"`
