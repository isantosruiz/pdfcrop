from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable

import fitz
from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename


MAX_UPLOAD_MB = 40
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
RASTER_DPI = 144
WHITE_THRESHOLD = 250

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


INDEX_HTML = """
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>pdfcrop</title>
    <style>
      :root {
        --bg: #f3f6f4;
        --card: #ffffff;
        --text: #17221f;
        --muted: #4f5d58;
        --accent: #0a7f5a;
        --accent-hover: #08684a;
        --border: #d7e3dd;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at 12% 12%, #d9efe5 0%, transparent 46%),
          radial-gradient(circle at 88% 86%, #d6e8ff 0%, transparent 41%),
          var(--bg);
        display: grid;
        place-items: center;
        padding: 24px;
      }
      .card {
        width: min(680px, 100%);
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 28px;
        box-shadow: 0 14px 40px rgba(9, 26, 20, 0.08);
      }
      h1 {
        margin: 0 0 10px;
        font-size: clamp(1.8rem, 4vw, 2.4rem);
        letter-spacing: 0.01em;
      }
      p {
        margin: 0 0 18px;
        line-height: 1.5;
        color: var(--muted);
      }
      form {
        display: grid;
        gap: 12px;
      }
      input[type="file"] {
        border: 1px dashed var(--border);
        border-radius: 12px;
        padding: 14px;
        font: inherit;
        background: #fbfdfc;
      }
      button {
        border: 0;
        border-radius: 12px;
        padding: 14px 16px;
        font-size: 1rem;
        font-weight: 600;
        color: #fff;
        background: var(--accent);
        cursor: pointer;
      }
      button:hover { background: var(--accent-hover); }
      .error {
        margin: 4px 0 2px;
        color: #a8312e;
        font-weight: 600;
      }
      .help {
        font-size: 0.92rem;
        margin-top: 6px;
      }
    </style>
  </head>
  <body>
    <main class="card">
      <h1>pdfcrop</h1>
      <p>Sube un PDF y se eliminarán automáticamente los márgenes vacíos de cada página.</p>
      {% if error %}
        <div class="error">{{ error }}</div>
      {% endif %}
      <form method="post" action="/crop" enctype="multipart/form-data">
        <input type="file" name="pdf_file" accept="application/pdf,.pdf" required />
        <button type="submit">Recortar y descargar</button>
      </form>
      <p class="help">Tamaño máximo del archivo: {{ max_upload_mb }} MB.</p>
    </main>
    <div id="copyright">
        <p>&copy; 2026, <a href="https://isantosruiz.github.io/home/" style="text-decoration: none;">Ildeberto de los Santos Ruiz</a></p>
    </div>
  </body>
</html>
"""


def rect_almost_equal(a: fitz.Rect, b: fitz.Rect, tol: float = 0.5) -> bool:
    return (
        abs(a.x0 - b.x0) <= tol
        and abs(a.y0 - b.y0) <= tol
        and abs(a.x1 - b.x1) <= tol
        and abs(a.y1 - b.y1) <= tol
    )


def union_rects(rects: Iterable[fitz.Rect]) -> fitz.Rect | None:
    rects = list(rects)
    if not rects:
        return None
    merged = fitz.Rect(rects[0])
    for rect in rects[1:]:
        merged.include_rect(rect)
    return merged


def clamp_rect(content_rect: fitz.Rect, bounds: fitz.Rect, padding: float = 0.0) -> fitz.Rect:
    padded = fitz.Rect(
        content_rect.x0 - padding,
        content_rect.y0 - padding,
        content_rect.x1 + padding,
        content_rect.y1 + padding,
    )
    return padded & bounds


def detect_bbox_from_objects(page: fitz.Page) -> fitz.Rect | None:
    rects: list[fitz.Rect] = []

    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        bbox = block.get("bbox")
        if not bbox:
            continue
        rect = fitz.Rect(bbox)
        if rect.is_empty or rect.get_area() <= 0:
            continue
        rects.append(rect)

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if not rect:
            continue
        drawing_rect = fitz.Rect(rect)
        if drawing_rect.is_empty or drawing_rect.get_area() <= 0:
            continue
        rects.append(drawing_rect)

    annots = page.annots()
    if annots:
        for annot in annots:
            annot_rect = fitz.Rect(annot.rect)
            if annot_rect.is_empty or annot_rect.get_area() <= 0:
                continue
            rects.append(annot_rect)

    return union_rects(rects)


def detect_bbox_from_raster(
    page: fitz.Page,
    threshold: int = WHITE_THRESHOLD,
    dpi: int = RASTER_DPI,
) -> fitz.Rect | None:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY, alpha=False)

    width = pix.width
    height = pix.height
    samples = pix.samples

    left = width
    top = height
    right = -1
    bottom = -1

    for y in range(height):
        row_start = y * width
        row = samples[row_start : row_start + width]
        for x, value in enumerate(row):
            if value >= threshold:
                continue
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)

    if right < left or bottom < top:
        return None

    page_rect = page.rect
    px_to_pt_x = page_rect.width / width
    px_to_pt_y = page_rect.height / height

    return fitz.Rect(
        page_rect.x0 + left * px_to_pt_x,
        page_rect.y0 + top * px_to_pt_y,
        page_rect.x0 + (right + 1) * px_to_pt_x,
        page_rect.y0 + (bottom + 1) * px_to_pt_y,
    )


def detect_content_bbox(page: fitz.Page) -> fitz.Rect | None:
    bbox = detect_bbox_from_objects(page)
    if bbox and bbox.get_area() > 0:
        return bbox
    return detect_bbox_from_raster(page)


def crop_pdf_bytes(pdf_bytes: bytes, padding: float = 0.0) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        try:
            page_bounds = fitz.Rect(page.rect)
            content_bbox = detect_content_bbox(page)
            if not content_bbox:
                continue

            target = clamp_rect(content_bbox, page_bounds, padding=padding)
            if target.is_empty or target.get_area() <= 1:
                continue
            if rect_almost_equal(target, page_bounds):
                continue

            # CropBox is enough to visually trim the page and avoids
            # MediaBox/CropBox consistency issues in some PDFs.
            page.set_cropbox(target)
        except Exception:
            # Skip problematic pages and continue processing the rest.
            continue

    output = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return output


@app.get("/")
def index():
    return render_template_string(INDEX_HTML, error=None, max_upload_mb=MAX_UPLOAD_MB)


@app.errorhandler(413)
def payload_too_large(_):
    return (
        render_template_string(
            INDEX_HTML,
            error=f"El archivo supera el límite de {MAX_UPLOAD_MB} MB.",
            max_upload_mb=MAX_UPLOAD_MB,
        ),
        413,
    )


@app.post("/crop")
def crop():
    uploaded = request.files.get("pdf_file")
    if not uploaded or not uploaded.filename:
        return (
            render_template_string(
                INDEX_HTML,
                error="Selecciona un archivo PDF.",
                max_upload_mb=MAX_UPLOAD_MB,
            ),
            400,
        )

    filename = uploaded.filename
    if not filename.lower().endswith(".pdf"):
        return (
            render_template_string(
                INDEX_HTML,
                error="El archivo debe tener extensión .pdf.",
                max_upload_mb=MAX_UPLOAD_MB,
            ),
            400,
        )

    raw_pdf = uploaded.read()
    if not raw_pdf:
        return (
            render_template_string(
                INDEX_HTML,
                error="El archivo está vacío o no se pudo leer.",
                max_upload_mb=MAX_UPLOAD_MB,
            ),
            400,
        )

    try:
        cropped_pdf = crop_pdf_bytes(raw_pdf)
    except Exception as exc:
        app.logger.exception("Error while processing PDF")
        debug_detail = f" ({exc})" if app.debug else ""
        return (
            render_template_string(
                INDEX_HTML,
                error=f"No se pudo procesar el PDF. Verifica que sea un archivo válido.{debug_detail}",
                max_upload_mb=MAX_UPLOAD_MB,
            ),
            400,
        )

    safe_name = Path(secure_filename(filename)).stem or "document"
    output_name = f"{safe_name}_cropped.pdf"
    return send_file(
        BytesIO(cropped_pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=output_name,
    )


if __name__ == "__main__":
    app.run(debug=True)
