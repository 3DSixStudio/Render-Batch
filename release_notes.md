Bản đầu tiên của SCS Batch Render (app UI).

**Cài đặt:** tải `SCS_Batch_Render_v1.0.0.zip` bên dưới → giải nén vào thư mục cố định → chạy `run.bat` (cần Python 3.10+, lần đầu tự cài PySide6).

- Tự dò blender.exe (registry, Program Files, Steam, PATH...)
- Chọn file .blend (kéo thả được), thư mục lưu ảnh
- Quét scene: đếm Scs / Icon / Custom, tick box từng ảnh; render tất cả hoặc chỉ mục được tích
- Nút Dừng ngay, log, màn hình "Đang render" (tiến độ sample, thời gian, thumbnail ảnh vừa xong)
- Ô % độ phân giải để render thử nhanh
- Update online qua GitHub Releases
- Sửa lỗi tool cũ: thứ tự Scs/Icon, frame & resolution của Custom object, render trùng empty con, tên file có ký tự đặc biệt, 1 ảnh lỗi không còn làm dừng cả batch
