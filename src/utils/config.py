"""
Configuration file for Attendance System
File cấu hình cho hệ thống điểm danh
"""

# Database configuration
DATABASE_PATH = "attendance_system/data/attendance.db"

# Face recognition settings
CONFIDENCE_THRESHOLD = 60  # Minimum confidence score for face recognition
RECOGNITION_COOLDOWN = 30  # Seconds between recognitions for same student
CASCADE_PATH = "haarcascade_frontalface_default.xml"

# Camera settings
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# GUI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
THEME_COLOR = "#2c3e50"

# Report settings
REPORTS_DIRECTORY = "attendance_system/reports"
MAX_REPORT_DAYS = 365

# Logging settings
LOG_DIRECTORY = "attendance_system/logs"
LOG_LEVEL = "INFO"

# File paths
TRAINING_DATA_PATH = "data/trainer/"
FACE_MODEL_PATH = "data/face_model.pkl"
STUDENT_PHOTOS_PATH = "attendance_system/data/students/"