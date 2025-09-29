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
```

 Nota: `PyMuPDF` es el nombre del paquete en PyPI, pero se importa como `fitz`.

## Uso

```bash
python pdfcrop.py input.pdf [opciones]
```

### Argumentos
| ARGUMENTO | DESCRIPCIÓN | VALOR POR DEFECTO |
| --- | --- | --- |
| input.pdf | Archivo PDF de entrada | — |
| -o, --output | Archivo de salida | input_cropped.pdf |
| --dpi | Resolución de análisis (DPI) | 200 |
| --threshold | Umbral de intensidad (0–255). Valores más bajos = más sensible | 245 |
| --margin | Margen adicional (admite pt, mm, cm, in, px) | 4mm |
| --quiet | Suprime mensajes de progreso | — |

## Ejemplos de uso

### Forma básica
```bash
python pdfcrop.py documento.pdf
```

### Personalizar margen y umbral
```bash
python pdfcrop.py escaneo.pdf --margin "10px" --threshold 230 --dpi 300
```

### Guardar con nombre específico
```bash
python pdfcrop.py libro.pdf -o libro_limpio.pdf --margin "0.2in"
```

## Cómo funciona
1. Cada página del PDF se convierte en una imagen en escala de grises a la resolución especificada (dpi).
2. Se identifican los píxeles cuyo valor es menor que el threshold (considerados "contenido").
3. Se calcula el rectángulo mínimo que contiene todo el contenido detectado.
4. Se ajusta el cropbox de la página PDF a ese rectángulo, añadiendo el margen solicitado (convertido a puntos PDF).
5. Las páginas sin contenido detectado se dejan sin cambios.

> El proceso no modifica el contenido original (texto, vectores, imágenes), solo redefine el área visible de cada página.

## Licencia
Este proyecto es de código abierto y está disponible bajo la licencia MIT.
