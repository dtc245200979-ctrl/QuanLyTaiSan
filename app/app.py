
import os
import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
)
import psycopg
from prometheus_flask_exporter import PrometheusMetrics


# Cau hinh ghi log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("quanlytaisan")

app = Flask(__name__)
metrics = PrometheusMetrics(app)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "dev-key-change-before-deployment",
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "database"),
    "dbname": os.getenv("DB_NAME", "quanlytaisan"),
    "user": os.getenv("DB_USER", "qlts_user"),
    "password": os.getenv("DB_PASSWORD", "Qlts_DB_2026!ChangeMe"),
}

VALID_STATUSES = {"Available", "InUse", "Maintenance", "Retired"}

HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Quản lý tài sản</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            margin: 0;
            color: #1e293b;
        }
        header {
            background: #1d4ed8;
            color: white;
            padding: 22px 5%;
        }
        header h1 { margin-top: 0; }
        main {
            max-width: 1100px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .card {
            background: white;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px #0000000d;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }
        input, select, button, textarea {
            box-sizing: border-box;
            padding: 10px;
            width: 100%;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font: inherit;
        }
        textarea {
            min-height: 80px;
            resize: vertical;
        }
        button {
            background: #2563eb;
            color: white;
            cursor: pointer;
            border: none;
            font-weight: bold;
        }
        button:hover { background: #1d4ed8; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th { background: #eff6ff; }
        .table-wrap { overflow-x: auto; }
        .message {
            padding: 10px;
            border-radius: 6px;
            background: #dcfce7;
            color: #166534;
            margin-bottom: 12px;
        }
        .error {
            background: #fee2e2;
            color: #991b1b;
        }
        .hint {
            color: #64748b;
            font-size: 14px;
        }
    </style>
</head>
<body>
<header>
    <h1>Hệ thống Quản lý Tài sản / Thiết bị</h1>
    <p>Theo dõi tài sản, người sử dụng và lịch sử bảo trì</p>
</header>

<main>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <p class="message {% if category == 'error' %}error{% endif %}">
                {{ message }}
            </p>
        {% endfor %}
    {% endwith %}

    <section class="card">
        <h2>Thêm tài sản mới</h2>
        <form method="post" action="{{ url_for('add_asset') }}">
            <div class="grid">
                <input name="asset_code"
                       placeholder="Mã tài sản (VD: TS007)" required>
                <input name="name" placeholder="Tên thiết bị" required>
                <input name="category" placeholder="Loại thiết bị">
                <input name="purchase_price" type="number"
                       min="0" step="0.01"
                       placeholder="Giá mua (VNĐ)" value="0">
                <select name="status">
                    <option value="Available">Sẵn sàng</option>
                    <option value="InUse">Đang sử dụng</option>
                    <option value="Maintenance">Đang bảo trì</option>
                    <option value="Retired">Ngừng sử dụng</option>
                </select>
                <button type="submit">Thêm tài sản</button>
            </div>
        </form>
    </section>

    <section class="card">
        <h2>Thêm lịch sử bảo trì</h2>
        {% if assets %}
        <form method="post" action="{{ url_for('add_maintenance') }}">
            <div class="grid">
                <select name="asset_id" required>
                    <option value="">-- Chọn tài sản --</option>
                    {% for item in assets %}
                    <option value="{{ item.id }}">
                        {{ item.asset_code }} - {{ item.name }}
                    </option>
                    {% endfor %}
                </select>

                <input type="date" name="maintenance_date"
                       value="{{ today }}" required>

                <input type="number" name="cost"
                       min="0" step="0.01"
                       placeholder="Chi phí bảo trì (VNĐ)"
                       value="0" required>

                <textarea name="description"
                          placeholder="Nội dung bảo trì"
                          required></textarea>

                <button type="submit">Lưu lịch sử bảo trì</button>
            </div>
        </form>
        {% else %}
            <p>Chưa có tài sản. Hãy thêm tài sản trước khi ghi nhận bảo trì.</p>
        {% endif %}
        <p class="hint">
            Chọn đúng tài sản, ngày thực hiện, nội dung và chi phí bảo trì.
        </p>
    </section>

    <section class="card">
        <h2>Danh sách tài sản ({{ assets|length }})</h2>
        <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Mã tài sản</th>
                    <th>Tên thiết bị</th>
                    <th>Loại</th>
                    <th>Giá mua (VNĐ)</th>
                    <th>Trạng thái</th>
                </tr>
            </thead>
            <tbody>
            {% for item in assets %}
                <tr>
                    <td>{{ item.asset_code }}</td>
                    <td>{{ item.name }}</td>
                    <td>{{ item.category or '-' }}</td>
                    <td>{{ "{:,.0f}".format(item.purchase_price or 0) }}</td>
                    <td>
                        {% if item.status == 'Available' %}Sẵn sàng
                        {% elif item.status == 'InUse' %}Đang sử dụng
                        {% elif item.status == 'Maintenance' %}Đang bảo trì
                        {% elif item.status == 'Retired' %}Ngừng sử dụng
                        {% else %}{{ item.status }}
                        {% endif %}
                    </td>
                </tr>
            {% else %}
                <tr><td colspan="5">Chưa có tài sản nào.</td></tr>
            {% endfor %}
            </tbody>
        </table>
        </div>
    </section>

    <section class="card">
        <h2>Lịch sử bảo trì ({{ maintenance|length }})</h2>
        <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Mã tài sản</th>
                    <th>Thiết bị</th>
                    <th>Ngày bảo trì</th>
                    <th>Nội dung</th>
                    <th>Chi phí (VNĐ)</th>
                </tr>
            </thead>
            <tbody>
            {% for item in maintenance %}
                <tr>
                    <td>{{ item.asset_code }}</td>
                    <td>{{ item.asset_name }}</td>
                    <td>{{ item.maintenance_date }}</td>
                    <td>{{ item.description }}</td>
                    <td>{{ "{:,.0f}".format(item.cost or 0) }}</td>
                </tr>
            {% else %}
                <tr><td colspan="5">Chưa có lịch sử bảo trì.</td></tr>
            {% endfor %}
            </tbody>
        </table>
        </div>
    </section>
</main>
</body>
</html>
"""


@app.get("/")
def index():
    logger.info("Yeu cau xem danh sach tai san.")

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, asset_code, name, category,
                           purchase_price, status
                    FROM assets
                    ORDER BY id DESC
                """)
                asset_rows = cur.fetchall()
                asset_columns = [
                    "id", "asset_code", "name", "category",
                    "purchase_price", "status",
                ]
                assets = [
                    dict(zip(asset_columns, row))
                    for row in asset_rows
                ]

                cur.execute("""
                    SELECT a.asset_code,
                           a.name AS asset_name,
                           m.maintenance_date,
                           m.description,
                           m.cost
                    FROM maintenance_history m
                    JOIN assets a ON a.id = m.asset_id
                    ORDER BY m.maintenance_date DESC, m.id DESC
                """)
                maintenance_rows = cur.fetchall()
                maintenance_columns = [
                    "asset_code", "asset_name", "maintenance_date",
                    "description", "cost",
                ]
                maintenance = [
                    dict(zip(maintenance_columns, row))
                    for row in maintenance_rows
                ]

        return render_template_string(
            HTML,
            assets=assets,
            maintenance=maintenance,
            today=date.today().isoformat(),
        )

    except Exception:
        logger.exception("Loi khi tai danh sach tai san va bao tri.")
        return "Đã xảy ra lỗi khi tải dữ liệu.", 500


@app.post("/assets")
def add_asset():
    asset_code = request.form.get("asset_code", "").strip()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or None
    status = request.form.get("status", "Available")

    try:
        price = Decimal(request.form.get("purchase_price") or "0")
        if not price.is_finite() or price < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError, TypeError):
        flash("Giá mua không hợp lệ.", "error")
        return redirect(url_for("index"))

    if not asset_code or not name:
        flash("Mã tài sản và tên thiết bị là bắt buộc.", "error")
        return redirect(url_for("index"))

    if status not in VALID_STATUSES:
        flash("Trạng thái tài sản không hợp lệ.", "error")
        return redirect(url_for("index"))

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO assets
                        (asset_code, name, category, purchase_price, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (asset_code, name, category, price, status))

        logger.info("Them tai san thanh cong: %s", asset_code)
        flash("Đã thêm tài sản thành công.", "success")

    except psycopg.errors.UniqueViolation:
        flash("Mã tài sản đã tồn tại.", "error")
    except Exception:
        logger.exception("Loi khi them tai san: %s", asset_code)
        flash("Đã xảy ra lỗi khi thêm tài sản.", "error")

    return redirect(url_for("index"))


@app.post("/maintenance")
def add_maintenance():
    asset_id = request.form.get("asset_id", "").strip()
    maintenance_date = request.form.get("maintenance_date", "").strip()
    description = request.form.get("description", "").strip()

    try:
        if not asset_id.isdigit():
            raise ValueError("Tai san khong hop le.")
        asset_id = int(asset_id)

        parsed_date = date.fromisoformat(maintenance_date)
        cost = Decimal(request.form.get("cost") or "0")

        if not cost.is_finite() or cost < 0:
            raise InvalidOperation

        if not description:
            flash("Vui lòng nhập nội dung bảo trì.", "error")
            return redirect(url_for("index"))

    except (ValueError, InvalidOperation, TypeError):
        flash("Ngày bảo trì hoặc chi phí không hợp lệ.", "error")
        return redirect(url_for("index"))

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM assets WHERE id = %s",
                    (asset_id,),
                )
                if cur.fetchone() is None:
                    flash("Tài sản đã chọn không tồn tại.", "error")
                    return redirect(url_for("index"))

                cur.execute("""
                    INSERT INTO maintenance_history
                        (asset_id, maintenance_date, description, cost)
                    VALUES (%s, %s, %s, %s)
                """, (asset_id, parsed_date, description, cost))

        logger.info(
            "Them lich su bao tri thanh cong: asset_id=%s",
            asset_id,
        )
        flash("Đã thêm lịch sử bảo trì thành công.", "success")

    except Exception:
        logger.exception("Loi khi them lich su bao tri.")
        flash(
            "Không thể thêm lịch sử bảo trì. Hãy kiểm tra log ứng dụng.",
            "error",
        )

    return redirect(url_for("index"))


if __name__ == "__main__":
    logger.info("Khoi dong ung dung Quan ly tai san.")
    app.run(host="0.0.0.0", port=5000, debug=False)
