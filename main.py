#!/usr/bin/env python3
"""
🎓 Student Attendance System - Face Recognition
Main entry point for the application

Run this file to start the attendance system:
    python main.py
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def setup_logging():
    """Setup logging configuration"""
    log_directory = os.path.join(src_dir, 'logs')
    os.makedirs(log_directory, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_directory, 'attendance_system.log')),
            logging.StreamHandler()
        ]
    )

def check_requirements():
    """Check if all required files and dependencies are available"""
    required_files = [
        ('assets/haarcascade_frontalface_default.xml', 'Haar cascade classifier')
    ]
    
    for file_path, description in required_files:
        full_path = os.path.join(current_dir, file_path)
        print(f"🔍 Checking: {full_path}")
        if not os.path.exists(full_path):
            print(f"❌ Missing required file: {description}")
            print(f"   Expected location: {full_path}")
            return False
    
    return True

def main():
    """Main entry point"""
    try:
        print("🎓 Starting Student Attendance System...")
        print("=" * 60)
        print("🎓 HỆ THỐNG ĐIỂM DANH HỌC SINH - FACE RECOGNITION")
        print("   Student Attendance System with Face Recognition") 
        print("=" * 60)
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Student Attendance System")
        
        # Check requirements
        if not check_requirements():
            logger.error("Required files not found")
            return 1
        
        # Import application modules
        logger.info("Initializing database...")
        from database.models import DatabaseManager
        
        # Initialize database
        db = DatabaseManager()
        logger.info("Database initialized successfully. Found {} classes.".format(len(db.get_all_classes())))
        print("✅ System initialized successfully!")
        
        # Start GUI application
        print("🚀 Starting GUI application...")
        from gui.main_app import AttendanceSystemGUI
        
        root = tk.Tk()
        app = AttendanceSystemGUI(root)
        
        # Graceful shutdown handling
        def on_closing():
            logger.info("Application closing gracefully")
            if hasattr(app, 'camera') and app.camera is not None:
                app.camera.release()
            root.quit()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
        print("👋 Thank you for using Student Attendance System!")
        return 0
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r config/requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        if 'logger' in locals():
            logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
