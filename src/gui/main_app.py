"""
Main GUI Application for Student Attendance System
Giao diện chính cho hệ thống điểm danh học sinh
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import os
import sys
import numpy as np
import threading
import time
from datetime import datetime, date, timedelta
import pandas as pd

# Add parent directory to path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import DatabaseManager

class AttendanceSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Điểm danh Học sinh - Face Recognition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Variables
        self.current_session_id = None
        self.camera = None
        self.is_recognizing = False
        self.camera_thread = None
        
        # Face recognition variables
        self.face_cascade = None
        self.face_recognizer = None
        self.face_names = {}  # Dictionary to map IDs to names
        self.last_recognition_time = {}  # To prevent duplicate recognitions
        
        # Initialize face recognition
        self.init_face_recognition()
        
        # Setup GUI
        self.setup_gui()
        
    def init_face_recognition(self):
        """Initialize face recognition components"""
        try:
            # Load Haar cascade from assets folder
            # Current file: src/gui/main_app.py -> go up 3 levels to project root
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            cascade_path = os.path.join(project_root, 'assets', 'haarcascade_frontalface_default.xml')
            
            print(f"🔍 Looking for cascade at: {cascade_path}")
            print(f"   Exists: {os.path.exists(cascade_path)}")
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # Initialize numpy-based face recognition
            self.trained_faces = None
            self.trained_ids = None
            
            # Load training data if available
            if self.load_training_data():
                print("✅ Numpy-based face recognition initialized successfully")
            else:
                print("⚠️ No training data found - please train the model first")
            
            # Load names from database
            self.load_face_names()
            
        except Exception as e:
            print(f"⚠️ Face recognition initialization error: {e}")
            messagebox.showwarning("Cảnh báo", f"Không thể khởi tạo nhận diện khuôn mặt: {e}")
    
    def load_face_names(self):
        """Load student names for face recognition"""
        try:
            students = self.db.get_all_students()
            self.face_names = {}
            for student in students:
                # Use student database ID as the key
                self.face_names[student[0]] = student[2]  # student[0] = id, student[2] = full_name
            print(f"✅ Loaded {len(self.face_names)} student names for recognition")
        except Exception as e:
            print(f"❌ Error loading face names: {e}")
        
    def setup_gui(self):
        """Setup main GUI layout"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎓 HỆ THỐNG ĐIỂM DANH HỌC SINH",
            font=('Arial', 20, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_student_management_tab()
        self.create_attendance_tab()
        self.create_reports_tab()
        self.create_settings_tab()
        
    def create_student_management_tab(self):
        """Tạo tab quản lý học sinh"""
        student_frame = ttk.Frame(self.notebook)
        self.notebook.add(student_frame, text="👥 Quản lý Học sinh")
        
        # Left panel - Student list
        left_panel = ttk.LabelFrame(student_frame, text="Danh sách Học sinh", padding=10)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Class selection
        class_frame = tk.Frame(left_panel)
        class_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(class_frame, text="Chọn lớp:", font=('Arial', 10, 'bold')).pack(side='left')
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(class_frame, textvariable=self.class_var, state='readonly')
        self.class_combo.pack(side='left', padx=(10, 0), fill='x', expand=True)
        self.class_combo.bind('<<ComboboxSelected>>', self.load_students)
        
        # Student list
        columns = ('ID', 'Mã HS', 'Tên', 'Email', 'Điện thoại')
        self.student_tree = ttk.Treeview(left_panel, columns=columns, show='tree headings', height=15)
        
        for col in columns:
            self.student_tree.heading(col, text=col)
            self.student_tree.column(col, width=100)
            
        # Scrollbar for student list
        student_scrollbar = ttk.Scrollbar(left_panel, orient='vertical', command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=student_scrollbar.set)
        
        self.student_tree.pack(side='left', fill='both', expand=True)
        student_scrollbar.pack(side='right', fill='y')
        
        # Bind event for student selection
        self.student_tree.bind('<<TreeviewSelect>>', self.on_student_select)
        
        # Right panel - Student details and actions
        right_panel = ttk.LabelFrame(student_frame, text="Thông tin Học sinh", padding=10)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        
        # Student form
        form_frame = tk.Frame(right_panel)
        form_frame.pack(fill='x', pady=(0, 20))
        
        # Student ID
        tk.Label(form_frame, text="Mã học sinh:").grid(row=0, column=0, sticky='w', pady=2)
        self.student_id_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.student_id_var, width=30).grid(row=0, column=1, pady=2, padx=(10, 0))
        
        # Full name
        tk.Label(form_frame, text="Họ và tên:").grid(row=1, column=0, sticky='w', pady=2)
        self.full_name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.full_name_var, width=30).grid(row=1, column=1, pady=2, padx=(10, 0))
        
        # Email
        tk.Label(form_frame, text="Email:").grid(row=2, column=0, sticky='w', pady=2)
        self.email_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=2, column=1, pady=2, padx=(10, 0))
        
        # Phone
        tk.Label(form_frame, text="Điện thoại:").grid(row=3, column=0, sticky='w', pady=2)
        self.phone_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.phone_var, width=30).grid(row=3, column=1, pady=2, padx=(10, 0))
        
        # Class for new student
        tk.Label(form_frame, text="Lớp:").grid(row=4, column=0, sticky='w', pady=2)
        self.new_class_var = tk.StringVar()
        self.new_class_combo = ttk.Combobox(form_frame, textvariable=self.new_class_var, state='readonly', width=27)
        self.new_class_combo.grid(row=4, column=1, pady=2, padx=(10, 0))
        
        # Buttons
        button_frame = tk.Frame(right_panel)
        button_frame.pack(fill='x', pady=10)
        
        tk.Button(
            button_frame, 
            text="➕ Thêm Học sinh", 
            command=self.add_student,
            bg='#27ae60', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(fill='x', pady=2)
        
        tk.Button(
            button_frame, 
            text="📸 Thu thập Ảnh", 
            command=self.collect_face_data,
            bg='#3498db', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(fill='x', pady=2)
        
        tk.Button(
            button_frame, 
            text="🔄 Cập nhật", 
            command=self.update_student,
            bg='#f39c12', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(fill='x', pady=2)
        
        tk.Button(
            button_frame, 
            text="🗑️ Xóa", 
            command=self.delete_student,
            bg='#e74c3c', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(fill='x', pady=2)
        
        tk.Button(
            button_frame, 
            text="🧹 Xóa Form", 
            command=self.clear_student_form,
            bg='#95a5a6', 
            fg='white', 
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(fill='x', pady=2)
        
        # Load initial data
        self.load_classes()
        # Load students for first class if available
        if hasattr(self, 'class_var') and self.class_var.get():
            self.load_students()
        self.load_students()  # Load students for default class
        
    def create_attendance_tab(self):
        """Tạo tab điểm danh"""
        attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(attendance_frame, text="✅ Điểm danh")
        
        # Top panel - Session management
        session_panel = ttk.LabelFrame(attendance_frame, text="Quản lý Phiên điểm danh", padding=10)
        session_panel.pack(fill='x', padx=10, pady=(10, 5))
        
        # Session form
        session_form = tk.Frame(session_panel)
        session_form.pack(fill='x')
        
        tk.Label(session_form, text="Tên phiên:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.session_name_var = tk.StringVar(value=f"Điểm danh {datetime.now().strftime('%d/%m/%Y')}")
        tk.Entry(session_form, textvariable=self.session_name_var, width=20).grid(row=0, column=1, padx=(0, 20))
        
        tk.Label(session_form, text="Lớp:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.session_class_var = tk.StringVar()
        self.session_class_combo = ttk.Combobox(session_form, textvariable=self.session_class_var, state='readonly', width=15)
        self.session_class_combo['values'] = ('12A1', '12A2', '12A3', '12A4', '12A5')
        self.session_class_combo.set('12A1')  # Set default selection
        self.session_class_combo.grid(row=0, column=3, padx=(0, 20))
        
        tk.Button(
            session_form, 
            text="🚀 Bắt đầu Điểm danh",
            command=self.start_attendance_session,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=4, padx=10)
        
        tk.Button(
            session_form, 
            text="⏹️ Kết thúc",
            command=self.end_attendance_session,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=5, padx=10)
        
        # Middle panel - Camera view
        camera_panel = ttk.LabelFrame(attendance_frame, text="Camera Nhận diện", padding=10)
        camera_panel.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Camera control buttons
        camera_controls = tk.Frame(camera_panel)
        camera_controls.pack(fill='x', pady=(0, 10))
        
        tk.Button(
            camera_controls,
            text="📹 Bật Camera",
            command=self.start_camera,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            camera_controls,
            text="⏹️ Tắt Camera", 
            command=self.stop_camera,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            camera_controls,
            text="🤖 Bật Nhận diện",
            command=self.toggle_recognition,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=(0, 10))
        
        # Camera display
        self.camera_label = tk.Label(camera_panel, text="📷 Camera chưa bật\n\nClick 'Bật Camera' để bắt đầu", bg='black', fg='white', width=80, height=20, font=('Arial', 12))
        self.camera_label.pack(side='left', fill='both', expand=True)
        
        # Attendance list
        attendance_list_frame = tk.Frame(camera_panel)
        attendance_list_frame.pack(side='right', fill='y', padx=(10, 0))
        
        tk.Label(attendance_list_frame, text="Đã điểm danh:", font=('Arial', 12, 'bold')).pack()
        
        self.attendance_listbox = tk.Listbox(attendance_list_frame, width=30, height=15)
        self.attendance_listbox.pack(fill='both', expand=True)
        
        # Status panel
        status_panel = tk.Frame(attendance_frame)
        status_panel.pack(fill='x', padx=10, pady=(5, 10))
        
        self.status_label = tk.Label(
            status_panel, 
            text="Trạng thái: Chưa bắt đầu", 
            font=('Arial', 12, 'bold'),
            fg='blue'
        )
        self.status_label.pack(side='left')
        
        self.attendance_count_label = tk.Label(
            status_panel, 
            text="Đã điểm danh: 0", 
            font=('Arial', 12, 'bold'),
            fg='green'
        )
        self.attendance_count_label.pack(side='right')
        
    def create_reports_tab(self):
        """Tạo tab báo cáo"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="📊 Báo cáo")
        
        # Main container
        main_container = tk.Frame(reports_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Report options
        left_panel = ttk.LabelFrame(main_container, text="Tùy chọn Báo cáo", padding=10)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.configure(width=350)
        
        # Report type selection
        report_type_frame = tk.Frame(left_panel)
        report_type_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(report_type_frame, text="Loại báo cáo:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.report_type_var = tk.StringVar(value="daily")
        
        report_types = [
            ("📅 Báo cáo theo ngày", "daily"),
            ("📚 Báo cáo theo lớp", "class"),
            ("👤 Báo cáo theo học sinh", "student"),
            ("📈 Thống kê tổng hợp", "summary"),
            ("⏰ Phân tích xu hướng", "trends")
        ]
        
        for text, value in report_types:
            tk.Radiobutton(
                report_type_frame,
                text=text,
                variable=self.report_type_var,
                value=value,
                font=('Arial', 9),
                command=self.update_report_options
            ).pack(anchor='w', padx=20)
        
        # Date range selection
        date_frame = tk.Frame(left_panel)
        date_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(date_frame, text="Khoảng thời gian:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # From date
        from_frame = tk.Frame(date_frame)
        from_frame.pack(fill='x', pady=2)
        tk.Label(from_frame, text="Từ ngày:").pack(side='left')
        self.from_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        tk.Entry(from_frame, textvariable=self.from_date_var, width=12).pack(side='right')
        
        # To date  
        to_frame = tk.Frame(date_frame)
        to_frame.pack(fill='x', pady=2)
        tk.Label(to_frame, text="Đến ngày:").pack(side='left')
        self.to_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        tk.Entry(to_frame, textvariable=self.to_date_var, width=12).pack(side='right')
        
        # Quick date buttons
        quick_date_frame = tk.Frame(date_frame)
        quick_date_frame.pack(fill='x', pady=5)
        
        quick_dates = [
            ("Hôm nay", 0),
            ("7 ngày", 7),
            ("30 ngày", 30),
            ("90 ngày", 90)
        ]
        
        for text, days in quick_dates:
            tk.Button(
                quick_date_frame,
                text=text,
                command=lambda d=days: self.set_quick_date_range(d),
                bg='#ecf0f1',
                font=('Arial', 8),
                relief='groove'
            ).pack(side='left', padx=2, fill='x', expand=True)
        
        # Class filter (for relevant reports)
        self.class_filter_frame = tk.Frame(left_panel)
        self.class_filter_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(self.class_filter_frame, text="Lọc theo lớp:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.report_class_var = tk.StringVar()
        self.report_class_combo = ttk.Combobox(self.class_filter_frame, textvariable=self.report_class_var, state='readonly')
        self.report_class_combo.pack(fill='x', pady=2)
        
        # Student filter (for student reports)
        self.student_filter_frame = tk.Frame(left_panel)
        
        tk.Label(self.student_filter_frame, text="Chọn học sinh:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.report_student_var = tk.StringVar()
        self.report_student_combo = ttk.Combobox(self.student_filter_frame, textvariable=self.report_student_var, state='readonly')
        self.report_student_combo.pack(fill='x', pady=2)
        
        # Action buttons
        button_frame = tk.Frame(left_panel)
        button_frame.pack(fill='x', pady=15)
        
        tk.Button(
            button_frame,
            text="🔍 Xem Báo cáo",
            command=self.generate_report_preview,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            pady=8
        ).pack(fill='x', pady=(0, 5))
        
        tk.Button(
            button_frame,
            text="📊 Xuất Excel",
            command=self.export_excel_report,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            pady=8
        ).pack(fill='x', pady=(0, 5))
        
        tk.Button(
            button_frame,
            text="📈 Xem Biểu đồ",
            command=self.show_report_charts,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 12, 'bold'),
            pady=8
        ).pack(fill='x')
        
        # Right panel - Report display
        right_panel = ttk.LabelFrame(main_container, text="Kết quả Báo cáo", padding=10)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Report summary
        self.report_summary_frame = tk.Frame(right_panel)
        self.report_summary_frame.pack(fill='x', pady=(0, 10))
        
        # Report content area with scrollbar
        content_frame = tk.Frame(right_panel)
        content_frame.pack(fill='both', expand=True)
        
        # Treeview for displaying report data
        self.report_tree = ttk.Treeview(content_frame, show='headings', height=20)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.report_tree.yview)
        h_scrollbar = ttk.Scrollbar(content_frame, orient='horizontal', command=self.report_tree.xview)
        self.report_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.report_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize report options
        self.init_report_data()
        self.update_report_options()
        
    def create_settings_tab(self):
        """Tạo tab cài đặt"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Cài đặt")
        
        # Class management
        class_mgmt_frame = ttk.LabelFrame(settings_frame, text="Quản lý Lớp học", padding=10)
        class_mgmt_frame.pack(fill='x', padx=10, pady=10)
        
        class_form = tk.Frame(class_mgmt_frame)
        class_form.pack(fill='x')
        
        tk.Label(class_form, text="Tên lớp:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.new_class_name_var = tk.StringVar()
        tk.Entry(class_form, textvariable=self.new_class_name_var, width=20).grid(row=0, column=1, padx=(0, 20))
        
        tk.Label(class_form, text="Mã lớp:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.new_class_code_var = tk.StringVar()
        tk.Entry(class_form, textvariable=self.new_class_code_var, width=15).grid(row=0, column=3, padx=(0, 20))
        
        tk.Button(
            class_form, 
            text="➕ Thêm Lớp",
            command=self.add_class,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=4, padx=10)
        
        # Face Recognition Training
        face_mgmt_frame = ttk.LabelFrame(settings_frame, text="🤖 Quản lý Nhận diện Khuôn mặt", padding=10)
        face_mgmt_frame.pack(fill='x', padx=10, pady=10)
        
        # Training info
        info_text = """
📸 Quy trình nhận diện khuôn mặt:
1. Thêm học sinh vào hệ thống
2. Thu thập ảnh khuôn mặt (30 ảnh/học sinh)
3. Train model nhận diện
4. Sử dụng trong điểm danh
        """
        
        tk.Label(
            face_mgmt_frame,
            text=info_text,
            font=('Arial', 10),
            justify='left',
            fg='#2c3e50'
        ).pack(anchor='w', pady=(0, 10))
        
        # Training buttons
        training_buttons = tk.Frame(face_mgmt_frame)
        training_buttons.pack(fill='x')
        
        tk.Button(
            training_buttons,
            text="🧠 Train Face Recognition Model",
            command=self.train_face_model,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            training_buttons,
            text="📁 Mở thư mục Dataset",
            command=self.open_dataset_folder,
            bg='#f39c12',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            training_buttons,
            text="🔄 Reload Face Model",
            command=self.reload_face_model,
            bg='#16a085',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side='left')
        
    # === Event Handlers ===
    def load_classes(self):
        """Load danh sách lớp học"""
        try:
            classes = self.db.get_all_classes()
            class_list = [f"{cls[2]} - {cls[1]}" for cls in classes]  # code - name
            
            print(f"📚 Loaded {len(classes)} classes: {class_list}")
            
            # Update combo boxes that exist
            if hasattr(self, 'class_combo') and self.class_combo:
                self.class_combo['values'] = class_list
                if class_list:
                    self.class_combo.set(class_list[0])
                    self.class_var.set(class_list[0])
            
            if hasattr(self, 'new_class_combo') and self.new_class_combo:
                self.new_class_combo['values'] = class_list
                if class_list:
                    self.new_class_combo.set(class_list[0])
            
            if hasattr(self, 'session_class_combo') and self.session_class_combo:
                self.session_class_combo['values'] = class_list
                if class_list:
                    self.session_class_combo.set(class_list[0])
        except Exception as e:
            print(f"❌ Error loading classes: {e}")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách lớp: {e}")
            
    def load_students(self, event=None):
        """Load danh sách học sinh theo lớp"""
        if not self.class_var.get():
            return
            
        # Extract class ID from combo selection
        try:
            class_code = self.class_var.get().split(' - ')[0]
            classes = self.db.get_all_classes()
            class_id = None
            for cls in classes:
                if cls[2] == class_code:  # cls[2] is class_code
                    class_id = cls[0]  # cls[0] is id
                    break
            
            if class_id:
                students = self.db.get_students_by_class(class_id)
                
                # Clear existing items
                for item in self.student_tree.get_children():
                    self.student_tree.delete(item)
                
                # Add students to tree
                for student in students:
                    self.student_tree.insert('', 'end', values=(
                        student[0],  # id
                        student[1],  # student_id
                        student[2],  # full_name
                        student[4] or '',  # email
                        student[5] or ''   # phone
                    ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách học sinh: {e}")
            
    def add_student(self):
        """Thêm học sinh mới"""
        try:
            # Validate input
            if not all([self.student_id_var.get(), self.full_name_var.get(), self.new_class_var.get()]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin bắt buộc")
                return
            
            # Get class ID
            class_code = self.new_class_var.get().split(' - ')[0]
            classes = self.db.get_all_classes()
            class_id = None
            for cls in classes:
                if cls[2] == class_code:
                    class_id = cls[0]
                    break
            
            if not class_id:
                messagebox.showerror("Lỗi", "Không tìm thấy lớp học")
                return
            
            # Add student
            self.db.add_student(
                self.student_id_var.get(),
                self.full_name_var.get(),
                class_id,
                self.email_var.get(),
                self.phone_var.get()
            )
            
            # Clear form
            self.clear_student_form()
            
            # Reload student list
            self.load_students()
            
            messagebox.showinfo("Thành công", "Đã thêm học sinh thành công!")
            
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm học sinh: {e}")
            
    def clear_student_form(self):
        """Xóa form thông tin học sinh"""
        self.student_id_var.set('')
        self.full_name_var.set('')
        self.email_var.set('')
        self.phone_var.set('')
        
    def collect_face_data(self):
        """Thu thập dữ liệu khuôn mặt cho học sinh"""
        selection = self.student_tree.selection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn học sinh cần thu thập ảnh")
            return
        
        # Get selected student info
        item = self.student_tree.item(selection[0])
        student_data = item['values']
        student_id = student_data[0]  # Database ID
        student_code = student_data[1]  # Student code
        student_name = student_data[2]  # Full name
        
        # Confirm with user
        response = messagebox.askyesno(
            "Xác nhận", 
            f"Thu thập ảnh cho học sinh: {student_name} ({student_code})\n\n"
            "Hệ thống sẽ thu thập 30 ảnh khuôn mặt.\n"
            "Bạn có muốn tiếp tục không?"
        )
        
        if not response:
            return
        
        # Start face data collection
        self.start_face_collection(student_id, student_name)
        
    def update_student(self):
        """Cập nhật thông tin học sinh"""
        try:
            # Kiểm tra xem có học sinh nào được chọn không
            selected = self.student_tree.selection()
            if not selected:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn học sinh cần cập nhật")
                return
            
            # Lấy thông tin học sinh được chọn
            item = self.student_tree.item(selected[0])
            student_id = item['values'][0]  # ID column
            
            # Lấy thông tin hiện tại từ form
            student_code = self.student_id_var.get().strip()
            full_name = self.full_name_var.get().strip()
            email = self.email_var.get().strip()
            phone = self.phone_var.get().strip()
            class_name = self.new_class_var.get().strip()
            
            # Validation
            if not all([student_code, full_name]):
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ mã học sinh và họ tên")
                return
            
            # Tìm class_id từ class_name
            class_id = None
            if class_name:
                classes = self.db.get_all_classes()
                for cls in classes:
                    if cls[1] == class_name:  # class_name column
                        class_id = cls[0]
                        break
                
                if class_id is None:
                    messagebox.showerror("Lỗi", f"Không tìm thấy lớp '{class_name}'")
                    return
            
            # Xác nhận cập nhật
            confirm = messagebox.askyesno(
                "Xác nhận", 
                f"Bạn có chắc muốn cập nhật thông tin học sinh '{full_name}'?"
            )
            
            if not confirm:
                return
            
            # Thực hiện cập nhật
            success = self.db.update_student(
                student_id=student_id,  # This is the database ID
                student_code=student_code,  # This will be stored in student_id column
                full_name=full_name,
                class_id=class_id,
                email=email if email else None,
                phone=phone if phone else None
            )
            
            if success:
                messagebox.showinfo("Thành công", "Đã cập nhật thông tin học sinh thành công!")
                self.load_students()  # Refresh danh sách
                self.clear_student_form()  # Clear form
            else:
                messagebox.showwarning("Thông báo", "Không có thay đổi nào được thực hiện")
                
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật học sinh: {e}")
        
    def delete_student(self):
        """Xóa học sinh và tất cả dữ liệu liên quan"""
        try:
            # Kiểm tra xem có học sinh nào được chọn không
            selected = self.student_tree.selection()
            if not selected:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn học sinh cần xóa")
                return
            
            # Lấy thông tin học sinh được chọn
            item = self.student_tree.item(selected[0])
            student_id = item['values'][0]  # ID column
            student_name = item['values'][2]  # Name column
            
            # Xác nhận xóa với cảnh báo nghiêm trọng
            confirm = messagebox.askyesno(
                "⚠️ XÁC NHẬN XÓA", 
                f"CẢNH BÁO: Bạn sắp xóa học sinh '{student_name}'\n\n"
                f"Điều này sẽ xóa VĨNH VIỄN:\n"
                f"• Thông tin học sinh\n"
                f"• Tất cả ảnh khuôn mặt đã thu thập\n"
                f"• Lịch sử điểm danh\n"
                f"• Dữ liệu nhận diện\n\n"
                f"Bạn có CHẮC CHẮN muốn tiếp tục?",
                icon='warning'
            )
            
            if not confirm:
                return
            
            # Xác nhận lần 2
            final_confirm = messagebox.askyesno(
                "⚠️ XÁC NHẬN CUỐI CÙNG",
                f"Đây là cảnh báo cuối cùng!\n\n"
                f"Xóa học sinh '{student_name}' sẽ KHÔNG THỂ HOÀN TÁC!\n\n"
                f"Bạn có thực sự muốn xóa?",
                icon='warning'
            )
            
            if not final_confirm:
                return
            
            # Thực hiện xóa
            result = self.db.delete_student(student_id)
            
            # Hiển thị kết quả
            message = f"✅ Đã xóa học sinh '{result['full_name']}' thành công!\n\n"
            message += f"📊 Chi tiết:\n"
            message += f"• Bản ghi điểm danh: {result['attendance_records']}\n"
            message += f"• Dữ liệu nhận diện: {result['face_encodings']}\n"
            message += f"• Ảnh khuôn mặt: {result['face_images']}"
            
            messagebox.showinfo("Xóa thành công", message)
            
            # Refresh danh sách và clear form
            self.load_students()
            self.clear_student_form()
            
            # Reload face model nếu có thay đổi về ảnh
            if result['face_images'] > 0:
                try:
                    self.reload_face_model()
                except:
                    pass  # Ignore errors in model reload
                
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa học sinh: {e}")
        
    def add_class(self):
        """Thêm lớp học mới"""
        try:
            if not all([self.new_class_name_var.get(), self.new_class_code_var.get()]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin lớp học")
                return
            
            self.db.add_class(
                self.new_class_name_var.get(),
                self.new_class_code_var.get()
            )
            
            # Clear form
            self.new_class_name_var.set('')
            self.new_class_code_var.set('')
            
            # Reload classes
            self.load_classes()
            
            messagebox.showinfo("Thành công", "Đã thêm lớp học thành công!")
            
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm lớp học: {e}")
            
    def start_attendance_session(self):
        """Bắt đầu phiên điểm danh"""
        try:
            if not all([self.session_name_var.get(), self.session_class_var.get()]):
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin phiên điểm danh")
                return
            
            # Get class ID - handle both database format and predefined format
            selected_class = self.session_class_var.get()
            classes = self.db.get_all_classes()
            class_id = None
            
            # Check if it's database format "code - name" or just class name
            if ' - ' in selected_class:
                class_code = selected_class.split(' - ')[0]
                for cls in classes:
                    if cls[2] == class_code:
                        class_id = cls[0]
                        break
            else:
                # It's a predefined class name (12A1, 12A2, etc.) - find or create
                for cls in classes:
                    if cls[1] == selected_class or cls[2] == selected_class:
                        class_id = cls[0]
                        break
                
                # If class doesn't exist, create it
                if not class_id:
                    try:
                        class_id = self.db.add_class(selected_class, selected_class, f"Lớp {selected_class}")
                    except ValueError:
                        # Class already exists but wasn't found - try again
                        classes = self.db.get_all_classes()
                        for cls in classes:
                            if cls[1] == selected_class or cls[2] == selected_class:
                                class_id = cls[0]
                                break
            
            if not class_id:
                messagebox.showerror("Lỗi", "Không thể tạo hoặc tìm thấy lớp học")
                return
            
            # Create attendance session
            self.current_session_id = self.db.create_attendance_session(
                self.session_name_var.get(),
                class_id,
                date.today().isoformat(),
                datetime.now().strftime('%H:%M:%S')
            )
            
            self.status_label.config(text="Trạng thái: Đang điểm danh", fg='green')
            
            # Clear attendance list and reset recognition times
            self.attendance_listbox.delete(0, tk.END)
            self.last_recognition_time.clear()
            
            # Reload face names in case new students were added
            self.load_face_names()
            
            messagebox.showinfo("Thành công", "Đã bắt đầu phiên điểm danh!\nBạn có thể bật camera để nhận diện khuôn mặt.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể bắt đầu phiên điểm danh: {e}")
            
    def end_attendance_session(self):
        """Kết thúc phiên điểm danh"""
        if self.current_session_id:
            # Stop recognition and camera
            self.is_recognizing = False
            
            self.db.end_attendance_session(self.current_session_id)
            self.current_session_id = None
            self.status_label.config(text="Trạng thái: Đã kết thúc", fg='red')
            
            # Update attendance count
            count = self.attendance_listbox.size()
            self.attendance_count_label.config(text=f"Tổng điểm danh: {count}")
            
            messagebox.showinfo("Thông báo", "Đã kết thúc phiên điểm danh!")
        else:
            messagebox.showwarning("Cảnh báo", "Không có phiên điểm danh nào đang hoạt động")
    
    # === Face Recognition Methods ===
    def convert_to_ascii(self, text):
        """Convert Vietnamese text to ASCII for OpenCV display"""
        # Vietnamese character mapping
        vietnamese_map = {
            'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
            'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
            'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
            'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
            'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
            'đ': 'd', 'Đ': 'D',
            # Uppercase
            'À': 'A', 'Á': 'A', 'Ạ': 'A', 'Ả': 'A', 'Ã': 'A',
            'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ậ': 'A', 'Ẩ': 'A', 'Ẫ': 'A',
            'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ặ': 'A', 'Ẳ': 'A', 'Ẵ': 'A',
            'È': 'E', 'É': 'E', 'Ẹ': 'E', 'Ẻ': 'E', 'Ẽ': 'E',
            'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ệ': 'E', 'Ể': 'E', 'Ễ': 'E',
            'Ì': 'I', 'Í': 'I', 'Ị': 'I', 'Ỉ': 'I', 'Ĩ': 'I',
            'Ò': 'O', 'Ó': 'O', 'Ọ': 'O', 'Ỏ': 'O', 'Õ': 'O',
            'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ộ': 'O', 'Ổ': 'O', 'Ỗ': 'O',
            'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ợ': 'O', 'Ở': 'O', 'Ỡ': 'O',
            'Ù': 'U', 'Ú': 'U', 'Ụ': 'U', 'Ủ': 'U', 'Ũ': 'U',
            'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ự': 'U', 'Ử': 'U', 'Ữ': 'U',
            'Ỳ': 'Y', 'Ý': 'Y', 'Ỵ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y'
        }
        
        # Convert each character
        result = ''
        for char in text:
            result += vietnamese_map.get(char, char)
        
        return result

    def load_training_data(self):
        """Load training data từ numpy files"""
        try:
            # Training data is in project_root/data/trainer/
            # Current file: src/gui/main_app.py -> go up 2 levels to project root  
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            trainer_dir = os.path.join(project_root, 'data', 'trainer')
            faces_path = os.path.join(trainer_dir, 'faces_data.npy')
            ids_path = os.path.join(trainer_dir, 'ids_data.npy')
            
            # Check training data files
            print(f"🔍 Loading training data from: {trainer_dir}")
            
            if os.path.exists(faces_path) and os.path.exists(ids_path):
                self.trained_faces = np.load(faces_path, allow_pickle=True)
                self.trained_ids = np.load(ids_path, allow_pickle=True)
                print(f"✅ Training data loaded: {len(self.trained_faces)} faces, {len(np.unique(self.trained_ids))} students")
                return True
            else:
                print("❌ Training data not found")
                self.trained_faces = None
                self.trained_ids = None
                return False
                
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            self.trained_faces = None
            self.trained_ids = None
            return False

    def recognize_face(self, face_roi):
        """Nhận diện khuôn mặt sử dụng thuật toán từ 03_face_recognition_fixed.py"""
        try:
            # Load training data if not already loaded
            if not hasattr(self, 'trained_faces') or self.trained_faces is None:
                self.load_training_data()
            
            if self.trained_faces is None or len(self.trained_faces) == 0:
                return "No Training Data", 0
            
            # Convert to grayscale if needed
            if len(face_roi.shape) == 3:
                face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Use the same algorithm as 03_face_recognition_fixed.py
            best_match_id = 0
            best_confidence = float('inf')
            
            for i, stored_face in enumerate(self.trained_faces):
                try:
                    # Resize both images to same size for comparison
                    target_size = min(face_roi.shape[0], face_roi.shape[1], 
                                    stored_face.shape[0], stored_face.shape[1])
                    
                    if target_size > 20:  # Minimum size check from original
                        face_resized = cv2.resize(face_roi, (target_size, target_size))
                        stored_resized = cv2.resize(stored_face, (target_size, target_size))
                        
                        # Calculate mean absolute difference (lower is better)
                        diff = np.mean(np.abs(face_resized.astype(float) - stored_resized.astype(float)))
                        
                        if diff < best_confidence:
                            best_confidence = diff
                            best_match_id = self.trained_ids[i]
                            
                except Exception as e:
                    print(f"Error comparing face {i}: {e}")
                    continue
            
            # Convert to percentage confidence using original formula
            confidence = max(0, 100 - (best_confidence / 255 * 100))
            

            
            # Recognition threshold (same as original: 50%)
            if confidence > 50:  # Threshold for recognition
                name = self.face_names.get(best_match_id, f"Student_{best_match_id}")

                return name, 100 - confidence  # Return as error rate for consistency
            else:

                return "Unknown", 100 - confidence
                
        except Exception as e:
            print(f"Face recognition error: {e}")
            return "Unknown", 0

    # === Camera and Face Recognition Methods ===
    def start_camera(self):
        """Bắt đầu camera"""
        try:
            if self.camera is None:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    messagebox.showerror("Lỗi", "Không thể mở camera")
                    self.camera = None
                    return
                
                # Start camera thread
                self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
                self.camera_thread.start()
                
                print("✅ Camera started successfully")
            else:
                messagebox.showinfo("Thông báo", "Camera đã được bật")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể bật camera: {e}")
    
    def stop_camera(self):
        """Dừng camera"""
        try:
            if self.camera is not None:
                self.camera.release()
                self.camera = None
                self.is_recognizing = False
                
                # Reset camera display
                self.camera_label.config(
                    image='',
                    text="📷 Camera đã tắt\n\nClick 'Bật Camera' để bắt đầu",
                    bg='black',
                    fg='white'
                )
                self.camera_label.image = None
                
                print("✅ Camera stopped")
            else:
                messagebox.showinfo("Thông báo", "Camera chưa được bật")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi tắt camera: {e}")
    
    def toggle_recognition(self):
        """Bật/tắt nhận diện khuôn mặt"""
        if self.camera is None:
            messagebox.showwarning("Cảnh báo", "Vui lòng bật camera trước")
            return
        
        if not self.current_session_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng bắt đầu phiên điểm danh trước")
            return
        
        self.is_recognizing = not self.is_recognizing
        if self.is_recognizing:
            print("✅ Face recognition enabled")
            messagebox.showinfo("Thông báo", "Đã bật nhận diện khuôn mặt")
        else:
            print("⏸️ Face recognition disabled")
            messagebox.showinfo("Thông báo", "Đã tắt nhận diện khuôn mặt")
    
    def update_camera(self):
        """Cập nhật hình ảnh camera liên tục"""
        while self.camera is not None:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process face recognition if enabled
                if self.is_recognizing and self.current_session_id:
                    frame = self.process_face_recognition(frame)
                
                # Convert frame to display format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_pil = frame_pil.resize((640, 480), Image.Resampling.LANCZOS)
                frame_tk = ImageTk.PhotoImage(frame_pil)
                
                # Update camera display
                self.camera_label.config(image=frame_tk, text='')
                self.camera_label.image = frame_tk
                
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Camera update error: {e}")
                break
    
    def process_face_recognition(self, frame):
        """Xử lý nhận diện khuôn mặt"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
            
            for (x, y, w, h) in faces:
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Perform face recognition using numpy-based matching
                roi_gray = gray[y:y+h, x:x+w]
                name, confidence = self.recognize_face(roi_gray)
                

                
                # Check if we got a valid recognition
                if name != "Unknown" and name != "No Training Data":
                    # Extract ID from name if possible
                    try:
                        if name.startswith("Student_"):
                            id_ = int(name.split("_")[1])
                        else:
                            # Try to find ID from face_names
                            id_ = None
                            for student_id, student_name in self.face_names.items():
                                if student_name == name:
                                    id_ = student_id
                                    break
                            if id_ is None:
                                id_ = 0  # Default ID for unknown mapping
                        
                        # Calculate display confidence (higher is better for user display)
                        display_confidence = 100 - confidence
                        confidence_text = f"{display_confidence:.1f}%"
                        
                        # Record attendance if not recently recorded
                        current_time = time.time()
                        if (id_ not in self.last_recognition_time or 
                            current_time - self.last_recognition_time[id_] > 5):  # 5 second cooldown
                            
                            self.record_student_attendance(id_, display_confidence, name)
                            self.last_recognition_time[id_] = current_time
                        
                        # Convert Vietnamese name to ASCII for display
                        display_name = self.convert_to_ascii(name)
                        
                        # Display name and confidence
                        cv2.putText(frame, f"{display_name}", (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        cv2.putText(frame, confidence_text, (x+5, y+h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                    except Exception as e:
                        print(f"Error processing recognition result: {e}")
                        cv2.putText(frame, "Unknown", (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    # Display the error message from recognition
                    display_text = "No Model" if name == "No Training Data" else "Unknown"
                    cv2.putText(frame, display_text, (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255) if name == "No Training Data" else (0, 0, 255), 2)
            
            # Add status text
            status_text = "Recognition: ON" if self.is_recognizing else "Recognition: OFF"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if self.is_recognizing else (0, 0, 255), 2)
            
        except Exception as e:
            print(f"Face recognition error: {e}")
        
        return frame
    
    def record_student_attendance(self, student_id, confidence, student_name):
        """Ghi nhận điểm danh cho học sinh"""
        try:
            if self.current_session_id:
                # Record in database
                self.db.record_attendance(
                    self.current_session_id,
                    student_id,
                    100 - confidence,  # Convert to positive confidence
                    'present'
                )
                
                # Update attendance list in GUI (GUI supports Unicode, so use original name)
                timestamp = datetime.now().strftime('%H:%M:%S')
                attendance_text = f"{timestamp} - {student_name}"
                
                self.attendance_listbox.insert(0, attendance_text)
                
                # Update attendance count
                count = self.attendance_listbox.size()
                self.attendance_count_label.config(text=f"Đã điểm danh: {count}")
                
                print(f"✅ Attendance recorded: {student_name} (ID: {student_id})")
                
        except Exception as e:
            print(f"❌ Error recording attendance: {e}")
    
    # === Face Training Methods ===
    def train_face_model(self):
        """Train face recognition model từ các ảnh đã thu thập - Sử dụng file training có sẵn"""
        try:
            # Dataset and trainer are in project_root/data/
            # __file__ is in src/gui/main_app.py, so we need 3 dirname() to get to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            dataset_dir = os.path.join(project_root, 'data', 'dataset')
            trainer_dir = os.path.join(project_root, 'data', 'trainer')
            
            # Check if dataset exists
            if not os.path.exists(dataset_dir) or not os.listdir(dataset_dir):
                messagebox.showwarning("Cảnh báo", "Không tìm thấy ảnh trong thư mục dataset!\nVui lòng thu thập ảnh trước.")
                return
            
            # Confirm training
            response = messagebox.askyesno(
                "Xác nhận Training", 
                "Sử dụng training script có sẵn để train face model?\n\n"
                "Quá trình này sẽ tạo ra numpy arrays để nhận diện khuôn mặt.\n"
                "Thời gian training tùy thuộc vào số lượng ảnh."
            )
            
            if not response:
                return
            
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Training Face Model")
            progress_window.geometry("400x200")
            progress_window.configure(bg='#2c3e50')
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            tk.Label(
                progress_window,
                text="🧠 Training Face Recognition Model",
                font=('Arial', 14, 'bold'),
                fg='white',
                bg='#2c3e50',
                pady=20
            ).pack()
            
            progress_label = tk.Label(
                progress_window,
                text="Đang xử lý ảnh...",
                font=('Arial', 12),
                fg='white',
                bg='#2c3e50'
            )
            progress_label.pack(pady=10)
            
            # Start training in thread
            training_thread = threading.Thread(
                target=self.perform_training,
                args=(dataset_dir, trainer_dir, progress_label, progress_window),
                daemon=True
            )
            training_thread.start()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể bắt đầu training: {e}")
    
    def perform_training(self, dataset_dir, trainer_dir, progress_label, progress_window):
        """Thực hiện training sử dụng logic từ 02_face_training_fixed.py"""
        try:
            # Create trainer directory
            os.makedirs(trainer_dir, exist_ok=True)
            
            progress_label.config(text="Đang xử lý ảnh từ dataset...")
            
            # Use the same logic as 02_face_training_fixed.py
            faces = []
            ids = []
            
            image_paths = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.endswith('.jpg')]
            
            if not image_paths:
                messagebox.showerror("Lỗi", "Không tìm thấy file ảnh (.jpg) trong dataset!")
                progress_window.destroy()
                return
            
            progress_label.config(text=f"Đang xử lý {len(image_paths)} ảnh...")
            
            for image_path in image_paths:
                try:
                    # Convert to grayscale using PIL (same as original script)
                    from PIL import Image
                    pil_img = Image.open(image_path).convert('L')
                    img_numpy = np.array(pil_img, 'uint8')
                    
                    # Get ID from filename (format: User.ID.count.jpg)
                    filename = os.path.basename(image_path)
                    user_id = int(filename.split(".")[1])
                    
                    # Use the whole face image (already cropped from dataset creation)
                    faces.append(img_numpy)
                    ids.append(user_id)
                    
                    print(f"Processed: {filename} -> ID: {user_id}")
                    
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    continue
            
            if not faces:
                messagebox.showerror("Lỗi", "Không tìm thấy ảnh hợp lệ để training!")
                progress_window.destroy()
                return
            
            progress_label.config(text=f"Đang lưu training data...")
            
            # Convert to numpy arrays (same as original script)
            faces_array = np.array(faces, dtype=object)  # Use object dtype for variable-sized arrays
            ids_array = np.array(ids)
            
            # Save the training data as numpy files
            np.save(os.path.join(trainer_dir, 'faces_data.npy'), faces_array)
            np.save(os.path.join(trainer_dir, 'ids_data.npy'), ids_array)
            
            progress_label.config(text="Training hoàn thành!")
            
            # Get unique IDs
            unique_ids = np.unique(ids_array)
            
            # Show success message
            messagebox.showinfo(
                "Training Thành công", 
                f"✅ Training hoàn thành!\n\n"
                f"📊 Thống kê:\n"
                f"• Tổng số ảnh: {len(faces)}\n"
                f"• Số học sinh: {len(unique_ids)}\n"
                f"• ID học sinh: {list(unique_ids)}\n\n"
                f"📁 Files đã tạo:\n"
                f"• data/trainer/faces_data.npy\n"
                f"• data/trainer/ids_data.npy\n\n"
                f"Hệ thống sử dụng numpy-based matching\n"
                f"(không cần opencv-contrib-python)"
            )
            
            # Reload the face recognition system
            self.load_face_names()
            self.load_training_data()  # Reload training data
            
            progress_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Lỗi Training", f"Lỗi trong quá trình training: {e}")
            if progress_window.winfo_exists():
                progress_window.destroy()
    
    def open_dataset_folder(self):
        """Mở thư mục dataset"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            dataset_dir = os.path.join(project_root, 'data', 'dataset')
            os.makedirs(dataset_dir, exist_ok=True)
            
            # Open folder in file explorer
            if os.name == 'nt':  # Windows
                os.startfile(dataset_dir)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{dataset_dir}"' if sys.platform == 'darwin' else f'xdg-open "{dataset_dir}"')
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục dataset: {e}")
    
    def reload_face_model(self):
        """Reload face recognition model"""
        try:
            self.init_face_recognition()
            self.load_face_names()
            messagebox.showinfo("Thành công", "✅ Đã reload face recognition model!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể reload model: {e}")
    
    def create_face_data_backup(self, dataset_dir, trainer_dir):
        """Tạo backup dữ liệu ảnh khi không có face recognizer"""
        try:
            os.makedirs(trainer_dir, exist_ok=True)
            
            # Create simple data backup
            faces = []
            ids = []
            
            for filename in os.listdir(dataset_dir):
                if filename.endswith('.jpg'):
                    try:
                        parts = filename.split('.')
                        if len(parts) >= 3 and parts[0] == 'User':
                            user_id = int(parts[1])
                            
                            # Load image
                            img_path = os.path.join(dataset_dir, filename)
                            face_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                            
                            if face_img is not None:
                                faces.append(face_img)
                                ids.append(user_id)
                    
                    except (ValueError, IndexError):
                        continue
            
            # Save face data for future use
            if faces:
                np.save(os.path.join(trainer_dir, 'faces_data.npy'), faces)
                np.save(os.path.join(trainer_dir, 'ids_data.npy'), ids)
                
                messagebox.showinfo(
                    "Backup hoàn thành", 
                    f"✅ Đã backup {len(faces)} ảnh từ {len(set(ids))} học sinh.\n\n"
                    "Hệ thống sẽ chỉ sử dụng face detection.\n"
                    "Để có đầy đủ face recognition, vui lòng cài đặt opencv-contrib-python."
                )
            else:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy ảnh hợp lệ để backup!")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo backup: {e}")
    
    # === Face Data Collection Methods ===
    def start_face_collection(self, student_id, student_name):
        """Bắt đầu thu thập dữ liệu khuôn mặt cho học sinh"""
        try:
            # Check if camera is available
            collection_camera = cv2.VideoCapture(0)
            if not collection_camera.isOpened():
                messagebox.showerror("Lỗi", "Không thể mở camera để thu thập ảnh")
                return
            
            # Create dataset directory if it doesn't exist  
            # __file__ is in src/gui/main_app.py, so we need 3 dirname() to get to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            dataset_dir = os.path.join(project_root, 'data', 'dataset')
            os.makedirs(dataset_dir, exist_ok=True)
            
            # Initialize variables for face collection
            face_id = student_id  # Use database ID as face ID
            count = 0
            max_samples = 30
            
            # Create a new window for face collection
            collection_window = tk.Toplevel(self.root)
            collection_window.title(f"Thu thập ảnh - {student_name}")
            collection_window.geometry("800x600")
            collection_window.configure(bg='#2c3e50')
            
            # Title
            title_label = tk.Label(
                collection_window,
                text=f"📸 Thu thập ảnh khuôn mặt\n{student_name}",
                font=('Arial', 16, 'bold'),
                fg='white',
                bg='#2c3e50',
                pady=20
            )
            title_label.pack()
            
            # Progress info
            self.progress_label = tk.Label(
                collection_window,
                text=f"Đã thu thập: 0/{max_samples} ảnh",
                font=('Arial', 12, 'bold'),
                fg='white',
                bg='#2c3e50'
            )
            self.progress_label.pack(pady=10)
            
            # Camera display for collection
            self.collection_label = tk.Label(collection_window, bg='black')
            self.collection_label.pack(padx=20, pady=10)
            
            # Instructions
            instruction_text = """
🔸 Hướng dẫn thu thập ảnh:
• Nhìn thẳng vào camera
• Từ từ xoay đầu sang trái, phải, lên, xuống
• Thay đổi biểu cảm (cười, nghiêm túc, ...)
• Đảm bảo ánh sáng đầy đủ
• Tránh che mặt bằng tay hoặc vật dụng
            """
            
            instruction_label = tk.Label(
                collection_window,
                text=instruction_text,
                font=('Arial', 10),
                fg='white',
                bg='#2c3e50',
                justify='left'
            )
            instruction_label.pack(pady=10)
            
            # Control buttons
            button_frame = tk.Frame(collection_window, bg='#2c3e50')
            button_frame.pack(pady=10)
            
            def close_collection():
                nonlocal collection_camera
                if collection_camera:
                    collection_camera.release()
                collection_window.destroy()
                messagebox.showinfo("Thông báo", f"Đã thu thập {count} ảnh cho {student_name}")
            
            tk.Button(
                button_frame,
                text="❌ Dừng thu thập",
                command=close_collection,
                bg='#e74c3c',
                fg='white',
                font=('Arial', 12, 'bold'),
                padx=20
            ).pack(side='left', padx=10)
            
            # Start collection thread
            collection_thread = threading.Thread(
                target=self.collect_face_samples,
                args=(collection_camera, face_id, student_name, max_samples, collection_window),
                daemon=True
            )
            collection_thread.start()
            
            # Handle window close
            collection_window.protocol("WM_DELETE_WINDOW", close_collection)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể bắt đầu thu thập ảnh: {e}")
    
    def collect_face_samples(self, camera, face_id, student_name, max_samples, window):
        """Thu thập các mẫu ảnh khuôn mặt"""
        count = 0
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        dataset_dir = os.path.join(project_root, 'data', 'dataset')
        
        while count < max_samples and camera.isOpened():
            try:
                ret, frame = camera.read()
                if not ret:
                    break
                
                # Flip frame horizontally
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    
                    # Increment count (same logic as original 01_face_dataset.py)
                    count += 1
                    
                    # Extract and save face region immediately (like original)
                    face_img = gray[y:y+h, x:x+w]
                    
                    # Save image with original naming convention
                    img_name = f"User.{face_id}.{count}.jpg"
                    img_path = os.path.join(dataset_dir, img_name)
                    cv2.imwrite(img_path, face_img)
                    
                    print(f"📸 Saved: {img_name}")
                    
                    # Add delay to get variety in poses (like original dataset collection)
                    time.sleep(0.2)  # 200ms delay between captures
                    
                    # Break if we have enough samples
                    if count >= max_samples:
                        break
                    
                    # Update progress
                    if hasattr(self, 'progress_label'):
                        self.progress_label.config(text=f"Đã thu thập: {count}/{max_samples} ảnh")
                    
                    # Add text to frame
                    cv2.putText(frame, f"Sample: {count}/{max_samples}", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Convert and display frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_pil = frame_pil.resize((640, 480), Image.Resampling.LANCZOS)
                frame_tk = ImageTk.PhotoImage(frame_pil)
                
                # Update display if window still exists
                if hasattr(self, 'collection_label') and self.collection_label.winfo_exists():
                    self.collection_label.config(image=frame_tk)
                    self.collection_label.image = frame_tk
                
                time.sleep(0.1)  # Small delay between captures
                
                # Break if we have enough samples or window is closed
                if count >= max_samples or not window.winfo_exists():
                    break
                    
            except Exception as e:
                print(f"Error in face collection: {e}")
                break
        
        # Cleanup
        camera.release()
        
        # Show completion message
        if count >= max_samples:
            messagebox.showinfo(
                "Hoàn thành", 
                f"✅ Đã thu thập đủ {max_samples} ảnh cho {student_name}!\n\n"
                "Bây giờ bạn có thể train model để nhận diện học sinh này."
            )
        
        # Close collection window
        if window.winfo_exists():
            window.destroy()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.release()
    
    def on_student_select(self, event):
        """Xử lý khi chọn học sinh từ danh sách"""
        try:
            selected = self.student_tree.selection()
            if not selected:
                return
            
            # Lấy thông tin học sinh được chọn
            item = self.student_tree.item(selected[0])
            student_db_id = item['values'][0]  # ID cột đầu tiên trong TreeView
            
            # Lấy thông tin chi tiết từ database
            student = self.db.get_student_by_id(student_db_id)
            if student:
                # Fill form với thông tin học sinh
                # student structure: (id, student_id, full_name, class_id, email, phone, address, photo_path, is_active, created_at, class_name, class_code)
                self.student_id_var.set(student[1] or '')   # student_id
                self.full_name_var.set(student[2] or '')    # full_name
                self.email_var.set(student[4] or '')        # email
                self.phone_var.set(student[5] or '')        # phone
                
                # Set class in combobox
                if student[10]:  # class_name
                    self.new_class_var.set(student[10])
                else:
                    self.new_class_var.set('')
        except Exception as e:
            print(f"Error loading student details: {e}")
            messagebox.showerror("Lỗi", f"Không thể tải thông tin học sinh: {e}")
    
    def clear_student_form(self):
        """Xóa tất cả thông tin trong form học sinh"""
        self.student_id_var.set('')
        self.full_name_var.set('')
        self.email_var.set('')
        self.phone_var.set('')
        self.new_class_var.set('')
        
        # Clear selection in tree
        for item in self.student_tree.selection():
            self.student_tree.selection_remove(item)
    
    # =============================================================================
    # REPORTS FUNCTIONALITY
    # =============================================================================
    
    def init_report_data(self):
        """Initialize report data and options"""
        try:
            # Import report generator
            from reports.report_generator import AttendanceReportGenerator
            
            # Initialize report generator
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(project_root, 'data', 'attendance.db')
            self.report_generator = AttendanceReportGenerator(db_path)
            
            # Load classes for filter
            classes = self.db.get_all_classes()
            class_names = ["Tất cả lớp"] + [f"{cls[1]} - {cls[2]}" for cls in classes]
            self.report_class_combo['values'] = class_names
            if class_names:
                self.report_class_combo.set(class_names[0])
                
            # Load students for filter
            students = self.db.get_all_students()
            student_names = ["Tất cả học sinh"] + [f"{student[2]} ({student[1]})" for student in students]
            self.report_student_combo['values'] = student_names
            if student_names:
                self.report_student_combo.set(student_names[0])
                
        except Exception as e:
            print(f"❌ Error initializing report data: {e}")
            messagebox.showerror("Lỗi", f"Không thể khởi tạo module báo cáo: {e}")
    
    def update_report_options(self):
        """Update report options based on selected type"""
        report_type = self.report_type_var.get()
        
        # Hide all optional frames first
        self.class_filter_frame.pack_forget()
        self.student_filter_frame.pack_forget()
        
        # Show relevant options based on report type
        if report_type in ["class", "summary"]:
            self.class_filter_frame.pack(fill='x', pady=(0, 15))
        elif report_type == "student":
            self.class_filter_frame.pack(fill='x', pady=(0, 15))
            self.student_filter_frame.pack(fill='x', pady=(0, 15))
    
    def set_quick_date_range(self, days):
        """Set quick date range"""
        end_date = datetime.now()
        if days == 0:  # Today
            start_date = end_date
        else:
            start_date = end_date - timedelta(days=days)
        
        self.from_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.to_date_var.set(end_date.strftime('%Y-%m-%d'))
    
    def generate_report_preview(self):
        """Generate and display report preview"""
        try:
            if not hasattr(self, 'report_generator'):
                self.init_report_data()
            
            report_type = self.report_type_var.get()
            start_date = self.from_date_var.get()
            end_date = self.to_date_var.get()
            
            # Validate dates
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ! Sử dụng YYYY-MM-DD")
                return
            
            # Clear existing report
            for item in self.report_tree.get_children():
                self.report_tree.delete(item)
            
            # Generate report based on type
            if report_type == "daily":
                data = self.report_generator.get_attendance_by_date_range(start_date, end_date)
                self._display_daily_report(data)
                
            elif report_type == "class":
                class_id = self._get_selected_class_id()
                data = self.report_generator.get_attendance_by_date_range(start_date, end_date, class_id)
                self._display_class_report(data)
                
            elif report_type == "student":
                student_id = self._get_selected_student_id()
                data = self.report_generator.get_student_attendance_summary(start_date, end_date, student_id)
                self._display_student_report(data)
                
            elif report_type == "summary":
                data = self.report_generator.get_daily_attendance_summary(start_date, end_date)
                self._display_summary_report(data)
                
            elif report_type == "trends":
                data = self.report_generator.get_attendance_trends(30)
                self._display_trends_report(data)
            
            # Update summary
            self._update_report_summary(start_date, end_date)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo báo cáo: {e}")
            print(f"Report error: {e}")
    
    def _get_selected_class_id(self):
        """Get selected class ID from combo"""
        class_text = self.report_class_var.get()
        if class_text == "Tất cả lớp" or not class_text:
            return None
        
        classes = self.db.get_all_classes()
        for cls in classes:
            if f"{cls[1]} - {cls[2]}" == class_text:
                return cls[0]
        return None
    
    def _get_selected_student_id(self):
        """Get selected student ID from combo"""
        student_text = self.report_student_var.get()
        if student_text == "Tất cả học sinh" or not student_text:
            return None
            
        students = self.db.get_all_students()
        for student in students:
            if f"{student[2]} ({student[1]})" == student_text:
                return student[0]
        return None
    
    def _display_daily_report(self, data):
        """Display daily attendance report"""
        if data.empty:
            self._show_no_data_message()
            return
            
        # Configure columns
        columns = ['Ngày', 'Giờ', 'Học sinh', 'Mã HS', 'Lớp', 'Độ tin cậy', 'Phiên']
        self.report_tree['columns'] = columns
        self.report_tree['show'] = 'headings'
        
        # Set column headers and widths
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120, anchor='center')
        
        # Insert data
        for _, row in data.iterrows():
            self.report_tree.insert('', 'end', values=[
                str(row['date'])[:10] if pd.notna(row['date']) else '',
                str(row['time'])[:8] if pd.notna(row['time']) else '',
                row['student_name'],
                row['student_code'],
                row['class_name'],
                f"{row['confidence_score']:.1f}%" if pd.notna(row['confidence_score']) else '',
                row['session_name'] if pd.notna(row['session_name']) else ''
            ])
    
    def _display_class_report(self, data):
        """Display class attendance report"""
        self._display_daily_report(data)  # Same format as daily report
    
    def _display_student_report(self, data):
        """Display student attendance summary"""
        if data.empty:
            self._show_no_data_message()
            return
            
        columns = ['Học sinh', 'Mã HS', 'Lớp', 'Ngày có mặt', 'Tổng phiên', 'Tỷ lệ (%)']
        self.report_tree['columns'] = columns
        self.report_tree['show'] = 'headings'
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120, anchor='center')
        
        for _, row in data.iterrows():
            self.report_tree.insert('', 'end', values=[
                row['student_name'],
                row['student_code'],
                row['class_name'],
                int(row['days_present']) if pd.notna(row['days_present']) else 0,
                int(row['total_sessions']) if pd.notna(row['total_sessions']) else 0,
                f"{row['attendance_percentage']:.1f}%" if pd.notna(row['attendance_percentage']) else '0%'
            ])
    
    def _display_summary_report(self, data):
        """Display daily summary report"""
        if data.empty:
            self._show_no_data_message()
            return
            
        columns = ['Ngày', 'Lớp', 'Có mặt', 'Tổng HS', 'Tỷ lệ (%)']
        self.report_tree['columns'] = columns
        self.report_tree['show'] = 'headings'
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120, anchor='center')
        
        for _, row in data.iterrows():
            self.report_tree.insert('', 'end', values=[
                row['attendance_date'],
                row['class_name'],
                int(row['present_count']),
                int(row['total_students']),
                f"{row['attendance_rate']:.1f}%"
            ])
    
    def _display_trends_report(self, data):
        """Display trends report"""
        if data.empty:
            self._show_no_data_message()
            return
            
        columns = ['Ngày', 'Học sinh duy nhất', 'Tổng bản ghi', 'Độ tin cậy TB']
        self.report_tree['columns'] = columns
        self.report_tree['show'] = 'headings'
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=150, anchor='center')
        
        for _, row in data.iterrows():
            self.report_tree.insert('', 'end', values=[
                row['date'],
                int(row['unique_students']),
                int(row['total_records']),
                f"{row['avg_confidence']:.1f}%" if pd.notna(row['avg_confidence']) else ''
            ])
    
    def _show_no_data_message(self):
        """Show message when no data available"""
        self.report_tree['columns'] = ['Thông báo']
        self.report_tree['show'] = 'headings'
        self.report_tree.heading('Thông báo', text='Thông báo')
        self.report_tree.column('Thông báo', width=400, anchor='center')
        self.report_tree.insert('', 'end', values=['Không có dữ liệu trong khoảng thời gian đã chọn'])
    
    def _update_report_summary(self, start_date, end_date):
        """Update report summary display"""
        try:
            summary = self.report_generator.get_report_summary(start_date, end_date)
            
            # Clear existing summary
            for widget in self.report_summary_frame.winfo_children():
                widget.destroy()
            
            # Create summary display
            summary_text = f"""
📊 Tóm tắt báo cáo ({summary['date_range']})
• Tổng bản ghi: {summary['total_records']}
• Học sinh tham gia: {summary['unique_students']}
• Số lớp tham gia: {summary['classes_count']}
• Độ tin cậy trung bình: {summary['avg_confidence']}%
• Ngày hoạt động cao nhất: {summary['most_active_day']} ({summary['most_active_day_count']} bản ghi)
            """.strip()
            
            tk.Label(
                self.report_summary_frame,
                text=summary_text,
                font=('Arial', 10),
                bg='#ecf0f1',
                relief='sunken',
                anchor='w',
                justify='left',
                padx=10,
                pady=5
            ).pack(fill='x')
            
        except Exception as e:
            print(f"Error updating summary: {e}")
    
    def export_excel_report(self):
        """Export current report to Excel"""
        try:
            if not hasattr(self, 'report_generator'):
                messagebox.showerror("Lỗi", "Vui lòng tạo báo cáo trước khi xuất!")
                return
            
            start_date = self.from_date_var.get()
            end_date = self.to_date_var.get()
            
            # Choose output file
            filename = filedialog.asksaveasfilename(
                title="Lưu báo cáo Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialname=f"attendance_report_{start_date}_{end_date}.xlsx"
            )
            
            if not filename:
                return
            
            # Export report
            output_path = self.report_generator.export_comprehensive_report(
                start_date, end_date, filename
            )
            
            messagebox.showinfo(
                "Thành công", 
                f"Báo cáo đã được xuất thành công!\n\nFile: {output_path}"
            )
            
            # Ask to open file
            if messagebox.askyesno("Mở file", "Bạn có muốn mở file Excel vừa tạo không?"):
                os.startfile(output_path)
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {e}")
    
    def show_report_charts(self):
        """Show report charts in new window"""
        try:
            if not hasattr(self, 'report_generator'):
                messagebox.showerror("Lỗi", "Vui lòng tạo báo cáo trước khi xem biểu đồ!")
                return
            
            start_date = self.from_date_var.get()
            end_date = self.to_date_var.get()
            
            # Create charts window
            charts_window = tk.Toplevel(self.root)
            charts_window.title("📈 Biểu đồ Báo cáo Điểm danh")
            charts_window.geometry("1000x700")
            charts_window.configure(bg='white')
            
            # Create notebook for different charts
            charts_notebook = ttk.Notebook(charts_window)
            charts_notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Generate charts
            charts = self.report_generator.create_attendance_visualization(start_date, end_date)
            
            if charts:
                for chart_name, chart_data in charts.items():
                    # Create frame for this chart
                    chart_frame = ttk.Frame(charts_notebook)
                    
                    # Decode and display chart
                    import base64
                    from io import BytesIO
                    
                    image_data = base64.b64decode(chart_data)
                    image = Image.open(BytesIO(image_data))
                    photo = ImageTk.PhotoImage(image)
                    
                    label = tk.Label(chart_frame, image=photo)
                    label.image = photo  # Keep a reference
                    label.pack(padx=10, pady=10)
                    
                    # Add to notebook
                    chart_titles = {
                        'daily_trend': 'Xu hướng hàng ngày',
                        'hourly_pattern': 'Phân bố theo giờ',
                        'class_comparison': 'So sánh lớp học'
                    }
                    
                    charts_notebook.add(chart_frame, text=chart_titles.get(chart_name, chart_name))
            else:
                tk.Label(
                    charts_window,
                    text="Không có dữ liệu để tạo biểu đồ",
                    font=('Arial', 14),
                    fg='gray'
                ).pack(expand=True)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị biểu đồ: {e}")
            print(f"Charts error: {e}")

def main():
    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()