CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    asset_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    purchase_date DATE,
    purchase_price NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'Available'
        CHECK (status IN ('Available', 'InUse', 'Maintenance', 'Retired')),
    department_id INTEGER REFERENCES departments(id),
    assigned_employee_id INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS maintenance_history (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    maintenance_date DATE NOT NULL DEFAULT CURRENT_DATE,
    description TEXT NOT NULL,
    cost NUMERIC(15,2) DEFAULT 0 CHECK (cost >= 0),
    performed_by VARCHAR(150),
    next_maintenance_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO departments (name, description)
VALUES
    ('Công nghệ thông tin', 'Quản lý thiết bị công nghệ'),
    ('Hành chính', 'Quản lý thiết bị văn phòng')
ON CONFLICT (name) DO NOTHING;

INSERT INTO employees (full_name, email, department_id)
SELECT 'Nguyễn Văn An', 'an@example.com', id
FROM departments
WHERE name = 'Công nghệ thông tin'
ON CONFLICT (email) DO NOTHING;

INSERT INTO assets (
    asset_code, name, category, purchase_date,
    purchase_price, status, department_id, assigned_employee_id
)
SELECT
    'TS001', 'Laptop Dell', 'Laptop', '2026-01-10',
    15000000, 'InUse', d.id, e.id
FROM departments d
CROSS JOIN employees e
WHERE d.name = 'Công nghệ thông tin'
  AND e.email = 'an@example.com'
ON CONFLICT (asset_code) DO NOTHING;

INSERT INTO maintenance_history (
    asset_id, maintenance_date, description, cost, performed_by,
    next_maintenance_date
)
SELECT id, CURRENT_DATE, 'Kiểm tra thiết bị định kỳ',
       200000, 'Bộ phận kỹ thuật', CURRENT_DATE + 90
FROM assets
WHERE asset_code = 'TS001'
  AND NOT EXISTS (
      SELECT 1 FROM maintenance_history
      WHERE asset_id = assets.id
        AND description = 'Kiểm tra thiết bị định kỳ'
  );
