"""Render the accepted framed SVG into a Windows ICO; never redraw the artwork.

Optional asset-maintenance tool. Needs system librsvg/cairo, not a Python image dependency.
The generated icon is committed, so ordinary installer builds need no SVG renderer.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import struct
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 24, 32, 48, 64, 128, 256)


class Rectangle(ctypes.Structure):
    _fields_ = [(name, ctypes.c_double) for name in ("x", "y", "width", "height")]


def build() -> None:
    svg = (ROOT / "src/ewp_transcripts/web_assets/brand/favicon.svg").read_bytes()
    rsvg = ctypes.CDLL(ctypes.util.find_library("rsvg-2"))
    cairo = ctypes.CDLL(ctypes.util.find_library("cairo"))
    gobject = ctypes.CDLL(ctypes.util.find_library("gobject-2.0"))
    rsvg.rsvg_handle_new_from_data.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_void_p]
    rsvg.rsvg_handle_new_from_data.restype = ctypes.c_void_p
    rsvg.rsvg_handle_render_document.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(Rectangle),
        ctypes.c_void_p,
    ]
    cairo.cairo_image_surface_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    cairo.cairo_image_surface_create.restype = ctypes.c_void_p
    cairo.cairo_create.argtypes = [ctypes.c_void_p]
    cairo.cairo_create.restype = ctypes.c_void_p
    cairo.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    cairo.cairo_destroy.argtypes = cairo.cairo_surface_destroy.argtypes = [ctypes.c_void_p]
    gobject.g_object_unref.argtypes = [ctypes.c_void_p]
    handle = rsvg.rsvg_handle_new_from_data(svg, len(svg), None)
    if not handle:
        raise ValueError("Cannot read the original framed vector")
    images = []
    with tempfile.TemporaryDirectory(prefix="ewp-icon-") as temporary:
        for size in SIZES:
            surface = cairo.cairo_image_surface_create(0, size, size)
            context = cairo.cairo_create(surface)
            rectangle = Rectangle(0, 0, size, size)
            if not rsvg.rsvg_handle_render_document(handle, context, ctypes.byref(rectangle), None):
                raise ValueError("SVG rendering failed")
            path = Path(temporary) / f"{size}.png"
            if cairo.cairo_surface_write_to_png(surface, str(path).encode()):
                raise ValueError("Icon encoding failed")
            images.append(path.read_bytes())
            cairo.cairo_destroy(context)
            cairo.cairo_surface_destroy(surface)
    gobject.g_object_unref(handle)
    offset = 6 + 16 * len(SIZES)
    entries = []
    for size, data in zip(SIZES, images, strict=True):
        entries.append(
            struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        )
        offset += len(data)
    (ROOT / "installer/windows/EwP.ico").write_bytes(
        struct.pack("<HHH", 0, 1, len(SIZES)) + b"".join(entries + images)
    )


if __name__ == "__main__":
    build()
