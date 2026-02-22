from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).resolve().parents[1] / "assets"
OUT = Path(__file__).resolve().parents[1] / "storage" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

TEMPLATE = ASSETS / "cert_template.png"
SAFE_JPG = OUT / "cert_template_safe.jpg"   # Telegram uchun 100% ishlaydi


def get_certificate_safe_path() -> Path:
    """
    Template rasmni Telegram 'photo' uchun 100% mos qilib qayta saqlaydi (JPEG).
    Bir marta yaratilgandan keyin qayta-qayta ishlataveradi.
    """
    if SAFE_JPG.exists():
        return SAFE_JPG

    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template topilmadi: {TEMPLATE}")

    img = Image.open(TEMPLATE)

    # Telegram ko‘p muammoli formatlarni yomon ko‘radi:
    # shuning uchun RGB ga o‘tkazamiz va JPEG qilib saqlaymiz
    img = img.convert("RGB")

    # Juda katta bo‘lsa (masalan 6000px+), kichraytirib yuboramiz
    max_w = 2000
    if img.size[0] > max_w:
        ratio = max_w / img.size[0]
        img = img.resize((max_w, int(img.size[1] * ratio)))

    img.save(SAFE_JPG, "JPEG", quality=92, optimize=True)
    return SAFE_JPG