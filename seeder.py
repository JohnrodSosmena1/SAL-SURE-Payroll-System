import pymysql
import random
import bcrypt
from datetime import datetime, timedelta

# DB Configuration (same as db.py)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default for XAMPP
    'db': 'payroll_db',
    'charset': 'utf8mb4',
}

# Lists for realistic data
first_names = [
    'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Olivia',
    'Robert', 'Sophia', 'William', 'Ava', 'Joseph', 'Mia', 'Charles', 'Isabella',
    'Thomas', 'Amelia', 'Christopher', 'Evelyn'
]

last_names = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
]

departments = ['IT', 'HR', 'Finance', 'Sales', 'Marketing', 'Operations', 'Legal', 'Customer Service']

def get_connection():
    """Establish a connection to the database."""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        print(f"DB Connection Error: {e}")
        raise

def check_table_exists(table_name):
    """Check if a table exists in the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            return bool(result)
    except pymysql.Error as e:
        print(f"Error checking table {table_name}: {e}")
        return False
    finally:
        conn.close()

def seed_employees():
    """Seed 100 realistic dummy employees and optional payroll data."""
    if not check_table_exists('employees'):
        print("Error: 'employees' table does not exist in database 'payroll_db'. Please create it first.")
        return
    if not check_table_exists('payrolls'):
        print("Warning: 'payrolls' table does not exist. Skipping payroll seeding.")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Get existing usernames and emp_ids to avoid conflicts
            existing_usernames = set()
            existing_emp_ids = set()
            cursor.execute("SELECT username, emp_id FROM employees")
            for row in cursor.fetchall():
                existing_usernames.add(row[0])
                existing_emp_ids.add(row[1])

            inserted = 0
            for i in range(100):  # Attempt to insert 100 employees
                first = random.choice(first_names)
                last = random.choice(last_names)
                base_username = f"{first.lower()}.{last.lower()}"
                username = base_username
                counter = 1
                while username in existing_usernames:
                    username = f"{base_username}{counter}"  # Append number if duplicate
                    counter += 1
                existing_usernames.add(username)

                # Generate unique emp_id
                emp_id = f"EMP{i+100:03d}"
                while emp_id in existing_emp_ids:
                    i += 1
                    emp_id = f"EMP{i+100:03d}"
                existing_emp_ids.add(emp_id)

                name = f"{first} {last}"
                email = f"{first.lower()}.{last.lower()}@example.com"
                salary = round(random.uniform(20000, 100000), 2)
                days_worked = random.randint(0, 30)
                department = random.choice(departments)
                # Hash password "123"
                salt = bcrypt.gensalt()
                password = bcrypt.hashpw(b"123", salt).decode()
                status = 'Inactive' if random.random() < 0.1 else 'Active'  # 10% Inactive
                pending = 1 if random.random() < 0.5 else 0  # 50% pending
                created_at = datetime.now() - timedelta(days=random.randint(0, 365))
                updated_at = created_at

                try:
                    cursor.execute("""
                        INSERT INTO employees 
                        (username, name, email, emp_id, salary, days_worked, department, password, status, pending, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        email = VALUES(email),
                        emp_id = VALUES(emp_id),
                        salary = VALUES(salary),
                        days_worked = VALUES(days_worked),
                        department = VALUES(department),
                        password = VALUES(password),
                        status = VALUES(status),
                        pending = VALUES(pending),
                        created_at = VALUES(created_at),
                        updated_at = VALUES(updated_at)
                    """, (username, name, email, emp_id, salary, days_worked, department, password, status, pending, created_at, updated_at))
                    inserted += 1
                    print(f"Inserted employee: {username} ({emp_id})")
                except pymysql.Error as e:
                    print(f"Error inserting {username}: {e}")
                    continue

                # Seed payroll data for 50% of employees
                if check_table_exists('payrolls') and random.random() < 0.5:
                    gross = (salary / 30) * days_worked
                    tax = 0.15 * gross
                    net = gross - tax
                    processed_at = created_at + timedelta(days=random.randint(1, 30))
                    try:
                        cursor.execute("""
                            INSERT INTO payrolls (employee_username, gross, tax, net, processed_at)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (username, gross, tax, net, processed_at))
                        print(f"Inserted payroll for {username}")
                    except pymysql.Error as e:
                        print(f"Error inserting payroll for {username}: {e}")

            conn.commit()
            print(f"Seeded {inserted} dummy employees successfully.")
    except pymysql.Error as e:
        print(f"Seeder Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_employees()