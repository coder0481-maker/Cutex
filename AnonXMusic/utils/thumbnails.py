import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def changeImageSize(maxWidth, maxHeight, image):
    ratio = min(maxWidth / image.size[0], maxHeight / image.size[1])
    return image.resize(
        (int(image.size[0] * ratio), int(image.size[1] * ratio))
    )


def fit_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    while draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]
    return text + "..."


def rounded_rectangle(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


async def get_thumb(videoid, user_id):
    try:
        path = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(path):
            return path

        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        result = (await search.next())["result"][0]

        title = result.get("title", "Unknown Title")
        title = " ".join(title.split()[:4])  # max 3–4 words
        duration = result.get("duration", "00:00")
        channel = result.get("channel", {}).get("name", "")
        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open("cache/temp.png", "wb") as f:
                    await f.write(await r.read())

        yt = Image.open("cache/temp.png").convert("RGBA")

        base = changeImageSize(1280, 720, yt)
        bg = base.filter(ImageFilter.GaussianBlur(15))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)

        draw = ImageDraw.Draw(bg)

        # 🎵 PLAYER BAR
        bar_x1, bar_y1 = 220, 160
        bar_x2, bar_y2 = 1060, 520
        rounded_rectangle(
            draw,
            (bar_x1, bar_y1, bar_x2, bar_y2),
            radius=40,
            fill=(40, 40, 40, 220),
        )

        # 🎶 Song Thumbnail (rounded rectangle)
        song_thumb = changeImageSize(200, 200, yt)
        mask = Image.new("L", song_thumb.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, song_thumb.size[0], song_thumb.size[1]),
            radius=30,
            fill=255,
        )
        bg.paste(song_thumb, (260, 210), mask)

        # Fonts
        font_title = ImageFont.truetype(
            "AnonXMusic/assets/font.ttf", 32
        )
        font_small = ImageFont.truetype(
            "AnonXMusic/assets/font2.ttf", 26
        )

        # Title (SAFE WIDTH)
        safe_title = fit_text(draw, title, font_title, 420)
        draw.text((500, 235), safe_title, fill="white", font=font_title)
        draw.text((500, 275), channel, fill="lightgray", font=font_small)

        # ⏳ Progress bar
        draw.rounded_rectangle(
            (500, 330, 960, 345),
            radius=10,
            fill=(120, 120, 120),
        )
        draw.rounded_rectangle(
            (500, 330, 720, 345),
            radius=10,
            fill=(255, 255, 255),
        )

        draw.text((500, 355), "00:00", fill="white", font=font_small)
        draw.text((915, 355), duration, fill="white", font=font_small)

        # ⏯ Buttons
        cy = 430

        # Previous
        draw.polygon([(610, cy), (630, cy - 15), (630, cy + 15)], fill="white")
        draw.polygon([(630, cy), (650, cy - 15), (650, cy + 15)], fill="white")

        # Play
        draw.polygon(
            [(705, cy - 18), (705, cy + 18), (740, cy)],
            fill="white",
        )

        # Next
        draw.polygon([(800, cy), (780, cy - 15), (780, cy + 15)], fill="white")
        draw.polygon([(820, cy), (800, cy - 15), (800, cy + 15)], fill="white")

        # Bot Name
        draw.text(
            (1050, 20),
            unidecode(app.name),
            fill="white",
            font=font_small,
        )

        bg.save(path)
        os.remove("cache/temp.png")
        return path

    except Exception:
        return YOUTUBE_IMG_URL
