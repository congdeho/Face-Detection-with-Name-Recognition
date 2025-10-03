"""
Database Models for Student Attendance System
Định nghĩa cấu trúc database cho hệ thống điểm danh học sinh
"""

import sqlite3
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Get project root directory
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            db_dir = os.path.join(project_root, 'data')
            self.db_path = os.path.join(db_dir, 'attendance.db')
        else:
            self.db_path = db_path
        self.ensure_directory()
        self.init_tables()
        self.init_sample_data()
    
    def ensure_directory(self):
        """Tạo thư mục data nếu chưa có"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Tạo kết nối database"""
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        """Khởi tạo các bảng database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bảng Classes (Lớp học)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL UNIQUE,
            class_code TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Bảng Students (Học sinh)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            class_id INTEGER,
            email TEXT,
            phone TEXT,
            address TEXT,
            photo_path TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
        ''')
        
        # Bảng Attendance Sessions (Phiên điểm danh)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
        ''')
        
        # Bảng Attendance Records (Bản ghi điểm danh)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            status TEXT DEFAULT 'present', -- present, absent, late
            confidence_score REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        ''')
        
        # Bảng Face Training Data (Dữ liệu training khuôn mặt)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            training_id INTEGER,
            is_trained BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at: {self.db_path}")
    
    def init_sample_data(self):
        """Khởi tạo dữ liệu mẫu nếu chưa có"""
        try:
            # Check if classes exist
            classes = self.get_all_classes()
            if not classes:
                print("📚 Creating sample classes...")
                # Add sample classes
                sample_classes = [
                    ('Lớp 12A1', '12A1', 'Lớp 12 chuyên Toán'),
                    ('Lớp 12A2', '12A2', 'Lớp 12 chuyên Lý'),
                    ('Lớp 12A3', '12A3', 'Lớp 12 chuyên Hóa'),
                    ('Lớp 12A4', '12A4', 'Lớp 12 chuyên Sinh'),
                    ('Lớp 12A5', '12A5', 'Lớp 12 chuyên Văn')
                ]
                
                for name, code, desc in sample_classes:
                    self.add_class(name, code, desc)
                
                print(f"✅ Created {len(sample_classes)} sample classes")
                
                # Add some sample students for the first class
                self.create_sample_students()
            else:
                print(f"📚 Found {len(classes)} existing classes")
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
    
    def create_sample_students(self):
        """Tạo học sinh mẫu cho lớp đầu tiên"""
        try:
            # Get first class ID
            classes = self.get_all_classes()
            if classes:
                first_class_id = classes[0][0]
                
                # Check if students exist for this class
                students = self.get_students_by_class(first_class_id)
                if not students:
                    print("👥 Creating sample students...")
                    sample_students = [
                        ('HS001', 'Nguyễn Văn An', 'an.nguyen@email.com', '0123456789'),
                        ('HS002', 'Trần Thị Bình', 'binh.tran@email.com', '0123456790'),
                        ('HS003', 'Lê Hoàng Cường', 'cuong.le@email.com', '0123456791'),
                        ('HS004', 'Phạm Thị Dung', 'dung.pham@email.com', '0123456792'),
                        ('HS005', 'Hồ Công Đệ', 'de.ho@email.com', '0123456793')
                    ]
                    
                    for student_id, name, email, phone in sample_students:
                        try:
                            self.add_student(student_id, name, first_class_id, email, phone)
                        except Exception as e:
                            print(f"⚠️ Could not add student {name}: {e}")
                    
                    print(f"✅ Created {len(sample_students)} sample students")
        except Exception as e:
            print(f"❌ Error creating sample students: {e}")
    
    # === CRUD Operations for Classes ===
    def add_class(self, class_name, class_code, description=""):
        """Thêm lớp học mới"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO classes (class_name, class_code, description)
                VALUES (?, ?, ?)
            ''', (class_name, class_code, description))
            conn.commit()
            class_id = cursor.lastrowid
            conn.close()
            return class_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Class name '{class_name}' or code '{class_code}' already exists")
    
    def get_all_classes(self):
        """Lấy danh sách tất cả các lớp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM classes ORDER BY class_name')
        classes = cursor.fetchall()
        conn.close()
        return classes
    
    # === CRUD Operations for Students ===
    def add_student(self, student_id, full_name, class_id, email="", phone="", address=""):
        """Thêm học sinh mới"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO students (student_id, full_name, class_id, email, phone, address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, full_name, class_id, email, phone, address))
            conn.commit()
            student_db_id = cursor.lastrowid
            conn.close()
            return student_db_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Student ID '{student_id}' already exists")
    
    def get_students_by_class(self, class_id):
        """Lấy danh sách học sinh theo lớp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.class_name 
            FROM students s 
            JOIN classes c ON s.class_id = c.id 
            WHERE s.class_id = ? AND s.is_active = 1
            ORDER BY s.full_name
        ''', (class_id,))
        students = cursor.fetchall()
        conn.close()
        return students
    
    def get_all_students(self):
        """Lấy danh sách tất cả học sinh"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.class_name 
            FROM students s 
            LEFT JOIN classes c ON s.class_id = c.id 
            WHERE s.is_active = 1
            ORDER BY s.full_name
        ''')
        students = cursor.fetchall()
        conn.close()
        return students
    
    def get_student_by_id(self, student_db_id):
        """Lấy thông tin học sinh theo ID database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.class_name 
            FROM students s 
            LEFT JOIN classes c ON s.class_id = c.id 
            WHERE s.id = ?
        ''', (student_db_id,))
        student = cursor.fetchone()
        conn.close()
        return student
    
    # === Attendance Session Operations ===
    def create_attendance_session(self, session_name, class_id, session_date, start_time, description=""):
        """Tạo phiên điểm danh mới"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance_sessions (session_name, class_id, session_date, start_time, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_name, class_id, session_date, start_time, description))
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id
    
    def get_active_sessions(self):
        """Lấy danh sách phiên điểm danh đang hoạt động"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.class_name 
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            WHERE s.is_active = 1
            ORDER BY s.session_date DESC, s.start_time DESC
        ''')
        sessions = cursor.fetchall()
        conn.close()
        return sessions
        
    def end_attendance_session(self, session_id):
        """Kết thúc phiên điểm danh"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE attendance_sessions 
            SET end_time = ?, is_active = 0 
            WHERE id = ?
        ''', (datetime.now().strftime('%H:%M:%S'), session_id))
        conn.commit()
        conn.close()
    
    # === Attendance Record Operations ===
    def record_attendance(self, session_id, student_id, confidence_score=0.0, status='present'):
        """Ghi nhận điểm danh cho học sinh"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra xem đã điểm danh chưa
        cursor.execute('''
            SELECT id FROM attendance_records 
            WHERE session_id = ? AND student_id = ?
        ''', (session_id, student_id))
        
        existing_record = cursor.fetchone()
        current_time = datetime.now()
        
        if existing_record:
            # Cập nhật check-out time nếu đã có check-in
            cursor.execute('''
                UPDATE attendance_records 
                SET check_out_time = ?, confidence_score = ?
                WHERE id = ?
            ''', (current_time, confidence_score, existing_record[0]))
        else:
            # Tạo bản ghi mới với check-in time
            cursor.execute('''
                INSERT INTO attendance_records 
                (session_id, student_id, check_in_time, confidence_score, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, student_id, current_time, confidence_score, status))
        
        conn.commit()
        conn.close()
    
    def get_attendance_by_session(self, session_id):
        """Lấy danh sách điểm danh theo phiên"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ar.*, s.full_name, s.student_id
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.id
            WHERE ar.session_id = ?
            ORDER BY ar.check_in_time
        ''', (session_id,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def get_student_attendance_history(self, student_id, days=30):
        """Lấy lịch sử điểm danh của học sinh"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ar.*, s.session_name, s.session_date, c.class_name
            FROM attendance_records ar
            JOIN attendance_sessions s ON ar.session_id = s.id
            JOIN classes c ON s.class_id = c.id
            WHERE ar.student_id = ? 
            AND s.session_date >= date('now', '-{} days')
            ORDER BY s.session_date DESC, ar.check_in_time DESC
        '''.format(days), (student_id,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def update_student(self, student_id, student_code=None, full_name=None, class_id=None, email=None, phone=None):
        """Cập nhật thông tin học sinh"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute('SELECT id FROM students WHERE id = ?', (student_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Học sinh với ID {student_id} không tồn tại")
        
        # Build dynamic update query
        updates = []
        params = []
        
        if student_code is not None:
            # Check if new student_id is unique
            cursor.execute('SELECT id FROM students WHERE student_id = ? AND id != ?', (student_code, student_id))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Mã học sinh '{student_code}' đã tồn tại")
            updates.append('student_id = ?')
            params.append(student_code)
            
        if full_name is not None:
            updates.append('full_name = ?')
            params.append(full_name)
            
        if class_id is not None:
            # Check if class exists
            cursor.execute('SELECT id FROM classes WHERE id = ?', (class_id,))
            if not cursor.fetchone():
                conn.close()
                raise ValueError(f"Lớp học với ID {class_id} không tồn tại")
            updates.append('class_id = ?')
            params.append(class_id)
            
        if email is not None:
            updates.append('email = ?')
            params.append(email)
            
        if phone is not None:
            updates.append('phone = ?')
            params.append(phone)
        
        if not updates:
            conn.close()
            return False  # No changes to make
        
        # Add updated_at timestamp
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(student_id)  # For WHERE clause
        
        query = f'UPDATE students SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    
    def delete_student(self, student_id):
        """Xóa học sinh và tất cả dữ liệu liên quan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if student exists
            cursor.execute('SELECT student_id, full_name FROM students WHERE id = ?', (student_id,))
            student = cursor.fetchone()
            if not student:
                conn.close()
                raise ValueError(f"Học sinh với ID {student_id} không tồn tại")
            
            student_code, full_name = student
            
            # Delete related records in correct order (foreign key constraints)
            # 1. Delete attendance records
            cursor.execute('DELETE FROM attendance_records WHERE student_id = ?', (student_id,))
            attendance_deleted = cursor.rowcount
            
            # 2. Delete face encodings
            cursor.execute('DELETE FROM face_encodings WHERE student_id = ?', (student_id,))
            encodings_deleted = cursor.rowcount
            
            # 3. Delete student record
            cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
            
            conn.commit()
            
            # Also try to delete face images from dataset folder
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dataset_dir = os.path.join(project_root, 'data', 'dataset')
            
            deleted_images = 0
            if os.path.exists(dataset_dir):
                # Delete images with pattern User.{student_id}.*.jpg
                for filename in os.listdir(dataset_dir):
                    if filename.startswith(f'User.{student_id}.') and filename.endswith('.jpg'):
                        try:
                            os.remove(os.path.join(dataset_dir, filename))
                            deleted_images += 1
                        except Exception as e:
                            print(f"⚠️ Could not delete image {filename}: {e}")
            
            conn.close()
            
            print(f"✅ Deleted student: {full_name} (ID: {student_id})")
            print(f"   - Attendance records: {attendance_deleted}")
            print(f"   - Face encodings: {encodings_deleted}")
            print(f"   - Face images: {deleted_images}")
            
            return {
                'student_id': student_code,
                'full_name': full_name,
                'attendance_records': attendance_deleted,
                'face_encodings': encodings_deleted,
                'face_images': deleted_images
            }
            
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    def get_student_by_id(self, student_id):
        """Lấy thông tin chi tiết học sinh theo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, c.class_name, c.class_code
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.id = ?
        ''', (student_id,))
        student = cursor.fetchone()
        conn.close()
        return student

# Test database initialization
if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
    
    # Thêm dữ liệu mẫu
    try:
        class_id = db.add_class("Lớp 12A1", "12A1", "Lớp chuyên Toán")
        student_id = db.add_student("HS001", "Nguyễn Văn An", class_id, "an@school.edu.vn", "0123456789")
        print(f"Added sample data: Class ID {class_id}, Student ID {student_id}")
    except ValueError as e:
        print(f"Sample data might already exist: {e}")