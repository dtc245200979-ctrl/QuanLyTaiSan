# HỆ THỐNG QUẢN LÝ TÀI SẢN – ĐỀ 16

## 1. Giới thiệu

Dự án xây dựng hệ thống quản lý tài sản sử dụng Flask để phát triển ứng dụng web, PostgreSQL để lưu trữ dữ liệu và Docker Compose để triển khai các dịch vụ.

Hệ thống hỗ trợ quản lý danh sách tài sản và lịch sử bảo trì. Các thông tin cấu hình nhạy cảm được lưu trong file `.env`, không đưa lên GitHub.

## 2. Công nghệ sử dụng

- **Backend:** Python, Flask
- **Cơ sở dữ liệu:** PostgreSQL 16
- **Triển khai:** Docker, Docker Compose
- **Reverse proxy và HTTPS:** Nginx
- **Giám sát:** Prometheus, Grafana, cAdvisor và các exporter
- **Thu thập log:** Loki, Promtail
- **Quản trị cơ sở dữ liệu:** pgAdmin

## 3. Cấu trúc dự án

- `app/`: Mã nguồn ứng dụng Flask
- `database/`: Cấu hình và tài nguyên cơ sở dữ liệu
- `logging/`: Cấu hình hệ thống ghi log
- `monitoring/`: Cấu hình giám sát
- `nginx/`: Cấu hình Nginx
- `certs/`: Chứng chỉ HTTPS dùng cho môi trường phù hợp
- `docker-compose.yml`: Cấu hình các dịch vụ Docker
- `.env.example`: Mẫu biến môi trường
- `.gitignore`: Các tệp và thư mục không đưa lên Git
- `README.md`: Tài liệu hướng dẫn dự án

## 4. Yêu cầu

- Docker Desktop
- Docker Compose
- Git (nếu cần quản lý mã nguồn bằng Git)

## 5. Cấu hình môi trường

1. Tạo file `.env` từ `.env.example` nếu chưa có.
2. Điền các giá trị cấu hình phù hợp vào `.env`.
3. Sử dụng mật khẩu mạnh và không chia sẻ file `.env`.
4. Không đưa mật khẩu, khóa bí mật hoặc dữ liệu nhạy cảm lên GitHub.

## 6. Khởi chạy dự án

Mở PowerShell tại thư mục dự án và chạy:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

## 7. Các địa chỉ truy cập

- Ứng dụng qua HTTP: http://localhost:8080
- Ứng dụng qua HTTPS: https://localhost:8443
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- pgAdmin: http://localhost:5050
- cAdvisor: http://localhost:8081

Lưu ý: Các địa chỉ trên sử dụng cổng được cấu hình trong Docker Compose. Trình duyệt có thể cảnh báo chứng chỉ HTTPS nếu dự án sử dụng chứng chỉ tự ký.

## 8. Giám sát và ghi log

Prometheus thu thập các chỉ số giám sát. Grafana hiển thị dashboard. Loki và Promtail phục vụ việc thu thập, truy vấn log. cAdvisor và các exporter cung cấp số liệu về container, Nginx và PostgreSQL.

## 9. Lưu ý bảo mật

- Không commit file `.env` hoặc thông tin xác thực.
- Không công khai cổng hoặc dịch vụ quản trị nếu chưa có biện pháp bảo vệ phù hợp.
- Không xóa volume cơ sở dữ liệu khi chưa sao lưu và chưa hiểu rõ tác động.
- Kiểm tra trạng thái các container sau khi khởi chạy.

## 10. Kiểm tra cấu hình

Chạy lệnh sau để kiểm tra cấu hình Docker Compose:

```powershell
docker compose config --quiet
```

Nếu lệnh không báo lỗi, cấu hình Docker Compose đã vượt qua bước kiểm tra cú pháp.
