#!/usr/bin/env python3
"""
Genera i post "brand/fiducia" (non legati a un singolo annuncio) per
Immobiliare Malfatti: prende i temi da data/brand_topics.json, scarica la
foto di sfondo indicata, ci sovrappone il template con la bolla del brand
e il testo della domanda, e produce un feed RSS separato
(docs/brand-feed.xml) da collegare a Postpikr.

A differenza dello scraper degli annunci, questo script NON gira in
automatico ogni settimana: è pensato per essere lanciato manualmente
quando si aggiungono nuovi temi a data/brand_topics.json. I post generati
sono pensati per essere salvati e riusati nel tempo su Postpikr.
"""

import json
import re
import sys
import textwrap
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

import requests
from feedgen.feed import FeedGenerator
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
PAGES_BASE_URL = "https://marketingimmobiliaremalfatti-max.github.io/postcreati/"

TEMPLATE_PATH = BASE_DIR / "assets" / "template_brand.png"
FONT_PATH = BASE_DIR / "assets" / "fonts" / "Poppins-Bold.ttf"
TOPICS_FILE = BASE_DIR / "data" / "brand_topics.json"
IMAGES_DIR = BASE_DIR / "docs" / "brand-images"
OUTPUT_FILE = BASE_DIR / "docs" / "brand-feed.xml"

TEXT_BOX = (110, 130, 950, 850)  # left, top, right, bottom
TEXT_COLOR = (255, 255, 255)
MAX_FONT_SIZE = 150
MIN_FONT_SIZE = 60
LINE_SPACING_RATIO = 0.2  # spazio tra le righe, proporzionale alla dimensione del font

# Rimuove gli emoji dal testo scritto SOPRA la foto: il font usato per il
# disegno (Poppins) non contiene i glifi emoji, quindi comparirebbe un
# quadratino vuoto. L'emoji resta comunque nel testo del post (caption),
# dove viene mostrato come testo normale da Facebook/Instagram.
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002300-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)


def strip_emoji(text):
    return EMOJI_PATTERN.sub("", text).strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MalfattiBrandBot/1.0)"
}


def fit_text_in_box(draw, text, max_width, max_height):
    """Trova la dimensione di font più grande (tra MIN e MAX_FONT_SIZE) che
    permette al testo, andando a capo, di stare dentro la box disponibile.
    Restituisce (font, lines, line_height)."""
    for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -4):
        font = ImageFont.truetype(str(FONT_PATH), size)
        lines = wrap_text_to_fit(draw, text, font, max_width)
        line_height = font.getbbox("Ag")[3] + int(size * LINE_SPACING_RATIO)
        total_height = line_height * len(lines)
        if total_height <= max_height:
            return font, lines, line_height

    font = ImageFont.truetype(str(FONT_PATH), MIN_FONT_SIZE)
    lines = wrap_text_to_fit(draw, text, font, max_width)
    line_height = font.getbbox("Ag")[3] + int(MIN_FONT_SIZE * LINE_SPACING_RATIO)
    return font, lines, line_height


def wrap_text_to_fit(draw, text, font, max_width):
    """Va a capo automaticamente in base alla larghezza reale del testo
    (non solo al numero di caratteri), per gestire bene anche gli emoji."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def compose_brand_image(topic):
    out_filename = f"{topic['id']}.jpg"
    out_path = IMAGES_DIR / out_filename

    if out_path.exists():
        return urljoin(PAGES_BASE_URL, f"brand-images/{out_filename}")

    if not TEMPLATE_PATH.exists():
        print(f"  [!] Template brand non trovato in {TEMPLATE_PATH}", file=sys.stderr)
        return None

    try:
        resp = requests.get(topic["image_url"], headers=HEADERS, timeout=30)
        resp.raise_for_status()
        photo = Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception as e:
        print(f"  [!] Errore scaricando la foto per {topic['id']}: {e}", file=sys.stderr)
        return None

    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    canvas_w, canvas_h = template.size

    photo_ratio = photo.width / photo.height
    canvas_ratio = canvas_w / canvas_h
    if photo_ratio > canvas_ratio:
        new_height = canvas_h
        new_width = int(new_height * photo_ratio)
    else:
        new_width = canvas_w
        new_height = int(new_width / photo_ratio)
    photo_resized = photo.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - canvas_w) // 2
    top = (new_height - canvas_h) // 2
    photo_cropped = photo_resized.crop((left, top, left + canvas_w, top + canvas_h))

    canvas = photo_cropped.convert("RGBA")
    canvas.alpha_composite(template)

    draw = ImageDraw.Draw(canvas)
    box_left, box_top, box_right, box_bottom = TEXT_BOX
    max_width = box_right - box_left
    max_height = box_bottom - box_top

    quote_for_image = strip_emoji(topic["quote"])
    font, lines, line_height = fit_text_in_box(draw, quote_for_image, max_width, max_height)

    total_height = line_height * len(lines)
    y = box_top + max(0, (max_height - total_height) // 2)

    for line in lines:
        draw.text((box_left, y), line, font=font, fill=TEXT_COLOR)
        y += line_height

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "JPEG", quality=90)

    return urljoin(PAGES_BASE_URL, f"brand-images/{out_filename}")


def build_feed(topics_with_images):
    fg = FeedGenerator()
    fg.title("Immobiliare Malfatti - Post Brand")
    fg.link(href=PAGES_BASE_URL, rel="alternate")
    fg.description("Post di fiducia/marketing (non legati a singoli annunci) per Immobiliare Malfatti")
    fg.language("it")

    for topic, image_url in topics_with_images:
        fe = fg.add_entry()
        fe.id(f"{PAGES_BASE_URL}brand/{topic['id']}")
        fe.title(topic["quote"])
        fe.link(href=PAGES_BASE_URL)
        fe.guid(f"{PAGES_BASE_URL}brand/{topic['id']}", permalink=False)

        desc_html = topic["caption"].replace("\n", "<br/>\n")
        if image_url:
            desc_html = f'<img src="{image_url}" /><br/>{desc_html}'
        fe.description(desc_html)

        if image_url:
            try:
                fe.enclosure(image_url, 0, "image/jpeg")
            except Exception:
                pass

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(OUTPUT_FILE), pretty=True)


def main():
    if not TOPICS_FILE.exists():
        print(f"File temi non trovato: {TOPICS_FILE}", file=sys.stderr)
        sys.exit(1)

    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    print(f"Temi trovati: {len(topics)}")

    topics_with_images = []
    for topic in topics:
        print(f"== {topic['id']}: {topic['quote']!r} ==")
        image_url = compose_brand_image(topic)
        if image_url:
            print(f"  Immagine: {image_url}")
        else:
            print("  [!] Nessuna immagine generata, il post userà solo il testo")
        topics_with_images.append((topic, image_url))

    build_feed(topics_with_images)
    print(f"Feed brand scritto in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
