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
pip install PyMuPDF numpy
