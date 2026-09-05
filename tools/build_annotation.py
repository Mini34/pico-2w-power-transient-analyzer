"""Draw editable component callouts without resynthesizing the source photograph.

Requires Pillow. Run from any directory; source coordinates are in original pixels.
An SVG embeds the untouched JPEG; the PNG preserves every pixel outside the overlay.
"""
from pathlib import Path
import base64
import html
import json
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'images/sanitized/01_image-1787893448668_sanitized.jpg'
OUT = ROOT / 'images/designs'
# label, box origin, box width, leader start, exact component endpoint
CALLOUTS = [
    ('1  Pico 2 W controller', (28, 42), 298, (260, 92), (328, 225)),
    ('2  INA219 sensor', (1000, 510), 250, (1000, 550), (953, 596)),
    ('3  OLED display', (1030, 930), 240, (1030, 930), (936, 851)),
    ('4  RC / diode test area', (32, 922), 312, (240, 922), (317, 646)),
    ('5  Manual ON/OFF switch', (1020, 210), 368, (1080, 260), (1080, 380)),
]

def main():
    source = Image.open(SOURCE).convert('RGB')
    assert source.size == (1536, 1152)
    overlay = Image.new('RGBA', source.size)
    draw = ImageDraw.Draw(overlay)
    candidates = [Path('C:/Windows/Fonts/arial.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font = ImageFont.truetype(str(next(p for p in candidates if p.exists())), 25)
    navy, yellow = '#102b4e', '#ffe15b'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1152" viewBox="0 0 1536 1152">',
           '<title>Pico 2 W prototype: five component callouts</title>',
           '<desc>Original photograph with a separate editable annotation layer. Pointers identify components, not electrical terminals.</desc>',
           '<image width="1536" height="1152" href="data:image/jpeg;base64,' + base64.b64encode(SOURCE.read_bytes()).decode() + '"/>',
           '<g id="component-callouts">']
    for label, (x, y), width, start, end in CALLOUTS:
        draw.line([start, end], fill=navy, width=7)
        draw.line([start, end], fill=yellow, width=3)
        ex, ey = end
        draw.ellipse((ex-8, ey-8, ex+8, ey+8), outline=navy, width=5)
        draw.ellipse((ex-7, ey-7, ex+7, ey+7), outline=yellow, width=3)
        draw.rounded_rectangle((x, y, x+width, y+50), radius=7, fill=navy, outline='white', width=2)
        draw.text((x+13, y+11), label, font=font, fill='white')
        sx, sy = start
        svg.extend([f'<g aria-label="{html.escape(label)}">',
                    f'<path d="M {sx} {sy} L {ex} {ey}" fill="none" stroke="{navy}" stroke-width="7"/>',
                    f'<path d="M {sx} {sy} L {ex} {ey}" fill="none" stroke="{yellow}" stroke-width="3"/>',
                    f'<circle cx="{ex}" cy="{ey}" r="7" fill="none" stroke="{navy}" stroke-width="5"/>',
                    f'<circle cx="{ex}" cy="{ey}" r="7" fill="none" stroke="{yellow}" stroke-width="3"/>',
                    f'<rect x="{x}" y="{y}" width="{width}" height="50" rx="7" fill="{navy}" stroke="white" stroke-width="2"/>',
                    f'<text x="{x+13}" y="{y+34}" font-family="Arial, sans-serif" font-size="25" fill="white">{html.escape(label)}</text></g>'])
    svg.append('</g></svg>')
    result = Image.alpha_composite(source.convert('RGBA'), overlay).convert('RGB')
    OUT.mkdir(exist_ok=True)
    result.save(OUT / '01_annotated_prototype_overview.png')
    (OUT / '01_annotated_prototype_overview.svg').write_text('\n'.join(svg), encoding='utf-8')
    # Mask out the intentional annotations and demand exact source preservation.
    outside = ImageChops.invert(overlay.getchannel('A'))
    difference = ImageChops.difference(source, result)
    assert Image.composite(difference, Image.new('RGB', source.size), outside).getbbox() is None
    print(json.dumps({'callouts': len(CALLOUTS), 'source_size': source.size,
                      'outside_overlay_pixels_unchanged': True}))

if __name__ == '__main__':
    main()
