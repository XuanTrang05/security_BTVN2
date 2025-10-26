# security_BTVN2
 1) Cấu trúc PDF liên quan chữ ký (Nghiên cứu)- Mô tả ngắn gọn: Catalog, Pages tree, Page object, Resources, Content streams, 
XObject, AcroForm, Signature field (widget), Signature dictionary (/Sig), 
/ByteRange, /Contents, incremental updates, và DSS (theo PAdES).- Liệt kê object refs quan trọng và giải thích vai trò của từng object trong 
lưu/truy xuất chữ ký.- Đầu ra: 1 trang tóm tắt + sơ đồ object (ví dụ: Catalog → Pages → Page → /Contents
 ; Catalog → /AcroForm → SigField → SigDict).
 2) Thời gian ký được lưu ở đâu?- Nêu tất cả vị trí có thể lưu thông tin thời gian:
 + /M trong Signature dictionary (dạng text, không có giá trị pháp lý).
 + Timestamp token (RFC 3161) trong PKCS#7 (attribute timeStampToken).
 + Document timestamp object (PAdES).
 + DSS (Document Security Store) nếu có lưu timestamp và dữ liệu xác minh.- Giải thích khác biệt giữa thông tin thời gian /M và timestamp RFC3161.
 3) Các bước tạo và lưu chữ ký trong PDF (đã có private RSA)- Viết script/code thực hiện tuần tự:
 1. Chuẩn bị file PDF gốc.
 2. Tạo Signature field (AcroForm), reserve vùng /Contents (8192 bytes).
 3. Xác định /ByteRange (loại trừ vùng /Contents khỏi hash).
 4. Tính hash (SHA-256/512) trên vùng ByteRange.
 5. Tạo PKCS#7/CMS detached hoặc CAdES:- Include messageDigest, signingTime, contentType.- Include certificate chain.- (Tùy chọn) thêm RFC3161 timestamp token.
 6. Chèn blob DER PKCS#7 vào /Contents (hex/binary) đúng offset.
 7. Ghi incremental update.
 8. (LTV) Cập nhật DSS với Certs, OCSPs, CRLs, VRI.- Phải nêu rõ: hash alg, RSA padding, key size, vị trí lưu trong PKCS#7.- Đầu ra: mã nguồn, file PDF gốc, file PDF đã ký.

## BÀI LÀM
# Catalog
- Catalog (hay còn gọi là Root Object) là đối tượng gốc của tài liệu PDF, đóng vai trò như điểm bắt đầu (entry point) để trình đọc PDF hiểu toàn bộ cấu trúc tài liệu.
# Chức năng chính:
- Là đối tượng cấp cao nhất trong cây đối tượng của PDF.
- Tham chiếu đến các thành phần quan trọng khác như:
- /Pages → cây các trang (Pages tree)
- /AcroForm → biểu mẫu (form), bao gồm trường chữ ký (signature field)
- /Names, /Outlines, /DSS, … (các thành phần tùy chọn khác)
- Ví dụ trong PDF:
1 0 obj
<<
  /Type /Catalog
  /Pages 2 0 R
  /AcroForm 5 0 R
>>
endobj
- /Type /Catalog: xác định đây là đối tượng Catalog.
- /Pages 2 0 R: tham chiếu đến đối tượng chứa danh sách trang.
- /AcroForm 5 0 R: tham chiếu đến biểu mẫu có thể chứa chữ ký.
# Vai trò trong cấu trúc chữ ký số:
- Là điểm bắt đầu để truy xuất chữ ký, vì chữ ký nằm trong /AcroForm.
- Khi phần mềm đọc chữ ký PDF, nó bắt đầu từ /Root (Catalog) → /AcroForm → /SigField → /Sig để lấy thông tin chữ
# Pages tree
- Pages Tree (cây trang) là cấu trúc phân cấp trong PDF dùng để tổ chức và quản lý các trang của tài liệu.
- Nó giúp trình đọc PDF dễ dàng duyệt, sắp xếp và hiển thị nội dung của từng trang.
# Thành phần chính
Node gốc: /Pages — đối tượng gốc của cây trang.
Các node con: có thể là /Pages khác (cấp trung gian) hoặc /Page (trang thực)
- Mỗi node /Pages có:
/Type /Pages — xác định là node dạng “Pages”.
/Kids — mảng chứa tham chiếu tới các trang hoặc node con.
/Count — tổng số trang nằm trong cây con đó.
# Ví dụ trong PDF:
2 0 obj
<<
  /Type /Pages
  /Kids [3 0 R 4 0 R]
  /Count 2
>>
endobj
- /Kids: chứa hai phần tử (3 0 R, 4 0 R) là hai Page Object.h
- /Count 2: tổng số trang = 2.
# Quan hệ với Catalog và Page Object:
Catalog
 └── /Pages (Pages Tree root)
        ├── /Kids → [Page1, Page2, ...]
        └── /Count → tổng số trang
# Page object
- Page Object là đối tượng đại diện cho một trang cụ thể trong tài liệu PDF.
- Mỗi trang mà bạn nhìn thấy khi mở file PDF đều tương ứng với một Page Object trong cấu trúc nội bộ của file.
# Chức năng chính:
- Mô tả nội dung, tài nguyên và bố cục của một trang.
- Liên kết đến:
- /Parent → node /Pages chứa nó
- /Resources → phông chữ, hình ảnh, XObject, v.v.
- /Contents → nội dung thực của trang (text, hình vẽ, annotation)
- /Annots → danh sách các chú thích hoặc trường biểu mẫu (bao gồm widget chữ ký)
# Ví dụ trong PDF:
3 0 obj
<<
  /Type /Page
  /Parent 2 0 R
  /Resources 6 0 R
  /Contents 7 0 R
  /Annots [8 0 R] 
  /MediaBox [0 0 595 842]
>>
endobj
- /Type /Page: xác định đây là trang PDF.
- /Parent 2 0 R: tham chiếu đến node /Pages cha.
- /Resources: chứa các tài nguyên đồ họa dùng trên trang.
- /Contents: tham chiếu đến luồng nội dung (text, hình ảnh, vẽ...).
- /Annots: mảng chứa annotation — ví dụ: ô chữ ký số, hộp nhập liệu, chú thích.
# Quan hệ trong cấu trúc:
Catalog
 └── /Pages
        ├── /Kids → [Page1, Page2, ...]
                  ├── /Contents → luồng nội dung
                  ├── /Resources → tài nguyên
                  └── /Annots → [Signature Widget]
- Vai trò trong cấu trúc chữ ký PDF:
- Chữ ký hiển thị (signature appearance) được thể hiện như một widget annotation nằm trong /Annots của Page Object.
- Widget này liên kết tới Signature Field trong /AcroForm, và từ đó trỏ tới Signature Dictionary chứa dữ liệu chữ ký thực.
# Resources
- Resources là tập hợp tài nguyên mà một trang PDF dùng để hiển thị nội dung.
- Gồm phông chữ, hình ảnh, màu sắc, mẫu vẽ, v.v.
# Chức năng chính:
- /Font: phông chữ dùng trong văn bản
- /XObject: hình ảnh, logo, hoặc form tái sử dụng
- /ExtGState, /ColorSpace: trạng thái vẽ, màu sắc
# Ví dụ:
/Resources <<
  /Font << /F1 9 0 R >>
  /XObject << /Im1 10 0 R >>
>>
# Vai trò trong chữ ký số:
- Chứa hình ảnh chữ ký (XObject) để hiển thị khung chữ ký trên trang.
# Content streams
- Content Streams là luồng dữ liệu mô tả nội dung hiển thị của trang PDF, bao gồm văn bản, hình vẽ, ảnh, chú thích, v.v.
- Trình đọc PDF sẽ giải mã và vẽ nội dung trang dựa trên luồng này.
# Chức năng:
- Chứa các lệnh đồ họa PDF (PDF drawing commands).
- Mỗi trang có một hoặc nhiều stream được tham chiếu qua khóa /Contents.
# Ví dụ:
7 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
(Signature Area) Tj
ET
endstream
endobj
# Vai trò trong chữ ký số:
- Chứa dòng lệnh hiển thị vùng chữ ký hoặc chữ “Signed by…”.
- Khi ký PDF, phần này có thể được thêm mới bằng cơ chế incremental update để hiển thị chữ ký mà không làm thay đổi nội dung gốc.
# XObject
- XObject (External Object) là đối tượng đồ họa có thể tái sử dụng trong PDF, thường dùng để chèn hình ảnh, biểu mẫu hoặc hình vẽ phức tạp vào nhiều trang mà không cần lặp lại dữ liệu.
# Các loại XObject phổ biến:
- /Image → ảnh (JPEG, PNG, v.v.)
- /Form → nhóm lệnh vẽ (dạng template hoặc khung ký)
- /PS → PostScript XObject (hiếm dùng)
# Ví dụ:
10 0 obj
<<
  /Type /XObject
  /Subtype /Image
  /Width 200
  /Height 50
  /ColorSpace /DeviceRGB
  /BitsPerComponent 8
  /Length 1024
>>
stream
...dữ liệu hình ảnh...
endstream
endobj
# Quan hệ trong cấu trúc:
Page Object
 └── /Resources
        └── /XObject << /Im1 10 0 R >>
# Vai trò trong chữ ký số:
- Chữ ký thường có hình ảnh hiển thị (signature appearance) như logo hoặc ảnh chữ ký tay.
- Hình đó được lưu trong /XObject và gọi ra trong Content Stream khi hiển thị khung chữ ký.
# AcroForm
- Là đối tượng mô tả biểu mẫu tương tác (form) trong PDF.
- Chứa mảng /Fields – danh sách các trường (text box, checkbox, chữ ký, v.v.).
- Khi PDF có chữ ký, trường chữ ký nằm trong /AcroForm/Fields.
# Ví dụ:
5 0 obj
<<
  /Fields [6 0 R]
>>
endobj
# Vai trò:
- Là nơi chứa định nghĩa trường chữ ký (Signature Field).
# Signature Field
- Là trường form đặc biệt có loại /FT /Sig.
- Hiển thị ô chữ ký trên trang PDF và trỏ tới chữ ký thật trong /V.
- Nằm trong /AcroForm/Fields.
# Ví dụ:
6 0 obj
<<
  /Type /Annot
  /Subtype /Widget
  /FT /Sig
  /T (Signature1)
  /V 7 0 R
  /Rect [100 100 300 150]
>>
endobj
# Vai trò:
- Xác định vị trí và liên kết của chữ ký hiển thị trên trang.
# Signature Dictionary
- Là đối tượng chứa dữ liệu chữ ký số thật (chứng thư, thời gian, thuật toán…).
- Được tham chiếu từ /V trong Signature Field.
# Ví dụ:
7 0 obj
<<
  /Type /Sig
  /Filter /Adobe.PPKLite
  /SubFilter /adbe.pkcs7.detached
  /Name (Hoang Thi Xuan Trang)
  /M (D:20251025)
  /ByteRange [0 15500 17000 3000]
  /Contents (3082A1FF...)
>>
endobj
# Vai trò: 
- Chứa toàn bộ dữ liệu chữ ký số (PKCS#7/CMS) và thông tin ký.
# ByteRange
- Là mảng chỉ định các đoạn byte trong file được đưa vào khi tính chữ ký.
- Giúp phần mềm kiểm tra tính toàn vẹn của tài liệu (bỏ qua vùng chứa chữ ký).
# Ví dụ:
/ByteRange [0 15500 17000 3000]
# Vai trò:
- Xác định phần dữ liệu được ký và được bỏ qua (chữ ký hex).
# Incremental Updates
- Là cơ chế cập nhật PDF mà không ghi đè dữ liệu cũ.
- Khi ký, phần chữ ký được thêm ở cuối file → giúp bảo toàn nội dung trước khi ký.
- Mỗi lần ký hoặc chỉnh sửa tạo ra một phiên bản mới (revision) trong cùng file.
# Vai trò:
- Đảm bảo toàn vẹn và khả năng xác minh lịch sử của chữ ký.
# DSS (theo PAdES)
- Là phần mở rộng của chuẩn PAdES (PDF Advanced Electronic Signature).
- Lưu trữ chứng thư số, OCSP, CRL để xác thực chữ ký lâu dài (LTV).
# Ví dụ:
8 0 obj
<<
  /Type /DSS
  /Certs [9 0 R]
  /OCSPs [10 0 R]
  /CRLs [11 0 R]
>>
endobj
# Vai trò: 
- Giúp chữ ký hợp lệ lâu dài ngay cả khi CA hoặc chứng thư gốc hết hạn.
