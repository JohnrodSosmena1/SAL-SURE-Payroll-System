import pymysql
import bcrypt  # For password hashing

# Database configuration (update if your XAMPP setup has a password)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default for XAMPP
    'db': 'payroll_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor  # Returns dicts for easy mapping
}

def get_connection():
    """Establish a connection to the database."""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        print(f"DB Connection Error: {e}")
        raise

def load_employees():
    """Load all employees as a dict {username: employee_dict}, matching JSON structure."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM employees")
            rows = cursor.fetchall()
            employees = {}
            for row in rows:
                username = row['username']
                employees[username] = {
                    'name': row['name'],
                    'email': row['email'],
                    'id': row['emp_id'],
                    'salary': float(row['salary']),  # Convert DECIMAL to float
                    'days': row['days_worked'],
                    'department': row['department'],
                    'password': row['password'],  # Hashed password
                    'status': row['status'],
                    'pending': bool(row['pending']),  # Convert TINYINT to bool
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return employees
    except pymysql.Error as e:
        print(f"Load Employees Error: {e}")
        return {}
    finally:
        conn.close()

def get_employee(username):
    """Load a single employee by username."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM employees WHERE username = %s", (username,))
            row = cursor.fetchone()
            if row:
                return {
                    'name': row['name'],
                    'email': row['email'],
                    'id': row['emp_id'],
                    'salary': float(row['salary']),
                    'days': row['days_worked'],
                    'department': row['department'],
                    'password': row['password'],  # Hashed
                    'status': row['status'],
                    'pending': bool(row['pending']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
    except pymysql.Error as e:
        print(f"Get Employee Error: {e}")
        return None
    finally:
        conn.close()

def save_employees(employees):
    """Save the employees dict to the database (upsert each record). Password should be pre-hashed."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for username, emp in employees.items():
                cursor.execute("""
                    INSERT INTO employees 
                    (username, name, email, emp_id, salary, days_worked, department, password, status, pending)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    email = VALUES(email),
                    emp_id = VALUES(emp_id),
                    salary = VALUES(salary),
                    days_worked = VALUES(days_worked),
                    department = VALUES(department),
                    password = VALUES(password),
                    status = VALUES(status),
                    pending = VALUES(pending)
                """, (
                    username, emp.get('name'), emp.get('email'), emp.get('id'),
                    emp.get('salary'), emp.get('days'), emp.get('department'),
                    emp.get('password'), emp.get('status'), emp.get('pending', True)  # Default pending to True for new/updated
                ))
        conn.commit()
    except pymysql.Error as e:
        print(f"Save Employees Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_employee(username):
    """Delete an employee by username, including related payroll records."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Delete related payroll records first to avoid foreign key constraints
            cursor.execute("DELETE FROM payrolls WHERE employee_username = %s", (username,))
            # Then delete the employee
            cursor.execute("DELETE FROM employees WHERE username = %s", (username,))
        conn.commit()
    except pymysql.Error as e:
        print(f"Delete Employee Error: {e}")
        conn.rollback()
        raise  # Propagate the error to the caller (UI) for proper handling
    finally:
        conn.close()

def save_payrolls(employees):
    """Process payroll calculations and save to payrolls table, then set pending=0."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for username, emp in employees.items():
                if emp.get('pending', False):
                    gross = (emp.get('salary', 0) / 30) * emp.get('days', 0)
                    tax = 0.15 * gross
                    net = gross - tax
                    cursor.execute("""
                        INSERT INTO payrolls (employee_username, gross, tax, net)
                        VALUES (%s, %s, %s, %s)
                    """, (username, gross, tax, net))
                    cursor.execute("UPDATE employees SET pending = 0 WHERE username = %s", (username,))
        conn.commit()
    except pymysql.Error as e:
        print(f"Save Payrolls Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def load_payrolls(username):
    """Load payroll history for an employee."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM payrolls WHERE employee_username = %s ORDER BY processed_at DESC", (username,))
            rows = cursor.fetchall()
            return [
                {
                    'gross': float(row['gross']),
                    'tax': float(row['tax']),
                    'net': float(row['net']),
                    'processed_at': row['processed_at']
                } for row in rows
            ]
    except pymysql.Error as e:
        print(f"Load Payrolls Error: {e}")
        return []
    finally:
        conn.close()