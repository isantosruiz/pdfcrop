# -*- coding: utf-8 -*-
"""
Herramienta para recortar márgenes en blanco de documentos PDF página por página.

Este script analiza cada página de un PDF, detecta el contenido no blanco mediante
rasterización a una resolución especificada (DPI), calcula el cuadro delimitador
(bounding box) del contenido y ajusta el cropbox de la página para eliminar
márgenes innecesarios, conservando un margen configurable.

Dependencias:
    - PyMuPDF (fitz)
    - NumPy
"""

import argparse
import re
import sys
import fitz  # PyMuPDF
import numpy as np


def parse_length_to_points(s: str, dpi: int) -> float:
    """Convierte una longitud con unidad a puntos PDF (pt).

    Soporta las siguientes unidades:
        - `pt`: puntos (1 pt = 1/72 pulgada)
        - `mm`: milímetros
        - `cm`: centímetros
        - `in`, `inch`, `inches`: pulgadas
        - `px`: píxeles (requiere especificar `dpi`)

    Si no se especifica unidad, se asume `pt`.

    Args:
        s (str): Cadena que representa la longitud (ej. "10mm", "2in", "150").
        dpi (int): Resolución en puntos por pulgada, usada solo si la unidad es "px".

    Returns:
        float: Longitud equivalente en puntos PDF (pt).

    Raises:
        ValueError: Si la cadena no tiene un formato válido o la unidad no es soportada.
        ValueError: Si se usa "px" sin proporcionar un valor válido de `dpi`.

    Examples:
        >>> parse_length_to_points("10mm", 300)
        28.346456692913385
        >>> parse_length_to_points("1in", 300)
        72.0
        >>> parse_length_to_points("150", 300)
        150.0
    """
    s = s.strip().lower()
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([a-z]*)\s*$", s)
    if not m:
        raise ValueError(f"Longitud inválida: {s}")
    val = float(m.group(1))
    unit = m.group(2) or "pt"
    if unit == "pt":
        return val
    if unit == "mm":
        return val * 72.0 / 25.4
    if unit == "cm":
        return val * 72.0 / 2.54
    if unit in ("in", "inch", "inches"):
        return val * 72.0
    if unit == "px":
        if not dpi:
            raise ValueError("Para 'px' se requiere --dpi.")
        return val * (72.0 / dpi)
    raise ValueError(f"Unidad no soportada: {unit}")


def find_content_bbox(pix: fitz.Pixmap, threshold: int) -> tuple | None:
    """Encuentra el cuadro delimitador (bounding box) del contenido no blanco en un pixmap en escala de grises.

    El contenido se define como cualquier píxel cuyo valor sea **menor** que `threshold`
    (0 = negro, 255 = blanco). Se asume que el pixmap está en modo GRAY (sin canal alfa).

    Args:
        pix (fitz.Pixmap): Pixmap en escala de grises (debe tener `pix.n == 1`).
        threshold (int): Umbral de intensidad (0–255). Valores menores se consideran contenido.

    Returns:
        tuple | None: Una tupla `(left, top, right, bottom)` en coordenadas de píxeles,
                      o `None` si no se detecta contenido (página en blanco).

    Raises:
        ValueError: Si el pixmap no está en escala de grises (`pix.n != 1`).

    Examples:
        >>> doc = fitz.open("ejemplo.pdf")
        >>> page = doc[0]
        >>> mat = fitz.Matrix(200/72, 200/72)
        >>> pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY, alpha=False)
        >>> bbox = find_content_bbox(pix, threshold=245)
        >>> print(bbox)  # Ej: (10, 20, 500, 700)
    """
    if pix.n != 1:
        raise ValueError("El Pixmap debe ser en escala de grises (n=1).")
    h, w = pix.height, pix.width
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w)
    mask = arr < np.uint8(threshold)
    if not mask.any():
        return None
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    top, bottom = int(rows[0]), int(rows[-1])
    left, right = int(cols[0]), int(cols[-1])
    return left, top, right, bottom


def crop_pdf(
    input_path: str,
    output_path: str,
    dpi: int,
    threshold: int,
    margin_pt: float,
    quiet: bool
) -> None:
    """Recorta las páginas de un PDF eliminando márgenes en blanco.

    Cada página se rasteriza a la resolución especificada (`dpi`), se detecta el
    contenido no blanco usando un umbral de intensidad, y se ajusta el `cropbox`
    de la página para ajustarse al contenido más un margen adicional.

    Args:
        input_path (str): Ruta al archivo PDF de entrada.
        output_path (str): Ruta donde se guardará el PDF recortado.
        dpi (int): Resolución de rasterización (puntos por pulgada).
        threshold (int): Umbral para distinguir contenido de fondo (0–255).
        margin_pt (float): Margen adicional a conservar alrededor del contenido, en puntos PDF.
        quiet (bool): Si es `True`, suprime la salida por consola.

    Side Effects:
        - Guarda un nuevo archivo PDF en `output_path`.
        - Imprime progreso en consola si `quiet=False`.

    Notes:
        - Las coordenadas en MuPDF tienen el origen en la esquina superior izquierda.
        - El margen se aplica en puntos PDF, no en píxeles.
        - Las páginas completamente en blanco se dejan sin modificar.
    """
    doc = fitz.open(input_path)
    scale = 72.0 / dpi  # Conversión: píxel -> punto PDF

    pages_cropped = 0
    for i, page in enumerate(doc, start=1):
        # Renderizar página en escala de grises sin canal alfa
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY, alpha=False)
        bbox_px = find_content_bbox(pix, threshold=threshold)

        if bbox_px is None:
            if not quiet:
                print(f"[{i}/{len(doc)}] Página en blanco aparente: sin recorte.")
            continue

        left_px, top_px, right_px, bottom_px = bbox_px

        # Convertir a puntos PDF y aplicar margen
        x0 = max(0.0, left_px * scale - margin_pt)
        y0 = max(0.0, top_px * scale - margin_pt)
        x1 = min(page.rect.width, (right_px + 1) * scale + margin_pt)
        y1 = min(page.rect.height, (bottom_px + 1) * scale + margin_pt)

        # Validar rectángulo resultante
        if x1 <= x0 or y1 <= y0:
            if not quiet:
                print(f"[{i}/{len(doc)}] Bounding box degenerado, se omite.")
            continue

        new_rect = fitz.Rect(x0, y0, x1, y1)
        page.set_cropbox(new_rect)
        pages_cropped += 1
        if not quiet:
            print(f"[{i}/{len(doc)}] Recortada a {new_rect} (margen {margin_pt:.2f} pt).")

    if pages_cropped == 0 and not quiet:
        print("No se aplicaron recortes. ¿Umbral muy bajo/alto o páginas realmente en blanco?")

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
    if not quiet:
        print(f"Guardado: {output_path}")


def main() -> None:
    """Punto de entrada principal del script.

    Procesa los argumentos de línea de comandos, valida entradas y ejecuta el recorte del PDF.

    Argumentos de línea de comandos:
        input (str): Archivo PDF de entrada.
        -o, --output (str, opcional): Archivo de salida. Por defecto: `<input>_cropped.pdf`.
        --dpi (int, opcional): DPI para rasterización. Por defecto: 200.
        --threshold (int, opcional): Umbral de detección de contenido (0–255). Por defecto: 245.
        --margin (str, opcional): Margen adicional (admite unidades: pt, mm, cm, in, px). Por defecto: "4mm".
        --quiet (flag): Suprime mensajes de progreso.

    Salidas:
        - Archivo PDF recortado.
        - Mensajes de estado en stderr/stdout (a menos que se use --quiet).

    Código de salida:
        - 0: Éxito.
        - 2: Error en argumentos o validación.
    """
    ap = argparse.ArgumentParser(
        description="Recorta un PDF eliminando márgenes en blanco por página."
    )
    ap.add_argument("input", help="PDF de entrada")
    ap.add_argument("-o", "--output", default=None, help="PDF de salida (por defecto: *_cropped.pdf)")
    ap.add_argument("--dpi", type=int, default=200, help="DPI para rasterizado (por defecto: 200)")
    ap.add_argument(
        "--threshold", type=int, default=245,
        help="Umbral 0–255: menor es 'contenido'. 245 suele ir bien (por defecto: 245)"
    )
    ap.add_argument(
        "--margin", default="4mm",
        help="Margen extra a conservar (pt, mm, cm, in, px). Por defecto: 4mm"
    )
    ap.add_argument("--quiet", action="store_true", help="Menos salida por consola")
    args = ap.parse_args()

    out = args.output or re.sub(r"\.pdf$", "", args.input, flags=re.I) + "_cropped.pdf"
    try:
        margin_pt = parse_length_to_points(args.margin, dpi=args.dpi)
    except Exception as e:
        print(f"Error en --margin: {e}", file=sys.stderr)
        sys.exit(2)

    if not (0 <= args.threshold <= 255):
        print("El --threshold debe estar entre 0 y 255.", file=sys.stderr)
        sys.exit(2)

    crop_pdf(args.input, out, dpi=args.dpi, threshold=args.threshold, margin_pt=margin_pt, quiet=args.quiet)


if __name__ == "__main__":
    main()