"""e-label 二维码标签生成（迁移自 app.py:generate_elabel）。返回 PNG 字节流。"""
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_elabel(result: dict) -> bytes:
    """生成 PNG 标签（二维码 + 文字），返回字节流。"""
    cable = result["cable_type"]
    length = result["length"]
    detail = result.get("analysis_detail") or {}
    test_time = (result.get("device_info") or {}).get("test_time", "")

    qr_data = (
        f"Cable: {cable}\n"
        f"Length: {length}m\n"
        f"Pass: {'YES' if result['qualified'] else 'NO'}\n"
        f"S11: {detail.get('s11_mean', 0):.1f}dB\n"
        f"S21: {detail.get('s21_mean', 0):.1f}dB\n"
        f"Time: {test_time}"
    )

    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    label_img = Image.new("RGB", (500, 300), "white")
    draw = ImageDraw.Draw(label_img)

    try:
        font_text = ImageFont.truetype("simhei.ttf", 16)
    except OSError:
        font_text = ImageFont.load_default()

    text_lines = [
        f"线缆类型: {cable}",
        f"长度: {length} m",
        f"合格状态: {'合格' if result['qualified'] else '不合格'}",
        f"S11均值: {detail.get('s11_mean', 0):.1f} dB",
        f"S21均值: {detail.get('s21_mean', 0):.1f} dB",
        f"测试时间: {test_time}",
    ]
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill="black", font=font_text)
        y += 25

    qr_img = qr_img.resize((150, 150))
    label_img.paste(qr_img, (330, 30))

    img_bytes = io.BytesIO()
    label_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()
