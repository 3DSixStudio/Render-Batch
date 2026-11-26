# SCS Batch Render

App Windows (PySide6) để render hàng loạt các collection `Scs_N` / `Icon_N` trong file Blender đã setup sẵn, chạy Blender ở chế độ background (không mở giao diện Blender).

## Cài & chạy

1. Cài **Python 3.10+** từ https://www.python.org/downloads/ (tick *Add python.exe to PATH*).
2. Tải repo về (Code → Download ZIP) và giải nén vào một thư mục cố định.
3. Chạy **`run.bat`**. Lần đầu nó tự cài PySide6.
4. (Tùy chọn) chạy `Tao_Shortcut_Desktop.bat` để tạo shortcut ngoài Desktop.

## Tính năng

- **Tự dò blender.exe**: registry, Program Files, mọi thư viện Steam, `%LOCALAPPDATA%`, Scoop, PATH. Danh sách hiện trong combobox, mặc định chọn bản mới nhất; có nút *Chọn...* để chỉ tay.
- **File .blend**: chọn hoặc **kéo thả** vào cửa sổ, app tự *Quét scene*.
- **Danh sách trong scene**: đếm số collection/ảnh Scs, Icon, Custom; tick box theo từng ảnh (Map, Map event, Object, Custom).
  - *Render tất cả* hoặc *Chỉ render mục được tích* (lựa chọn tick được nhớ theo từng file .blend).
- **Dừng ngay**: kill Blender lập tức.
- **Màn hình Đang render**: mục đang render, resolution/frame, tiến độ sample, tổng n/m, thời gian và ước tính còn lại, thumbnail ảnh vừa xong (bấm để mở).
- **Log** đầy đủ như bản .bat, có lưu log ra file.
- **Update online** từ GitHub (repo này); bản cũ được backup vào `_backup_update/`.
- Ô **Độ phân giải %** để render thử nhanh (100% = full).

## Quy tắc render

| Collection | Resolution | Frame |
|---|---|---|
| `Scs_N` | 2796 × 2048 | Start + (N − 1) |
| `Icon_N` | 2048 × 2048 | Start + (N − 1) |

- Mỗi object gốc (empty/mesh top-level) trong collection → 1 ảnh, object con hiện theo.
- `Setup` luôn hiện. `Map` render riêng (1 ảnh, hoặc 1 ảnh / `Event_` có `scs_event_active`), luôn ẩn trong ảnh object.
- Object có `scs_render_separate = True` render riêng ở cuối, dùng frame gốc của scene.
- Thứ tự: Scs trước, Icon sau, mỗi nhóm tăng dần theo số.

## Chạy không cần UI

`SCS_Batch_Render_CLI.bat`, hoặc:

```
blender --background scene.blend --python scs_render_core.py --python-exit-code 1 -- --output D:\renders [--gpu] [--only Scs_1,Icon_2] [--percent 25]
```

## Phát hành bản mới

Sửa code → tăng số trong `version.txt` → push lên `main`. App của mọi người bấm *Update online* sẽ thấy bản mới.
