"""Generate icon.ico + ui/icon.png for SCS Batch Render (run: python tools/make_icon.py)."""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c1, c2):
    g = Image.new("RGB", (size, size))
    px = g.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size - 2)
            px[x, y] = lerp(c1, c2, t)
    return g


def rounded_mask(size, box, r):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    return m


def make():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pad = 40
    bg = gradient(S, (124, 92, 255), (255, 159, 67)).convert("RGBA")
    img.paste(bg, (0, 0), rounded_mask(S, (pad, pad, S - pad, S - pad), 230))

    # back card (batch)
    back = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(back)
    d.rounded_rectangle((300, 215, 790, 640), 70, fill=(255, 255, 255, 110))
    img = Image.alpha_composite(img, back)

    # front card shadow
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((225, 330, 735, 790), 75, fill=(40, 20, 90, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img, sh)

    # front card (image)
    front = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(front)
    d.rounded_rectangle((215, 305, 725, 765), 75, fill=(255, 255, 255, 255))
    # mountains + sun inside
    d.polygon([(275, 705), (430, 520), (560, 705)], fill=(124, 92, 255))
    d.polygon([(450, 705), (575, 575), (665, 705)], fill=(167, 140, 255))
    d.ellipse((560, 375, 650, 465), fill=(255, 159, 67))
    img = Image.alpha_composite(img, front)

    # sparkle (render)
    sp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    cx, cy, R, r = 770, 270, 120, 26
    d.polygon([(cx, cy - R), (cx + r, cy - r), (cx + R, cy), (cx + r, cy + r),
               (cx, cy + R), (cx - r, cy + r), (cx - R, cy), (cx - r, cy - r)], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, sp)

    os.makedirs(os.path.join(ROOT, "ui"), exist_ok=True)
    img.resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, "ui", "icon.png"))
    img.save(os.path.join(ROOT, "icon.ico"),
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon.ico + ui/icon.png written")


if __name__ == "__main__":
    make()
