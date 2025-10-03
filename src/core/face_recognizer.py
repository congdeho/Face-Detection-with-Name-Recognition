"""
Enhanced Face Recognition Module for Attendance System
Module nhận diện khuôn mặt nâng cao cho hệ thống điểm danh
"""

import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time

class AttendanceFaceRecognizer:
    def __init__(self, database_manager, confidence_threshold=60):
        self.db = database_manager
        self.confidence_threshold = confidence_threshold
        
        # Face detection
        self.cascade_path = "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        
        # Recognition data
        self.faces_data = None
        self.ids_data = None
        self.student_names = {}
        
        # Camera
        self.camera = None
        self.is_running = False
        
        # Attendance tracking
        self.current_session_id = None
        self.last_recognition_time = {}
        self.recognition_cooldown = 30  # seconds
        
        # Load training data
        self.load_training_data()
        
    def load_training_data(self):
        """Load trained face recognition data"""
        try:
            # Try to load from new format first
            if os.path.exists('attendance_system/data/face_model.pkl'):
                with open('attendance_system/data/face_model.pkl', 'rb') as f:
                    model_data = pickle.load(f)
                    self.faces_data = model_data['faces']
                    self.ids_data = model_data['ids']
                    self.student_names = model_data['names']
                print(f"[INFO] Loaded enhanced model with {len(self.faces_data)} samples")
            else:
                # Fall back to original format - use correct data/trainer/ path
                self.faces_data = np.load('data/trainer/faces_data.npy', allow_pickle=True)
                self.ids_data = np.load('data/trainer/ids_data.npy')
                
                # Build name mapping from database
                students = self.db.get_all_students()
                self.student_names = {student[0]: student[2] for student in students}  # id: name
                
                print(f"[INFO] Loaded original model with {len(self.faces_data)} samples")
                print(f"[INFO] Available student IDs: {np.unique(self.ids_data)}")
                
        except Exception as e:
            print(f"[ERROR] Could not load training data: {e}")
            print("Please run face training first!")
            self.faces_data = np.array([])
            self.ids_data = np.array([])
            self.student_names = {}
    
    def enhanced_face_recognition(self, face_img):
        """Enhanced face recognition with better accuracy"""
        if len(self.faces_data) == 0:
            return 0, 0.0
            
        best_match_id = 0
        best_confidence = float('inf')
        
        # Multiple recognition methods for better accuracy
        confidences = []
        
        try:
            # Method 1: Template matching with different sizes
            for i, stored_face in enumerate(self.faces_data):
                try:
                    # Resize to multiple scales for better matching
                    scales = [0.8, 1.0, 1.2]
                    scale_scores = []
                    
                    for scale in scales:
                        # Resize face image
                        h, w = face_img.shape
                        new_h, new_w = int(h * scale), int(w * scale)
                        if new_h > 20 and new_w > 20:
                            scaled_face = cv2.resize(face_img, (new_w, new_h))
                            
                            # Match with stored face
                            target_size = min(scaled_face.shape[0], scaled_face.shape[1], 
                                            stored_face.shape[0], stored_face.shape[1])
                            
                            if target_size > 20:
                                face_resized = cv2.resize(scaled_face, (target_size, target_size))
                                stored_resized = cv2.resize(stored_face, (target_size, target_size))
                                
                                # Calculate similarity
                                diff = np.mean(np.abs(face_resized.astype(float) - stored_resized.astype(float)))
                                scale_scores.append(diff)
                    
                    # Use best scale score
                    if scale_scores:
                        avg_diff = np.mean(scale_scores)
                        if avg_diff < best_confidence:
                            best_confidence = avg_diff
                            best_match_id = self.ids_data[i]
                            
                except Exception:
                    continue
            
            # Convert to percentage confidence (higher is better)
            confidence = max(0, 100 - (best_confidence / 255 * 100)) if best_confidence != float('inf') else 0
            
            return best_match_id, confidence
            
        except Exception as e:
            print(f"[ERROR] Recognition failed: {e}")
            return 0, 0.0
    
    def start_camera(self, camera_id=0):
        """Start camera for face recognition"""
        try:
            self.camera = cv2.VideoCapture(camera_id)
            if not self.camera.isOpened():
                raise Exception("Cannot open camera")
                
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            print("[INFO] Camera started successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop camera"""
        self.is_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        print("[INFO] Camera stopped")
    
    def recognize_faces_in_frame(self, frame):
        """Recognize faces in a single frame"""
        if self.camera is None or len(self.faces_data) == 0:
            return frame, []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        recognized_students = []
        
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Extract face for recognition
            face_img = gray[y:y+h, x:x+w]
            
            # Recognize face
            student_id, confidence = self.enhanced_face_recognition(face_img)
            
            # Determine name and status
            if confidence > self.confidence_threshold and student_id in self.student_names:
                name = self.student_names[student_id]
                status_color = (0, 255, 0)  # Green
                
                # Add to recognized list
                recognized_students.append({
                    'student_id': student_id,
                    'name': name,
                    'confidence': confidence,
                    'position': (x, y, w, h)
                })
                
            else:
                name = "Unknown"
                status_color = (0, 0, 255)  # Red
            
            # Display name and confidence
            label = f"{name} ({confidence:.1f}%)"
            cv2.putText(frame, label, (x+5, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            cv2.putText(frame, f"ID: {student_id}", (x+5, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        return frame, recognized_students
    
    def record_attendance_for_student(self, student_id, confidence):
        """Record attendance for a recognized student"""
        if not self.current_session_id:
            return False
        
        current_time = time.time()
        
        # Check cooldown period
        if student_id in self.last_recognition_time:
            if current_time - self.last_recognition_time[student_id] < self.recognition_cooldown:
                return False  # Still in cooldown
        
        try:
            # Record attendance
            self.db.record_attendance(
                self.current_session_id,
                student_id,
                confidence,
                'present'
            )
            
            # Update last recognition time
            self.last_recognition_time[student_id] = current_time
            
            print(f"[INFO] Recorded attendance for {self.student_names.get(student_id, f'ID:{student_id}')} (confidence: {confidence:.1f}%)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to record attendance: {e}")
            return False
    
    def start_attendance_recognition(self, session_id, callback=None):
        """Start automatic attendance recognition"""
        self.current_session_id = session_id
        self.is_running = True
        self.last_recognition_time = {}
        
        print(f"[INFO] Started attendance recognition for session {session_id}")
        
        def recognition_loop():
            while self.is_running and self.camera is not None:
                try:
                    ret, frame = self.camera.read()
                    if not ret:
                        continue
                    
                    # Recognize faces
                    processed_frame, recognized_students = self.recognize_faces_in_frame(frame)
                    
                    # Record attendance for recognized students
                    for student in recognized_students:
                        success = self.record_attendance_for_student(
                            student['student_id'], 
                            student['confidence']
                        )
                        
                        if success and callback:
                            callback(student)
                    
                    # Display frame (if GUI is integrated)
                    if callback:
                        callback({'frame': processed_frame, 'students': recognized_students})
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"[ERROR] Recognition loop error: {e}")
                    time.sleep(1)
        
        # Start recognition in separate thread
        self.recognition_thread = threading.Thread(target=recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
    
    def stop_attendance_recognition(self):
        """Stop automatic attendance recognition"""
        self.is_running = False
        self.current_session_id = None
        print("[INFO] Stopped attendance recognition")
    
    def get_session_stats(self):
        """Get current session statistics"""
        if not self.current_session_id:
            return None
        
        try:
            records = self.db.get_attendance_by_session(self.current_session_id)
            total_present = len(records)
            
            # Get total students in class (if needed)
            session_info = self.db.get_active_sessions()
            current_session = None
            for session in session_info:
                if session[0] == self.current_session_id:
                    current_session = session
                    break
            
            if current_session:
                class_id = current_session[2]
                all_students = self.db.get_students_by_class(class_id)
                total_students = len(all_students)
            else:
                total_students = total_present
            
            return {
                'total_students': total_students,
                'present': total_present,
                'absent': max(0, total_students - total_present),
                'attendance_rate': (total_present / total_students * 100) if total_students > 0 else 0
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to get session stats: {e}")
            return None

# Test function
def test_recognition():
    """Test face recognition system"""
    from database.models import DatabaseManager
    
    db = DatabaseManager()
    recognizer = AttendanceFaceRecognizer(db)
    
    if recognizer.start_camera():
        print("Press 'q' to quit")
        
        while True:
            ret, frame = recognizer.camera.read()
            if not ret:
                break
            
            processed_frame, students = recognizer.recognize_faces_in_frame(frame)
            
            cv2.imshow('Face Recognition Test', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        recognizer.stop_camera()
        cv2.destroyAllWindows()
    else:
        print("Failed to start camera")

if __name__ == "__main__":
    test_recognition()