# Hệ thống quản lý tài sản – Đề 16

## 1. Giới thiệu

Dự án xây dựng hệ thống quản lý tài sản, sử dụng Flask để phát triển ứng dụng web, PostgreSQL để lưu trữ dữ liệu và Docker Compose để triển khai các dịch vụ.

Hệ thống có chức năng quản lý danh sách tài sản và lịch sử bảo trì, đồng thời tích hợp HTTPS, giám sát hệ thống và thu thập log.

## 2. Công nghệ sử dụng

- Python và Flask
- PostgreSQL 16
- pgAdmin
- Docker và Docker Compose
- Nginx và HTTPS
- Prometheus và Grafana
- Loki và Promtail

## 3. Chức năng chính

- Hiển thị danh sách tài sản.
- Theo dõi trạng thái tài sản.
- Thêm lịch sử bảo trì.
- Lưu trữ dữ liệu trong PostgreSQL.
- Truy cập ứng dụng qua HTTPS.
- Thu thập và giám sát chỉ số hệ thống.
- Thu thập log để hỗ trợ kiểm tra và xử lý lỗi.

## 4. Cấu hình môi trường

1. Cài đặt Docker Desktop và khởi động Docker.
2. Sao chép `.env.example` thành `.env`.
3. Điền các mật khẩu và khóa bí mật riêng vào `.env`.
4. Không đưa `.env` thật lên GitHub.

## 5. Khởi chạy dự án

Mở Terminal tại thư mục dự án và chạy:

```bash
docker compose up -d --build
```

Kiểm tra trạng thái các dịch vụ:

```bash
docker compose ps
```

Xem log ứng dụng:

```bash
docker compose logs --tail=50 app
```

## 6. Các địa chỉ truy cập

- Ứng dụng HTTPS: https://localhost:8443
- Ứng dụng HTTP: http://localhost:8080
- pgAdmin: http://localhost:5050
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

Chứng chỉ HTTPS tự ký có thể khiến trình duyệt hiển thị cảnh báo khi chạy trên máy phát triển.

## 7. Giám sát và ghi log

Prometheus được sử dụng để thu thập các chỉ số từ những dịch vụ đã cấu hình. Grafana cung cấp dashboard trực quan. Loki và Promtail hỗ trợ thu thập, truy vấn log.

## 8. Bảo mật

- Sử dụng biến môi trường để cấu hình thông tin nhạy cảm.
- Không công khai mật khẩu hoặc khóa bí mật.
- Nginx bổ sung các HTTP Security Headers.
- Các cổng dịch vụ được giới hạn truy cập qua địa chỉ localhost theo cấu hình Docker Compose.

## 9. Dừng hệ thống

```bash
docker compose down
```

Lệnh trên dừng và xóa các container, nhưng không xóa các named volume dữ liệu.

## 10. Ảnh minh chứng

Các ảnh minh chứng được lưu trong thư mục `anh_minh_chung/`, bao gồm giao diện HTTPS, Security Headers, Prometheus, Grafana và Loki.
