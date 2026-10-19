import os
import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template_string, request, redirect, url_for, flash
import psycopg
from prometheus_flask_exporter import PrometheusMetrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("quanlytaisan")

app = Flask(__name__)
metrics = PrometheusMetrics(app)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-before-deployment")

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
body { font-family: Arial, sans-serif; background: #f1f5f9; margin: 0; color: #1e293b; }
header { background: #1d4ed8; color: white; padding: 22px 5%; }
header h1 { margin-top: 0; }
main { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
.card { background: white; padding: 22px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 2px 8px #0000000d; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
input, select, button, textarea { box-sizing: border-box; padding: 10px; width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; font: inherit; }
textarea { min-height: 80px; resize: vertical; }
button { background: #2563eb; color: white; cursor: pointer; border: none; font-weight: bold; }
button:hover { background: #1d4ed8; }
table { width: 100%; border-collapse: collapse; background: white; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
th { background: #eff6ff; }
.table-wrap { overflow-x: auto; }
.message { padding: 10px; border-radius: 6px; background: #dcfce7; color: #166534; margin-bottom: 12px; }
.error { background: #fee2e2; color: #991b1b; }
.hint { color: #64748b; font-size: 14px; }
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.filter-row input, .filter-row select { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; }
.filter-row input { flex: 1; min-width: 220px; }
.filter-row select { min-width: 180px; }
#noResults { margin-top: 12px; color: #64748b; }
.edit-link { display: inline-block; padding: 7px 12px; background: #dbeafe; color: #1d4ed8; border-radius: 6px; text-decoration: none; font-weight: bold; white-space: nowrap; }
.edit-link:hover { background: #bfdbfe; }
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
<p class="message {% if category == 'error' %}error{% endif %}">{{ message }}</p>
{% endfor %}
{% endwith %}

<section class="card">
<h2>Thêm tài sản mới</h2>
<form method="post" action="{{ url_for('add_asset') }}">
<div class="grid">
<input name="asset_code" placeholder="Mã tài sản (VD: TS007)" required>
<input name="name" placeholder="Tên thiết bị" required>
<input name="category" placeholder="Loại thiết bị">
<input name="purchase_price" type="number" min="0" step="0.01" placeholder="Giá mua (VNĐ)" value="0">
<select name="status">
<option value="Available">Sẵn sàng</option><option value="InUse">Đang sử dụng</option>
<option value="Maintenance">Đang bảo trì</option><option value="Retired">Ngừng sử dụng</option>
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
<select name="asset_id" required><option value="">-- Chọn tài sản --</option>
{% for item in assets %}<option value="{{ item.id }}">{{ item.asset_code }} - {{ item.name }}</option>{% endfor %}
</select>
<input type="date" name="maintenance_date" value="{{ today }}" required>
<input type="number" name="cost" min="0" step="0.01" placeholder="Chi phí bảo trì (VNĐ)" value="0" required>
<textarea name="description" placeholder="Nội dung bảo trì" required></textarea>
<button type="submit">Lưu lịch sử bảo trì</button>
</div>
</form>
{% else %}<p>Chưa có tài sản. Hãy thêm tài sản trước khi ghi nhận bảo trì.</p>{% endif %}
<p class="hint">Chọn đúng tài sản, ngày thực hiện, nội dung và chi phí bảo trì.</p>
</section>

<section class="card">
<h2>Danh sách tài sản (<span id="assetCount">{{ assets|length }}</span>)</h2>
<div class="filter-row">
<input type="text" id="searchAsset" placeholder="Tìm theo mã, tên thiết bị hoặc loại...">
<select id="filterStatus">
<option value="">Tất cả trạng thái</option><option value="Available">Sẵn sàng</option>
<option value="InUse">Đang sử dụng</option><option value="Maintenance">Đang bảo trì</option>
<option value="Retired">Ngừng sử dụng</option>
</select>
</div>
<div class="table-wrap">
<table id="assetTable">
<thead><tr><th>Mã tài sản</th><th>Tên thiết bị</th><th>Loại</th><th>Giá mua (VNĐ)</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
<tbody>
{% for item in assets %}
<tr data-status="{{ item.status }}">
<td>{{ item.asset_code }}</td><td>{{ item.name }}</td><td>{{ item.category or '-' }}</td>
<td>{{ "{:,.0f}".format(item.purchase_price or 0) }}</td>
<td>{% if item.status == 'Available' %}Sẵn sàng
{% elif item.status == 'InUse' %}Đang sử dụng
{% elif item.status == 'Maintenance' %}Đang bảo trì
{% elif item.status == 'Retired' %}Ngừng sử dụng
{% else %}{{ item.status }}{% endif %}</td>
<td><a class="edit-link" href="{{ url_for('edit_asset', asset_id=item.id) }}">Sửa</a></td>
</tr>
{% else %}<tr class="empty-row"><td colspan="6">Chưa có tài sản nào.</td></tr>{% endfor %}
</tbody>
</table>
<p id="noResults" hidden>Không tìm thấy tài sản phù hợp.</p>
</div>
</section>

<script>
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchAsset");
    const statusFilter = document.getElementById("filterStatus");
    const table = document.getElementById("assetTable");
    const count = document.getElementById("assetCount");
    const noResults = document.getElementById("noResults");
    function filterAssets() {
        const keyword = searchInput.value.trim().toLocaleLowerCase();
        const status = statusFilter.value;
        let visibleCount = 0;
        table.querySelectorAll("tbody tr[data-status]").forEach(function (row) {
            const text = row.innerText.toLocaleLowerCase();
            const visible = text.includes(keyword) && (!status || row.dataset.status === status);
            row.hidden = !visible;
            if (visible) visibleCount++;
        });
        count.textContent = visibleCount;
        noResults.hidden = visibleCount !== 0;
    }
    searchInput.addEventListener("input", filterAssets);
    statusFilter.addEventListener("change", filterAssets);
});
</script>

<section class="card">
<h2>Lịch sử bảo trì ({{ maintenance|length }})</h2>
<div class="table-wrap"><table>
<thead><tr><th>Mã tài sản</th><th>Thiết bị</th><th>Ngày bảo trì</th><th>Nội dung</th><th>Chi phí (VNĐ)</th></tr></thead>
<tbody>
{% for item in maintenance %}
<tr><td>{{ item.asset_code }}</td><td>{{ item.asset_name }}</td><td>{{ item.maintenance_date }}</td><td>{{ item.description }}</td><td>{{ "{:,.0f}".format(item.cost or 0) }}</td></tr>
{% else %}<tr><td colspan="5">Chưa có lịch sử bảo trì.</td></tr>{% endfor %}
</tbody></table></div>
</section>
</main>
</body>
</html>
"""

EDIT_ASSET_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sửa tài sản</title>
<style>
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; background: #f1f5f9; margin: 0; color: #1e293b; }
main { max-width: 650px; margin: 35px auto; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 2px 8px #0000000d; }
input, select, button { width: 100%; padding: 11px; margin: 8px 0 16px; border: 1px solid #cbd5e1; border-radius: 6px; font: inherit; }
button { background: #2563eb; color: white; border: none; cursor: pointer; font-weight: bold; }
button:hover { background: #1d4ed8; }
a { color: #2563eb; }
.message { padding: 10px; border-radius: 6px; background: #dcfce7; color: #166534; }
.error { background: #fee2e2; color: #991b1b; }
</style>
</head>
<body><main>
<h1>Sửa thông tin tài sản</h1>
{% with messages = get_flashed_messages(with_categories=true) %}
{% for category, message in messages %}
<p class="message {% if category == 'error' %}error{% endif %}">{{ message }}</p>
{% endfor %}
{% endwith %}
<form method="post">
<label for="asset_code">Mã tài sản</label>
<input id="asset_code" name="asset_code" value="{{ asset.asset_code }}" required>
<label for="name">Tên thiết bị</label>
<input id="name" name="name" value="{{ asset.name }}" required>
<label for="category">Loại thiết bị</label>
<input id="category" name="category" value="{{ asset.category or '' }}">
<label for="purchase_price">Giá mua (VNĐ)</label>
<input id="purchase_price" name="purchase_price" type="number" min="0" step="0.01" value="{{ asset.purchase_price or 0 }}" required>
<label for="status">Trạng thái</label>
<select id="status" name="status" required>
<option value="Available" {% if asset.status == 'Available' %}selected{% endif %}>Sẵn sàng</option>
<option value="InUse" {% if asset.status == 'InUse' %}selected{% endif %}>Đang sử dụng</option>
<option value="Maintenance" {% if asset.status == 'Maintenance' %}selected{% endif %}>Đang bảo trì</option>
<option value="Retired" {% if asset.status == 'Retired' %}selected{% endif %}>Ngừng sử dụng</option>
</select>
<button type="submit">Lưu thay đổi</button>
</form>
<p><a href="{{ url_for('index') }}">Quay lại danh sách</a></p>
</main></body></html>
"""


@app.get("/")
def index():
    logger.info("Yeu cau xem danh sach tai san.")
    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, asset_code, name, category, purchase_price, status
                    FROM assets ORDER BY id DESC
                """)
                asset_rows = cur.fetchall()
                asset_columns = ["id", "asset_code", "name", "category", "purchase_price", "status"]
                assets = [dict(zip(asset_columns, row)) for row in asset_rows]

                cur.execute("""
                    SELECT a.asset_code, a.name AS asset_name,
                           m.maintenance_date, m.description, m.cost
                    FROM maintenance_history m
                    JOIN assets a ON a.id = m.asset_id
                    ORDER BY m.maintenance_date DESC, m.id DESC
                """)
                maintenance_rows = cur.fetchall()
                maintenance_columns = ["asset_code", "asset_name", "maintenance_date", "description", "cost"]
                maintenance = [dict(zip(maintenance_columns, row)) for row in maintenance_rows]

        return render_template_string(HTML, assets=assets, maintenance=maintenance, today=date.today().isoformat())
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
                    INSERT INTO assets (asset_code, name, category, purchase_price, status)
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



@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
def edit_asset(asset_id):
    if request.method == "POST":
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
            return redirect(url_for("edit_asset", asset_id=asset_id))

        if not asset_code or not name:
            flash("Mã tài sản và tên thiết bị là bắt buộc.", "error")
            return redirect(url_for("edit_asset", asset_id=asset_id))

        if status not in VALID_STATUSES:
            flash("Trạng thái tài sản không hợp lệ.", "error")
            return redirect(url_for("edit_asset", asset_id=asset_id))

        try:
            with psycopg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE assets
                        SET asset_code = %s,
                            name = %s,
                            category = %s,
                            purchase_price = %s,
                            status = %s
                        WHERE id = %s
                    """, (asset_code, name, category, price, status, asset_id))

                    if cur.rowcount == 0:
                        flash("Không tìm thấy tài sản.", "error")
                        return redirect(url_for("index"))

            flash("Đã cập nhật tài sản thành công.", "success")
            return redirect(url_for("index"))

        except psycopg.errors.UniqueViolation:
            flash("Mã tài sản đã tồn tại.", "error")
        except Exception:
            logger.exception("Lỗi khi sửa tài sản ID: %s", asset_id)
            flash("Không thể cập nhật tài sản.", "error")

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, asset_code, name, category, purchase_price, status
                    FROM assets
                    WHERE id = %s
                """, (asset_id,))
                asset = cur.fetchone()

        if not asset:
            return "Không tìm thấy tài sản.", 404

        return render_template_string("""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Sửa tài sản</title>
            </head>
            <body>
                <h1>Sửa tài sản</h1>

                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% for category, message in messages %}
                    <p>{{ message }}</p>
                  {% endfor %}
                {% endwith %}

                <form method="post">
                    <p>Mã tài sản:
                    <input name="asset_code" required value="{{ asset[1] }}"></p>

                    <p>Tên thiết bị:
                    <input name="name" required value="{{ asset[2] }}"></p>

                    <p>Loại:
                    <input name="category" value="{{ asset[3] or '' }}"></p>

                    <p>Giá mua (VNĐ):
                    <input name="purchase_price" type="number" min="0"
                           step="0.01" required value="{{ asset[4] }}"></p>

                    <p>Trạng thái:
                    <select name="status">
                      {% for value, label in [
                        ('Available', 'Sẵn sàng'),
                        ('InUse', 'Đang sử dụng'),
                        ('Maintenance', 'Đang bảo trì'),
                        ('Retired', 'Ngừng sử dụng')
                      ] %}
                        <option value="{{ value }}"
                          {% if asset[5] == value %}selected{% endif %}>
                          {{ label }}
                        </option>
                      {% endfor %}
                    </select></p>

                    <button type="submit">Lưu thay đổi</button>
                    <a href="{{ url_for('index') }}">Quay lại</a>
                </form>
            </body>
            </html>
        """, asset=asset)

    except Exception:
        logger.exception("Lỗi khi tải tài sản ID: %s", asset_id)
        return "Không thể tải thông tin tài sản.", 500


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
                cur.execute("SELECT id FROM assets WHERE id = %s", (asset_id,))
                if cur.fetchone() is None:
                    flash("Tài sản đã chọn không tồn tại.", "error")
                    return redirect(url_for("index"))
                cur.execute("""
                    INSERT INTO maintenance_history (asset_id, maintenance_date, description, cost)
                    VALUES (%s, %s, %s, %s)
                """, (asset_id, parsed_date, description, cost))
        logger.info("Them lich su bao tri thanh cong: asset_id=%s", asset_id)
        flash("Đã thêm lịch sử bảo trì thành công.", "success")
    except Exception:
        logger.exception("Loi khi them lich su bao tri.")
        flash("Không thể thêm lịch sử bảo trì. Hãy kiểm tra log ứng dụng.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    logger.info("Khoi dong ung dung Quan ly tai san.")
    app.run(host="0.0.0.0", port=5000, debug=False)
