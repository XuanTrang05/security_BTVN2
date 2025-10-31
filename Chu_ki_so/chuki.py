# sign_full.py
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import io, os, datetime, hashlib

# ====================== CONFIG ======================
BASE_DIR = r"D:\Chu_ki_so"
INPUT_PDF = os.path.join(BASE_DIR, "CHU_KI_SO_BTVN2.pdf")
PRIVATE_KEY = os.path.join(BASE_DIR, "private.pem")
SIGN_IMG = os.path.join(BASE_DIR, "signature_image.png")
TEMP_VISUAL = os.path.join(BASE_DIR, "temp_visual.pdf")
UNSIGNED_PDF = os.path.join(BASE_DIR, "unsigned.pdf")
OUTPUT_PDF = os.path.join(BASE_DIR, "CHU_KI_SO_BTVN2_signed_final.pdf")
SIG_PLACEHOLDER_LEN = 8192

NAME_TEXT = "Hoàng Thị Xuân Trang"
PHONE_TEXT = "033 2914 611"

# ====================== BƯỚC 1: TẠO ẢNH CHỮ KÝ TRONG SUỐT ======================
def make_signature_transparent(input_path, output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ Không tìm thấy ảnh chữ ký: {input_path}")

    print("🖼️ Đang xử lý ảnh chữ ký (loại bỏ nền trắng)...")
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()
    new_data = []

    for item in datas:
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"✅ Ảnh chữ ký trong suốt: {output_path}")
    return output_path

signature_img_transparent = os.path.join(BASE_DIR, "signature_image_transparent.png")
signature_img_used = make_signature_transparent(SIGN_IMG, signature_img_transparent)

# ====================== BƯỚC 2: TẠO FILE PDF CÓ ẢNH CHỮ KÝ + THÔNG TIN ======================
def register_unicode_font():
    candidates = [
        r"C:\Windows\Fonts\ARIALUNI.TTF",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\DejaVuSans.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("UIFONT", path))
            return "UIFONT"
    return "Helvetica"

font_name = register_unicode_font()
now = datetime.datetime.now()
date_str = now.strftime("%d/%m/%Y")
time_str = now.strftime("%H:%M:%S")

print("2) Tạo visual PDF tạm (chèn ảnh chữ ký, tên, ngày, SĐT)...")

reader = PdfReader(INPUT_PDF)
page = reader.pages[-1]  # Chèn chữ ký vào trang cuối
w = float(page.mediabox.width)
h = float(page.mediabox.height)

packet = io.BytesIO()
can = canvas.Canvas(packet, pagesize=(w, h))
sig = ImageReader(signature_img_used)

sig_w, sig_h = 150, 60
x = w - sig_w - 50
y = 80

can.drawImage(sig, x, y, width=sig_w, height=sig_h, mask='auto')
can.setFont(font_name, 10)
can.drawCentredString(x + sig_w / 2, y - 14, NAME_TEXT)
can.setFont(font_name, 9)
can.drawRightString(x + sig_w, y - 28, f"Ký ngày: {date_str} {time_str}")
can.drawRightString(x + sig_w, y - 42, f"Điện thoại: {PHONE_TEXT}")
can.save()
packet.seek(0)

visual_pdf = PdfReader(packet)
writer = PdfWriter()
for i, p in enumerate(reader.pages):
    if i == len(reader.pages) - 1:
        p.merge_page(visual_pdf.pages[0])
    writer.add_page(p)

with open(TEMP_VISUAL, "wb") as f:
    writer.write(f)

print(f"✅ Tạo visual PDF: {TEMP_VISUAL}")

# ====================== BƯỚC 3–6: KÝ SỐ PDF ======================
print("3) Tạo unsigned PDF (có vùng /Contents dự trữ + /ByteRange placeholder) ...")

reader = PdfReader(TEMP_VISUAL)
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

sig_placeholder = "0" * SIG_PLACEHOLDER_LEN
writer.add_metadata({
    "/ByteRange": "[0 ********** ********** **********]",
    "/Contents": f"<{sig_placeholder}>"
})

with open(UNSIGNED_PDF, "wb") as f:
    writer.write(f)
print(f"✅ unsigned PDF tạo xong: {UNSIGNED_PDF}")

# ---- 4) Hash ----
print("4) Tính /ByteRange và hash SHA-256 (loại trừ /Contents) ...")
data = open(UNSIGNED_PDF, "rb").read()
contents_start = data.find(b"<" + b"0" * SIG_PLACEHOLDER_LEN + b">")
contents_end = contents_start + len(b"<" + b"0" * SIG_PLACEHOLDER_LEN + b">")
byte_range = [0, contents_start, contents_end, len(data) - contents_end]
data_to_hash = data[:contents_start] + data[contents_end:]
digest = hashlib.sha256(data_to_hash).digest()
print(f"ByteRange: {byte_range}")
print(f"SHA-256 digest (hex): {digest.hex()}")

# ---- 5) Ký bằng Private Key ----
print("5) Ký bằng private key (RSA PKCS#1 v1.5 + SHA256) ...")
with open(PRIVATE_KEY, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

signature = private_key.sign(
    digest,
    padding.PKCS1v15(),
    hashes.SHA256()
)
print(f"Kích thước chữ ký (bytes): {len(signature)}")

# ---- 6) Ghi chữ ký vào PDF ----
print("6) Ghi chữ ký vào /Contents và cập nhật /ByteRange ...")
sig_hex = signature.hex()
sig_hex_padded = sig_hex + "0" * (SIG_PLACEHOLDER_LEN * 2 - len(sig_hex))
byte_range_str = f"/ByteRange [0 {byte_range[1]} {byte_range[2]} {byte_range[3]}]"
data_signed = data.replace(b"/ByteRange [0 ********** ********** **********]", byte_range_str.encode())
data_signed = data_signed.replace(
    b"<" + b"0" * SIG_PLACEHOLDER_LEN + b">",
    f"<{sig_hex_padded}>".encode()
)

with open(OUTPUT_PDF, "wb") as f:
    f.write(data_signed)

print(f"✅ Hoàn tất: file ký lưu tại: {OUTPUT_PDF}")
