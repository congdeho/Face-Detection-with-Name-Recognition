"""
Sample Data Generator for Attendance Reports Demo
Tạo dữ liệu mẫu để demo báo cáo điểm danh
"""

import sqlite3
import random
from datetime import datetime, timedelta, time

def create_sample_attendance_data():
    """Create sample attendance data for demo"""
    
    # Connect to database
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    # Get existing students
    cursor.execute("SELECT id FROM students")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    if not student_ids:
        print("❌ No students found in database")
        conn.close()
        return
    
    # Get existing classes  
    cursor.execute("SELECT id FROM classes")
    class_ids = [row[0] for row in cursor.fetchall()]
    
    # Create some attendance sessions first
    session_data = []
    for i in range(10):  # Create 10 sessions over last 30 days
        session_date = datetime.now() - timedelta(days=random.randint(0, 30))
        start_time = time(hour=random.randint(8, 15), minute=random.choice([0, 30]))
        end_time = time(hour=start_time.hour + 2, minute=start_time.minute)
        
        session_data.append((
            f"Phiên điểm danh {session_date.strftime('%d/%m')}",  # session_name
            random.choice(class_ids),  # class_id
            session_date.date(),  # session_date
            start_time,  # start_time
            end_time,  # end_time
            f"Điểm danh buổi {['sáng', 'chiều'][random.randint(0, 1)]}",  # description
            True,  # is_active
            datetime.now()  # created_at
        ))
    
    # Insert sessions
    cursor.executemany("""
        INSERT INTO attendance_sessions 
        (session_name, class_id, session_date, start_time, end_time, description, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, session_data)
    
    # Get session IDs
    cursor.execute("SELECT id FROM attendance_sessions")
    session_ids = [row[0] for row in cursor.fetchall()]
    
    # Create attendance records
    attendance_records = []
    
    for _ in range(50):  # Create 50 attendance records
        check_in_time = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(8, 16),
            minutes=random.randint(0, 59)
        )
        
        attendance_records.append((
            random.choice(session_ids),  # session_id
            random.choice(student_ids),  # student_id
            check_in_time,  # check_in_time
            None,  # check_out_time (can be null)
            'present',  # status
            round(random.uniform(60.0, 95.0), 1),  # confidence_score
            random.choice(['Điểm danh bình thường', 'Điểm danh trễ', '']),  # notes
            datetime.now()  # created_at
        ))
    
    # Insert attendance records
    cursor.executemany("""
        INSERT INTO attendance_records 
        (session_id, student_id, check_in_time, check_out_time, status, confidence_score, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, attendance_records)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"✅ Created {len(session_data)} attendance sessions")
    print(f"✅ Created {len(attendance_records)} attendance records")
    print("🎉 Sample data generation completed!")

def check_existing_data():
    """Check what data already exists"""
    conn = sqlite3.connect('data/attendance.db')
    cursor = conn.cursor()
    
    # Check students
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    
    # Check classes
    cursor.execute("SELECT COUNT(*) FROM classes") 
    class_count = cursor.fetchone()[0]
    
    # Check attendance records
    cursor.execute("SELECT COUNT(*) FROM attendance_records")
    attendance_count = cursor.fetchone()[0]
    
    # Check sessions
    cursor.execute("SELECT COUNT(*) FROM attendance_sessions")
    session_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("=== CURRENT DATABASE STATUS ===")
    print(f"👥 Students: {student_count}")
    print(f"📚 Classes: {class_count}")
    print(f"📝 Attendance Records: {attendance_count}")
    print(f"⏰ Sessions: {session_count}")
    
    return attendance_count > 0

if __name__ == "__main__":
    print("🎯 Attendance Report Demo - Sample Data Generator")
    print("=" * 50)
    
    # Check existing data
    has_data = check_existing_data()
    
    if has_data:
        response = input("\n⚠️  Database already has attendance data. Add more? (y/n): ")
        if response.lower() != 'y':
            print("❌ Skipping data generation")
            exit()
    
    print("\n🚀 Generating sample attendance data...")
    create_sample_attendance_data()
    
    print("\n✅ Sample data ready! You can now:")
    print("1. Run the main application: python main.py")
    print("2. Go to the '📊 Báo cáo' tab")
    print("3. Try different report types and date ranges")
    print("4. Export Excel reports")
    print("5. View charts and statistics")