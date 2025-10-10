import sys
from datetime import datetime
import bcrypt  # For password hashing
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout,
    QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QFrame,
    QGridLayout, QHeaderView, QMainWindow, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QPieSeries, QValueAxis

# Backend functions (keep your existing db.py)
from db import load_employees, save_employees, get_employee, delete_employee, save_payrolls, load_payrolls


# ------------------ Global Design Tokens ------------------
PALETTE = {
    "sidebar": "#1E40AF",      # deep blue
    "accent": "#3B82F6",       # bright accent blue
    "bg": "#F3F4F6",           # light gray background
    "card": "#FFFFFF",         # white cards
    "text": "#1F2937",         # dark gray text
    "muted": "#6B7280",        # secondary text
    "danger": "#EF4444",       # red
    "success": "#10B981",      # green
}

GLOBAL_STYLE = f"""
/* App-wide */
QWidget {{
    background-color: {PALETTE['bg']};
    color: {PALETTE['text']};
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 13px;
}}

/* Inputs */
QLineEdit {{
    background: white;
    border: 1px solid #e6eef8;
    border-radius: 8px;
    padding: 8px;
}}

/* Buttons */
QPushButton {{
    border: none;
    padding: 8px 12px;
    border-radius: 8px;
    font-weight: 600;
}}

QPushButton#primaryBtn {{
    background-color: {PALETTE['accent']};
    color: white;
}}
QPushButton#primaryBtn:hover {{
    background-color: #2563EB;
}}

QPushButton#secondaryBtn {{
    background-color: #EFF6FF;
    color: {PALETTE['sidebar']};
    border: none;
}}
QPushButton#secondaryBtn:hover {{
    background-color: #DBEAFE;
}}

QPushButton#sidebarBtn {{
    color: white;
    background: transparent;
    text-align: left;
    padding-left: 18px;
    padding-right: 18px;
}}
QPushButton#sidebarBtn:hover {{
    background-color: rgba(255,255,255,0.06);
}}
QPushButton#sidebarBtn:pressed {{
    background-color: rgba(255,255,255,0.08);
}}

QPushButton#logoutBtn {{
    background-color: white;
    color: {PALETTE['sidebar']};
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 700;
}}
QPushButton#logoutBtn:hover {{
    background-color: #f1f5f9;
}}

/* Frames / Cards */
QFrame.card {{
    background: {PALETTE['card']};
    border-radius: 12px;
    border: 1px solid rgba(10,10,10,0.03);
}}
QFrame.panel {{
    background: {PALETTE['card']};
    border-radius: 12px;
    border: 1px solid rgba(10,10,10,0.03);
}}

/* Table */
QTableWidget {{
    background: {PALETTE['card']};
    border-radius: 8px;
}}
QHeaderView::section {{
    background: transparent;
    padding: 8px;
    border: none;
    color: {PALETTE['muted']};
    font-weight: 700;
}}

/* Labels */
QLabel.title {{
    font-size: 18px;
    font-weight: 800;
    color: {PALETTE['text']};
}}
QLabel.subtitle {{
    color: {PALETTE['muted']};
    font-size: 12px;
}}
"""

# ------------------ Circular Progress Widget ------------------
class CircularProgressBar(QWidget):
    def __init__(self, value, max_value, title, color):
        super().__init__()
        self.value = value
        self.max_value = max_value if max_value > 0 else 1
        self.title = title
        self.color = color
        self.setMinimumSize(140, 150)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRect(15, 10, 110, 110)
        percentage = int((self.value / self.max_value) * 100)
        percentage = max(0, min(100, percentage))

        pen_bg = QPen(QColor('#e6eef8'), 12)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 0, 360 * 16)

        pen_fg = QPen(QColor(self.color), 12)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        span = -int((percentage / 100) * 360) * 16
        painter.drawArc(rect, 90 * 16, span)

        painter.setPen(QColor(PALETTE['text']))
        painter.setFont(QFont('Segoe UI', 12, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{percentage}%")

        painter.setFont(QFont('Segoe UI', 9))
        painter.setPen(QColor(PALETTE['muted']))
        painter.drawText(0, rect.bottom() + 10, self.width(), 30, Qt.AlignCenter, self.title)


# ------------------ MAIN ENTRY / SELECTION ------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAL SURE - Select Position")
        self.setGeometry(400, 200, 480, 380)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("SAL SURE")
        title.setObjectName("appTitle")
        title.setStyleSheet("font-size:24px; font-weight:800; color: white;")
        # create a small header card to emulate the reference
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header.setStyleSheet(f"background:{PALETTE['sidebar']}; border-radius: 12px; padding: 18px;")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(QLabel("Payroll System"), alignment=Qt.AlignLeft)
        header_layout.addSpacing(8)
        header.setLayout(header_layout)

        big_title = QLabel("Welcome to SAL SURE")
        big_title.setStyleSheet("font-size:20px; font-weight:800; color: #0f172a;")
        big_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(big_title)

        subtitle = QLabel("Sal Sure Payroll System.")
        subtitle.setStyleSheet("color: #6B7280; font-size:13px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.admin_btn = QPushButton("Admin Portal")
        self.admin_btn.setObjectName("primaryBtn")
        self.admin_btn.setFixedHeight(44)
        self.admin_btn.clicked.connect(self.open_admin_login)
        layout.addWidget(self.admin_btn)

        self.emp_btn = QPushButton("Employee Portal")
        self.emp_btn.setObjectName("secondaryBtn")
        self.emp_btn.setFixedHeight(44)
        self.emp_btn.clicked.connect(self.open_employee_login)
        layout.addWidget(self.emp_btn)

        # spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

    def open_admin_login(self):
        self.admin_window = AdminLogin()
        self.admin_window.show()
        self.close()

    def open_employee_login(self):
        self.employee_window = EmployeeLogin()
        self.employee_window.show()
        self.close()


# ------------------ ADMIN LOGIN ------------------
class AdminLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.setGeometry(360, 140, 420, 320)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("🔑 Admin Login")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size:18px; font-weight:800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        self.login_btn = QPushButton("Log In")
        self.login_btn.setObjectName("primaryBtn")
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self.check_login)
        layout.addWidget(self.login_btn)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.setFixedHeight(36)
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    def check_login(self):
        if (self.username.text().strip() == "admin" and self.password.text() in ("123", "admin123")):
            self.dashboard = DashboardWindow(self.username.text().strip())
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid Admin Credentials")

    def go_back(self):
        self.main = MainWindow()
        self.main.show()
        self.close()


# ------------------ DASHBOARD WINDOW (ADMIN) ------------------
class DashboardWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Admin Payroll Dashboard")
        self.setGeometry(160, 80, 1200, 720)
        self.showMaximized()

        # Load employees from DB (backend handled separately)
        self.employees = load_employees()
        if not isinstance(self.employees, dict):
            self.employees = {}

        # Central widget + layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 0)

        # Content area
        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"background-color: {PALETTE['bg']};")
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(28, 24, 28, 24)
        self.content_layout.setSpacing(16)
        self.content_area.setLayout(self.content_layout)
        main_layout.addWidget(self.content_area, 1)

        # Header + start dashboard
        self.show_dashboard_view()

    def create_sidebar(self):
        frame = QFrame()
        frame.setFixedWidth(260)
        frame.setStyleSheet(f"background-color: {PALETTE['sidebar']};")
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        logo = QLabel("💰 SAL SURE")
        logo.setStyleSheet("font-size: 18px; font-weight: 800; color: white;")
        layout.addWidget(logo)

        sub = QLabel("Payroll Management")
        sub.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.9);")
        layout.addWidget(sub)
        layout.addSpacing(8)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setObjectName("sidebarBtn")
        self.btn_dashboard.setFixedHeight(44)
        self.btn_dashboard.clicked.connect(self.show_dashboard_view)
        layout.addWidget(self.btn_dashboard)

        self.btn_manage = QPushButton("Manage Payroll")
        self.btn_manage.setObjectName("sidebarBtn")
        self.btn_manage.setFixedHeight(44)
        self.btn_manage.clicked.connect(self.show_manage_view)
        layout.addWidget(self.btn_manage)

        self.btn_employees = QPushButton("Employee Data")
        self.btn_employees.setObjectName("sidebarBtn")
        self.btn_employees.setFixedHeight(44)
        self.btn_employees.clicked.connect(self.show_employees_view)
        layout.addWidget(self.btn_employees)

        layout.addStretch()

        user_label = QLabel(f"👤 {self.username}")
        user_label.setStyleSheet("color: rgba(255,255,255,0.9);")
        layout.addWidget(user_label)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        frame.setLayout(layout)
        return frame

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_dashboard_view(self):
        self.clear_content()

        header_row = QHBoxLayout()
        notify = QPushButton("🔔")
        notify.setFixedSize(40, 40)
        notify.setStyleSheet("border-radius: 10px; background: white;")
        header_row.addStretch()
        header_row.addWidget(notify)
        header_widget = QWidget()
        header_widget.setLayout(header_row)
        self.content_layout.addWidget(header_widget)

        top = QHBoxLayout()
        welcome = QLabel(f"Welcome back, {self.username}! 👋")
        welcome.setStyleSheet("font-size:20px; font-weight:800;")
        top.addWidget(welcome)
        top.addStretch()
        top_widget = QWidget()
        top_widget.setLayout(top)
        self.content_layout.addWidget(top_widget)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        total_employees = len(self.employees)
        active = sum(1 for e in self.employees.values() if e.get("status", "Active") == "Active")
        inactive = max(0, total_employees - active)
        pending_pay = sum(1 for e in self.employees.values() if e.get("pending", False))

        cpb_active = CircularProgressBar(active, max(1, total_employees), "Active Staff", PALETTE['accent'])
        cpb_inactive = CircularProgressBar(inactive, max(1, total_employees), "Inactive", "#06b6d4")
        stats_row.addWidget(cpb_active)
        stats_row.addWidget(cpb_inactive)

        card_total = self.make_colored_card("Total Employees", str(total_employees))
        card_pending = self.make_colored_card("Pending Payroll", str(pending_pay))
        total_pay = sum(
            ((e.get('salary', 0) / 30) * e.get('days', 0) - 0.15 * ((e.get('salary', 0) / 30) * e.get('days', 0)))
            for e in self.employees.values() if e.get("pending", False)
        )
        card_revenue = self.make_colored_card("This Month Payroll", f"₱ {total_pay:.2f}")
        stats_row.addWidget(card_total)
        stats_row.addWidget(card_pending)
        stats_row.addWidget(card_revenue)

        stats_widget = QWidget()
        stats_widget.setLayout(stats_row)
        self.content_layout.addWidget(stats_widget)

        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        line = self.create_line_chart()
        pie = self.create_pie_chart()
        charts_row.addWidget(line, 2)
        charts_row.addWidget(pie, 1)
        charts_widget = QWidget()
        charts_widget.setLayout(charts_row)
        self.content_layout.addWidget(charts_widget)

        # Lower row: activity + quick stats
        lower_row = QHBoxLayout()
        activity_frame = QFrame()
        activity_frame.setProperty("class", "card")
        activity_frame.setStyleSheet("padding: 12px;")
        activity_layout = QVBoxLayout()
        activity_title = QLabel("Recent Payroll Activity")
        activity_title.setStyleSheet("font-size: 16px; font-weight:700;")
        activity_layout.addWidget(activity_title)
        last = sorted(self.employees.values(), key=lambda e: e.get("created_at", datetime.min), reverse=True)[:6]
        if not last:
            activity_layout.addWidget(QLabel("No recent payroll activity"))
        else:
            for e in last:
                name = e.get("name", "-")
                empid = e.get("id", "-")
                pending = "Pending" if e.get("pending", False) else "Approved"
                salary = (e.get("salary", 0) / 30) * e.get("days", 0)
                net_salary = salary - 0.15 * salary
                lbl = QLabel(f"{name} (ID: {empid}) — {pending} (Net: ₱{net_salary:.2f})")
                lbl.setStyleSheet("color: #475569; font-size: 12px; margin-top: 4px;")
                activity_layout.addWidget(lbl)
        activity_frame.setLayout(activity_layout)
        lower_row.addWidget(activity_frame, 1)

        stats_frame = QFrame()
        stats_frame.setProperty("class", "card")
        stats_frame.setStyleSheet("padding: 12px;")
        stats_layout = QVBoxLayout()
        stats_title = QLabel("Quick Stats")
        stats_title.setStyleSheet("font-size: 16px; font-weight:700;")
        stats_layout.addWidget(stats_title)
        total_employees = max(1, total_employees)
        avg_salary = sum(e.get("salary", 0) for e in self.employees.values()) / total_employees
        avg_days = sum(e.get("days", 0) for e in self.employees.values()) / total_employees
        stats_layout.addWidget(QLabel(f"Average Monthly Salary: ₱{avg_salary:.2f}"))
        stats_layout.addWidget(QLabel(f"Average Days Worked: {avg_days:.1f}"))
        dept_count = {}
        for e in self.employees.values():
            d = e.get("department", "Unknown")
            dept_count[d] = dept_count.get(d, 0) + 1
        if dept_count:
            largest_dept = max(dept_count, key=dept_count.get)
            stats_layout.addWidget(QLabel(f"Largest Department: {largest_dept}"))
        stats_frame.setLayout(stats_layout)
        lower_row.addWidget(stats_frame, 1)

        lower_widget = QWidget()
        lower_widget.setLayout(lower_row)
        self.content_layout.addWidget(lower_widget)

    def create_line_chart(self):
        series = QLineSeries()
        # Dummy data
        for x in range(6):
            series.append(x, 15000 + x * 1000 + (x % 3) * 2000)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Payroll Trend (Sample)")
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().hide()

        axisX = QValueAxis()
        axisX.setTickCount(6)
        axisX.setLabelFormat("%d")
        chart.setAxisX(axisX, series)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background-color: white; border-radius: 12px;")
        return view

    def create_pie_chart(self):
        series = QPieSeries()
        # Dummy departments
        depts = {"Operations": 17, "IT": 12, "HR": 12, "Customer Serv.": 11, "Finance": 11, "Marketing": 11}
        colors = ["#7C3AED", "#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#06B6D4"]
        for i, (dept, pct) in enumerate(depts.items()):
            slice_ = series.append(f"{dept} ({pct}%)", pct)
            slice_.setLabelVisible(True)
            slice_.setColor(QColor(colors[i]))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Department Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignRight)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background-color: white; border-radius: 12px;")
        return view

    def make_colored_card(self, title, value):
        w = QFrame()
        w.setProperty("class", "card")
        w.setStyleSheet("background-color: #EFF6FF; border-radius: 12px; border: 1px solid #DBEAFE;")
        w.setFixedSize(220, 100)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel(title))
        val = QLabel(value)
        val.setStyleSheet("font-weight:800; font-size:18px; color: #0f172a;")
        layout.addStretch()
        layout.addWidget(val)
        w.setLayout(layout)
        return w

    def show_manage_view(self):
        self.clear_content()

        header = QHBoxLayout()
        title = QLabel("Manage Payroll")
        title.setStyleSheet("font-size:18px; font-weight:700;")
        header.addWidget(title)
        header.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)
        header_widget = QWidget()
        header_widget.setLayout(header)
        self.content_layout.addWidget(header_widget)

        form_frame = QFrame()
        form_frame.setProperty("class", "panel")
        form_layout = QGridLayout()
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        form_layout.addWidget(QLabel("Username (key):"), 0, 0)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Employee Username")
        form_layout.addWidget(self.input_name, 0, 1)

        form_layout.addWidget(QLabel("Email:"), 1, 0)
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email")
        form_layout.addWidget(self.input_email, 1, 1)

        form_layout.addWidget(QLabel("Employee ID:"), 2, 0)
        self.input_empid = QLineEdit()
        self.input_empid.setPlaceholderText("Employee ID")
        form_layout.addWidget(self.input_empid, 2, 1)

        form_layout.addWidget(QLabel("Salary (monthly):"), 3, 0)
        self.input_salary = QLineEdit()
        self.input_salary.setPlaceholderText("Base Salary (Monthly)")
        form_layout.addWidget(self.input_salary, 3, 1)

        form_layout.addWidget(QLabel("Days worked:"), 4, 0)
        self.input_days = QLineEdit()
        self.input_days.setPlaceholderText("Attendance (Days Worked)")
        form_layout.addWidget(self.input_days, 4, 1)

        form_layout.addWidget(QLabel("Department:"), 5, 0)
        self.input_dept = QLineEdit()
        self.input_dept.setPlaceholderText("Department (optional)")
        form_layout.addWidget(self.input_dept, 5, 1)

        form_layout.addWidget(QLabel("Password:"), 6, 0)
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Password (leave blank to keep existing)")
        self.input_password.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.input_password, 6, 1)

        form_frame.setLayout(form_layout)
        self.content_layout.addWidget(form_frame)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.load_btn = QPushButton("Load Employee")
        self.load_btn.setObjectName("secondaryBtn")
        self.load_btn.clicked.connect(self.load_employee)
        btn_row.addWidget(self.load_btn)

        self.save_btn = QPushButton("Save Employee")
        self.save_btn.setObjectName("secondaryBtn")
        self.save_btn.clicked.connect(self.save_employee)
        btn_row.addWidget(self.save_btn)

        self.calc_btn = QPushButton("Calculate Payroll")
        self.calc_btn.setObjectName("secondaryBtn")
        self.calc_btn.clicked.connect(self.calculate_payroll_table)
        btn_row.addWidget(self.calc_btn)

        self.approve_btn = QPushButton("Approve Payroll")
        self.approve_btn.setObjectName("secondaryBtn")
        self.approve_btn.clicked.connect(self.approve_payroll)
        btn_row.addWidget(self.approve_btn)

        btn_widget = QWidget()
        btn_widget.setLayout(btn_row)
        self.content_layout.addWidget(btn_widget)

        self.pay_table = QTableWidget()
        self.pay_table.setColumnCount(5)
        self.pay_table.setHorizontalHeaderLabels(["Name", "ID", "Base Salary", "Days Worked", "Calculated Salary"])
        self.pay_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pay_table.setStyleSheet("background-color: white; border-radius: 8px;")
        self.content_layout.addWidget(self.pay_table)

    def load_employee(self):
        key = self.input_name.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Enter Username to load.")
            return
        try:
            emp = get_employee(key)
            if emp:
                self.input_email.setText(emp.get("email", ""))
                self.input_empid.setText(emp.get("id", ""))
                self.input_salary.setText(str(emp.get("salary", "")))
                self.input_days.setText(str(emp.get("days", "")))
                self.input_dept.setText(emp.get("department", ""))
                # Password not loaded for security
                QMessageBox.information(self, "Loaded", f"Employee '{key}' loaded.")
            else:
                QMessageBox.warning(self, "Not Found", f"Employee '{key}' not found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")

    def save_employee(self):
        key = self.input_name.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Username required.")
            return

        try:
            salary = float(self.input_salary.text().strip() or "0")
            days = int(self.input_days.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid salary or days.")
            return

        emp = {
            "name": key,
            "email": self.input_email.text().strip(),
            "id": self.input_empid.text().strip(),
            "salary": salary,
            "days": days,
            "department": self.input_dept.text().strip(),
            "created_at": datetime.now(),
            "status": "Active",
            "pending": True
        }

        password_text = self.input_password.text().strip()
        if password_text:
            salt = bcrypt.gensalt()
            emp['password'] = bcrypt.hashpw(password_text.encode(), salt).decode()
        else:
            if key in self.employees:
                emp['password'] = self.employees[key]['password']
            else:
                salt = bcrypt.gensalt()
                emp['password'] = bcrypt.hashpw(b"123", salt).decode()

        self.employees[key] = emp
        try:
            save_employees(self.employees)
            self.employees = load_employees()
            QMessageBox.information(self, "Saved", f"Employee '{key}' saved.")
            self.input_name.clear()
            self.input_email.clear()
            self.input_empid.clear()
            self.input_salary.clear()
            self.input_days.clear()
            self.input_dept.clear()
            self.input_password.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save employee: {str(e)}")

    def calculate_payroll_table(self):
        self.pay_table.setRowCount(0)
        for idx, (key, emp) in enumerate(self.employees.items()):
            salary = (emp.get("salary", 0) / 30) * emp.get("days", 0)
            self.pay_table.insertRow(idx)
            self.pay_table.setItem(idx, 0, QTableWidgetItem(emp.get("name", key)))
            self.pay_table.setItem(idx, 1, QTableWidgetItem(emp.get("id", "")))
            self.pay_table.setItem(idx, 2, QTableWidgetItem(str(emp.get("salary", 0))))
            self.pay_table.setItem(idx, 3, QTableWidgetItem(str(emp.get("days", 0))))
            self.pay_table.setItem(idx, 4, QTableWidgetItem(str(round(salary, 2))))

    def approve_payroll(self):
        try:
            save_payrolls(self.employees)
            self.employees = load_employees()
            QMessageBox.information(self, "Payroll Approved",
                                    "Payroll processed, saved to history, and employees notified.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to approve payroll: {str(e)}")

    def show_employees_view(self):
        self.clear_content()

        header = QHBoxLayout()
        title = QLabel("Employee Data")
        title.setStyleSheet("font-size:18px; font-weight:700;")
        header.addWidget(title)
        header.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)
        header_widget = QWidget()
        header_widget.setLayout(header)
        self.content_layout.addWidget(header_widget)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(7)
        self.emp_table.setHorizontalHeaderLabels(["Key", "Name", "ID", "Email", "Department", "Salary", "Actions"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.setRowCount(0)
        for idx, (key, emp) in enumerate(self.employees.items()):
            self.emp_table.insertRow(idx)
            self.emp_table.setItem(idx, 0, QTableWidgetItem(key))
            self.emp_table.setItem(idx, 1, QTableWidgetItem(emp.get("name", "")))
            self.emp_table.setItem(idx, 2, QTableWidgetItem(emp.get("id", "")))
            self.emp_table.setItem(idx, 3, QTableWidgetItem(emp.get("email", "")))
            self.emp_table.setItem(idx, 4, QTableWidgetItem(emp.get("department", "")))
            self.emp_table.setItem(idx, 5, QTableWidgetItem(str(emp.get("salary", ""))))
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("secondaryBtn")
            delete_btn.clicked.connect(lambda checked, k=key: self.delete_employee(k))
            self.emp_table.setCellWidget(idx, 6, delete_btn)
        self.emp_table.setStyleSheet("background-color: white; border-radius: 8px;")
        self.content_layout.addWidget(self.emp_table)

    def delete_employee(self, username):
        reply = QMessageBox.question(self, 'Confirm Delete', f"Are you sure you want to delete '{username}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                delete_employee(username)
                self.employees = load_employees()
                self.show_employees_view()
                QMessageBox.information(self, "Deleted", f"Employee '{username}' deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    def logout(self):
        self.close()
        self.login = AdminLogin()
        self.login.show()


# ------------------ EMPLOYEE LOGIN ------------------
class EmployeeLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Login")
        self.setGeometry(400, 200, 420, 320)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("👤 Employee Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a;")
        layout.addWidget(title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username (key you used when admin saved you)")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Employee Password")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        self.login_btn = QPushButton("Log In")
        self.login_btn.setObjectName("primaryBtn")
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self.check_login)
        layout.addWidget(self.login_btn)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.setFixedHeight(36)
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    def check_login(self):
        try:
            employees = load_employees()
            key = self.username.text().strip()
            if key in employees and bcrypt.checkpw(self.password.text().encode(),
                                                   employees[key].get("password", "").encode()):
                self.emp_view = EmployeeDashboard(key)
                self.emp_view.showMaximized()
                self.close()
            else:
                QMessageBox.warning(self, "Error", "Invalid Employee Credentials")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")

    def go_back(self):
        self.main = MainWindow()
        self.main.show()
        self.close()


# ------------------ EMPLOYEE DASHBOARD ------------------
class EmployeeDashboard(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Employee Payroll Dashboard")
        self.setGeometry(300, 100, 960, 640)

        try:
            self.employees = load_employees()
            if self.username not in self.employees:
                QMessageBox.warning(self, "Error", "Employee data not found.")
                self.close()
                return
            self.emp = self.employees[self.username]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load employee data: {str(e)}")
            self.close()
            return

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 0)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(12)
        self.content_area.setLayout(self.content_layout)
        main_layout.addWidget(self.content_area, 1)

        header = QHBoxLayout()
        header.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.clicked.connect(self.logout)
        header.addWidget(logout_btn)
        header_widget = QWidget()
        header_widget.setLayout(header)
        self.content_layout.addWidget(header_widget)

        self.show_dashboard_view()

    def create_sidebar(self):
        frame = QFrame()
        frame.setFixedWidth(220)
        frame.setStyleSheet(f"background-color: {PALETTE['sidebar']};")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        logo = QLabel("💰 SAL SURE")
        logo.setStyleSheet("font-size: 16px; font-weight: 700; color: white;")
        layout.addWidget(logo)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setObjectName("sidebarBtn")
        self.btn_dashboard.setFixedHeight(40)
        self.btn_dashboard.clicked.connect(self.show_dashboard_view)
        layout.addWidget(self.btn_dashboard)

        self.btn_payroll = QPushButton("Payroll Status")
        self.btn_payroll.setObjectName("sidebarBtn")
        self.btn_payroll.setFixedHeight(40)
        self.btn_payroll.clicked.connect(self.show_payroll_view)
        layout.addWidget(self.btn_payroll)

        self.btn_history = QPushButton("Pay History")
        self.btn_history.setObjectName("sidebarBtn")
        self.btn_history.setFixedHeight(40)
        self.btn_history.clicked.connect(self.show_pay_history_view)
        layout.addWidget(self.btn_history)

        layout.addStretch()
        user_label = QLabel(f"👤 {self.username}")
        user_label.setStyleSheet("color: rgba(255,255,255,0.9);")
        layout.addWidget(user_label)

        frame.setLayout(layout)
        return frame

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_dashboard_view(self):
        self.clear_content()

        welcome = QLabel(f"Welcome back, {self.emp.get('name', self.username)}! 👋")
        welcome.setStyleSheet("font-size:18px; font-weight:700;")
        self.content_layout.addWidget(welcome)

        info_frame = QFrame()
        info_frame.setProperty("class", "card")
        info_frame.setStyleSheet("padding: 12px;")
        info_layout = QGridLayout()
        info_layout.addWidget(QLabel("Employee ID:"), 0, 0)
        info_layout.addWidget(QLabel(self.emp.get("id", "")), 0, 1)
        info_layout.addWidget(QLabel("Email:"), 1, 0)
        info_layout.addWidget(QLabel(self.emp.get("email", "")), 1, 1)
        info_layout.addWidget(QLabel("Department:"), 2, 0)
        info_layout.addWidget(QLabel(self.emp.get("department", "Unknown")), 2, 1)
        info_layout.addWidget(QLabel("Status:"), 3, 0)
        info_layout.addWidget(QLabel(self.emp.get("status", "Active")), 3, 1)
        info_frame.setLayout(info_layout)
        self.content_layout.addWidget(info_frame)

        stats_row = QHBoxLayout()
        days_worked = self.emp.get("days", 0)
        cpb_attendance = CircularProgressBar(days_worked, 30, "Attendance", PALETTE['accent'])
        stats_row.addWidget(cpb_attendance)

        base_salary = self.emp.get("salary", 0)
        calculated_salary = (base_salary / 30) * days_worked
        tax = 0.15 * calculated_salary
        net_salary = calculated_salary - tax
        card1 = self.make_stat_card("Base Salary", f"₱{base_salary:.2f}")
        card2 = self.make_stat_card("Net Salary", f"₱{net_salary:.2f}")
        stats_row.addWidget(card1)
        stats_row.addWidget(card2)
        stats_widget = QWidget()
        stats_widget.setLayout(stats_row)
        self.content_layout.addWidget(stats_widget)

        pie = self.create_salary_pie_chart(calculated_salary, tax, net_salary)
        self.content_layout.addWidget(pie)

    def show_payroll_view(self):
        self.clear_content()

        title = QLabel("Payroll Status")
        title.setStyleSheet("font-size:16px; font-weight:700;")
        self.content_layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Base Salary", "Days Worked", "Net Salary"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(1)
        base_salary = self.emp.get("salary", 0)
        days_worked = self.emp.get("days", 0)
        calculated_salary = (base_salary / 30) * days_worked
        tax = 0.15 * calculated_salary
        net_salary = calculated_salary - tax
        table.setItem(0, 0, QTableWidgetItem(self.emp.get("id", "")))
        table.setItem(0, 1, QTableWidgetItem(f"₱{base_salary:.2f}"))
        table.setItem(0, 2, QTableWidgetItem(str(days_worked)))
        table.setItem(0, 3, QTableWidgetItem(f"₱{net_salary:.2f}"))
        table.setStyleSheet("background-color: white; border-radius: 8px;")
        self.content_layout.addWidget(table)

        tax_label = QLabel(f"Tax Deducted: 15% (₱{tax:.2f})")
        tax_label.setStyleSheet("font-size:14px; color: #ef4444;")
        self.content_layout.addWidget(tax_label)

        if self.emp.get('pending', False):
            pending_label = QLabel("Status: Pending Approval")
            pending_label.setStyleSheet("font-size:14px; color: #f59e0b;")
            self.content_layout.addWidget(pending_label)
        else:
            pending_label = QLabel("Status: Approved")
            pending_label.setStyleSheet("font-size:14px; color: #10b981;")
            self.content_layout.addWidget(pending_label)

    def show_pay_history_view(self):
        self.clear_content()

        title = QLabel("Pay History")
        title.setStyleSheet("font-size:16px; font-weight:700;")
        self.content_layout.addWidget(title)

        payrolls = load_payrolls(self.username)
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Processed At", "Gross", "Tax", "Net"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(payrolls))
        for idx, p in enumerate(payrolls):
            table.setItem(idx, 0, QTableWidgetItem(str(p['processed_at'])))
            table.setItem(idx, 1, QTableWidgetItem(f"₱{p['gross']:.2f}"))
            table.setItem(idx, 2, QTableWidgetItem(f"₱{p['tax']:.2f}"))
            table.setItem(idx, 3, QTableWidgetItem(f"₱{p['net']:.2f}"))
        table.setStyleSheet("background-color: white; border-radius: 8px;")
        self.content_layout.addWidget(table)

        if not payrolls:
            no_history = QLabel("No payroll history available.")
            no_history.setStyleSheet("color: #475569;")
            self.content_layout.addWidget(no_history)

    def make_stat_card(self, title, value):
        w = QFrame()
        w.setProperty("class", "card")
        w.setFixedSize(220, 100)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel(title))
        val = QLabel(value)
        val.setStyleSheet("font-weight:800; font-size:18px; color: #0f172a;")
        layout.addStretch()
        layout.addWidget(val)
        w.setLayout(layout)
        return w

    def create_salary_pie_chart(self, gross, tax, net):
        series = QPieSeries()
        # avoid zero-slice (charts look better)
        series.append("Tax", tax if tax > 0 else 1)
        series.append("Net Salary", net if net > 0 else 1)

        colors = ['#ef4444', '#10b981']
        for i, s in enumerate(series.slices()):
            s.setLabelVisible(True)
            s.setColor(QColor(colors[i]))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Salary Breakdown")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignRight)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(240)
        view.setStyleSheet("background-color: white; border-radius: 12px;")
        return view

    def logout(self):
        self.close()
        self.login = EmployeeLogin()
        self.login.show()


# ------------------ Run App ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())