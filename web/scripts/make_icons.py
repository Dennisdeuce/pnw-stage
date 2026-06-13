"""Generate brand PWA icons with no external deps (stdlib zlib/struct only).

Design: evergreen-black field, an amber marquee bar, and a coral stage block —
the same primitives as the app's signature. Run: python scripts/make_icons.py
"""
import struct
import zlib
from pathlib import Path

BG = (11, 15, 13, 255)      # ink-900
AMBER = (245, 181, 68, 255) # marquee bulbs bar
CORAL = (255, 90, 60, 255)  # stage block


def render(size: int) -> bytes:
    px = bytearray()
    bar_top, bar_bot = int(size * 0.20), int(size * 0.26)
    stage_l, stage_r = int(size * 0.22), int(size * 0.78)
    stage_t, stage_b = int(size * 0.40), int(size * 0.74)
    for y in range(size):
        px.append(0)  # PNG filter type 0 for each scanline
        for x in range(size):
            if bar_top <= y <= bar_bot and int(size * 0.14) <= x <= int(size * 0.86):
                c = AMBER
            elif stage_l <= x <= stage_r and stage_t <= y <= stage_b:
                c = CORAL
            else:
                c = BG
            px.extend(c)
    return bytes(px)


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(
        ">I", zlib.crc32(tag + data) & 0xFFFFFFFF
    )


def png(size: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = zlib.compress(render(size), 9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "public"
    out.mkdir(exist_ok=True)
    for s in (192, 512):
        (out / f"icon-{s}.png").write_bytes(png(s))
        print(f"wrote public/icon-{s}.png")
