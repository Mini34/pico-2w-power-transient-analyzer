"""Build a photo-faithful annotated overview from two original project photos.

The overview and resistor close-up are not resynthesized. Labels identify whole
components, not electrical terminals or a verified wiring path.
"""

from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "images/sanitized/01_image-1787893448668_sanitized.jpg"
RESISTOR = ROOT / "images/sanitized/08_image-1787893496016_sanitized.jpg"
CAPACITOR = ROOT / "images/sanitized/03_image-1787893461592_sanitized.jpg"
OUTPUT = ROOT / "images/designs/02_annotated_physical_prototype.webp"

NAVY = "#102b4e"
GOLD = "#ffe15b"
WHITE = "#ffffff"
PANEL = "#e8f1f4"
SIZE = (2048, 1152)

# Text, box x/y/width, leader origin and endpoint on the photographed component.
CALLOUTS = [
    ("Pico 2 W controller", (28, 42, 316), (265, 93), (328, 225)),
    ("1000 µF capacitor", (24, 422, 310), (294, 474), (297, 520)),
    ("INA219 sensor", (1000, 507, 255), (1000, 554), (953, 596)),
    ("OLED display", (1030, 930, 242), (1030, 930), (936, 851)),
    ("Manual ON/OFF switch", (1019, 210, 363), (1080, 260), (1080, 380)),
]


def font(size):
    for path in (Path("C:/Windows/Fonts/arial.ttf"),
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("A legible TrueType font is required")


def callout(draw, label, box, origin, target, label_font):
    x, y, width = box
    draw.line((origin, target), fill=NAVY, width=7)
    draw.line((origin, target), fill=GOLD, width=3)
    tx, ty = target
    draw.ellipse((tx-8, ty-8, tx+8, ty+8), outline=NAVY, width=5)
    draw.ellipse((tx-7, ty-7, tx+7, ty+7), outline=GOLD, width=3)
    draw.rounded_rectangle((x, y, x+width, y+54), radius=8, fill=NAVY,
                           outline=WHITE, width=2)
    draw.text((x+12, y+12), label, font=label_font, fill=WHITE)


def main():
    overview = Image.open(OVERVIEW).convert("RGB")
    resistor = Image.open(RESISTOR).convert("RGB")
    capacitor = Image.open(CAPACITOR).convert("RGB")
    assert overview.size == (1536, 1152)
    assert resistor.size == (1152, 1536)
    assert capacitor.size == (1152, 1536)

    canvas = Image.new("RGB", SIZE, PANEL)
    canvas.paste(overview, (0, 0))
    # Original close-ups resolve two components that are small or cropped in
    # the overview; the pixels are cropped/resized, never reconstructed.
    cap_detail = capacitor.crop((260, 460, 900, 1040)).resize(
        (440, 399), Image.Resampling.LANCZOS)
    load_detail = resistor.crop((370, 220, 1050, 940)).resize(
        (440, 466), Image.Resampling.LANCZOS)
    cap_inset, load_inset = (1572, 103), (1572, 598)
    canvas.paste(cap_detail, cap_inset)
    canvas.paste(load_detail, load_inset)
    draw = ImageDraw.Draw(canvas)
    for x, y, detail in ((cap_inset[0], cap_inset[1], cap_detail),
                         (load_inset[0], load_inset[1], load_detail)):
        draw.rectangle((x-3, y-3, x+detail.width+3, y+detail.height+3),
                       outline=NAVY, width=5)
    draw.text((1573, 36), "1000 µF capacitor · close-up", font=font(27), fill=NAVY)
    draw.text((1573, 535), "10 Ω · 100 W load resistor", font=font(27), fill=NAVY)
    draw.text((1573, 1090), "Insets: original project photographs", font=font(21), fill=NAVY)
    for label, box, origin, target in CALLOUTS:
        callout(draw, label, box, origin, target, font(26))

    # Short leaders from the inset headings to the photographed component body.
    for origin, target in (((1750, 79), (1737, 296)),
                           ((1780, 577), (1818, 819))):
        draw.line((origin, target), fill=NAVY, width=7)
        draw.line((origin, target), fill=GOLD, width=3)
        tx, ty = target
        draw.ellipse((tx-8, ty-8, tx+8, ty+8), outline=NAVY, width=5)
        draw.ellipse((tx-7, ty-7, tx+7, ty+7), outline=GOLD, width=3)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, format="WEBP", quality=92, method=6)
    # The photograph is unchanged beyond the drawn leader/label overlay.
    base = Image.new("RGB", SIZE, PANEL)
    base.paste(overview, (0, 0))
    base.paste(cap_detail, cap_inset)
    base.paste(load_detail, load_inset)
    assert ImageChops.difference(base.crop((350, 0, 900, 400)),
                                 canvas.crop((350, 0, 900, 400))).getbbox() is None
    print(json.dumps({"size": SIZE,
                      "photo_sources": [OVERVIEW.name, CAPACITOR.name, RESISTOR.name],
                      "labels": len(CALLOUTS)+2, "output": str(OUTPUT)}))


if __name__ == "__main__":
    main()
