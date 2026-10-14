# Khôi phục CyberSentinel sau khi dọn Docker

Repository có source, Dockerfile, Compose, migrations, `uv.lock` và
`frontend/package-lock.json`. GitHub không thay thế bản sao dữ liệu runtime.

## Phân biệt cloud và local

Bản portfolio được mô tả tại `docs/portfolio-deployment.md` chạy frontend trên
Vercel, API trên Render và PostgreSQL trên Neon. Xóa dữ liệu Docker trên laptop
không xóa các dịch vụ cloud này. Database, model và dữ liệu thử nghiệm local vẫn
cần được kiểm kê riêng.

## Những gì phải giữ ngoài GitHub

- `.env`, `.env.demo.local`, `frontend/.env.local` và secrets triển khai thực tế.
- Database PostgreSQL local và dữ liệu ứng dụng trong các volume Compose.
- Dữ liệu Redis nếu cần giữ queue/state; dashboard và lịch sử monitoring nếu cần.
- Dataset và model trong `data/`, `artifacts/`, DVC cache hoặc DVC remote.
  File `.dvc` trong Git là metadata, không phải toàn bộ nội dung dataset/model.
- File tạo trong writable layer của container mà chưa đưa ra volume/bind mount.

Trong Compose mặc định, các volume gồm `postgres-data`, `cybersentinel-data`,
`redis-data` và các volume monitoring. Compose demo/staging có thể dùng tên khác.
Lấy tên thực tế từ `docker volume ls` và mounts của container trước khi sao lưu.

## Sao lưu và kiểm tra

1. Push source và ghi commit bằng `git rev-parse HEAD`.
2. Giữ cấu hình riêng ở thư mục backup ngoài repo, có giới hạn quyền truy cập.
3. Giữ dataset/model/DVC content thực tế; không chỉ lưu file metadata `.dvc`.
4. Với stack Compose mặc định, `scripts/backup-postgres.sh` xuất PostgreSQL
   custom dump, kiểm tra mục lục và tạo checksum. Script cần `POSTGRES_USER`,
   `POSTGRES_DB`; dùng đúng Compose project và cấu hình đã tạo database.
5. Sao lưu các volume khác và file local cần giữ. Dừng tiến trình ghi trước khi
   lấy bản raw volume; ghi lại image và PostgreSQL major version.
6. Kiểm tra checksum, giải nén archive và restore database vào môi trường tạm.
   Có `scripts/backup-restore-drill.sh`; đọc yêu cầu và cấu hình đích trước khi chạy.

## Dựng lại

Clone repo, checkout commit đã lưu, khôi phục cấu hình riêng và DVC content.
Nếu DVC remote đã được sao lưu đầy đủ, cấu hình lại remote tương ứng rồi chạy
`uv run dvc pull`. Không ghi đè cấu hình cloud bằng credential của database local.

Để dựng demo mới với dữ liệu mẫu:

```bash
./scripts/start-demo.sh
```

Demo mới không khôi phục lịch sử local cũ. Để lấy lại dữ liệu cũ, dùng cùng
Compose project và cùng cấu hình đã lưu; khôi phục database/volume vào môi trường
trống trước khi cho API và worker chạy. Dùng `scripts/restore-postgres.sh` chỉ
sau khi kiểm tra database đích. Bản raw PostgreSQL cần major version tương thích.

Kiểm tra `/ready`, đăng nhập, danh sách incidents và model/dataset cần sử dụng.
Thử phục hồi trên môi trường riêng; không ghi đè database Neon hoặc volume gốc
để thử backup.

Image và build cache có thể tải/build lại. Chỉ dọn toàn bộ Docker khi dữ liệu
cần giữ đã được sao lưu và kiểm tra khôi phục. Không push `.env`, database dump,
archive volume, hoặc dữ liệu riêng tư lên GitHub công khai. Một bản backup trên
ổ khác cùng máy bảo vệ trước việc dọn Docker; cần bản ngoài máy để phòng mất máy.
