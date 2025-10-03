''''
Real Time Face Recognition - Simple Version
	==> Uses numpy data instead of opencv-contrib
	==> Works with data created by 02_face_training_fixed.py

Based on original code by Anirban Kar: https://github.com/thecodacus/Face-Recognition    
Modified to work without opencv-contrib
'''

import cv2
import numpy as np
import os

# Load training data
try:
    faces_data = np.load('data/trainer/faces_data.npy', allow_pickle=True)
    ids_data = np.load('data/trainer/ids_data.npy')
    print(f"[INFO] Loaded {len(faces_data)} face samples")
    print(f"[INFO] Unique IDs: {np.unique(ids_data)}")
except:
    print("[ERROR] Could not load training data!")
    print("Make sure you have run 02_face_training_fixed.py first")
    exit()

cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

font = cv2.FONT_HERSHEY_SIMPLEX

# Names related to ids: example ==> ID 1: 'Duong', ID 2: 'Lan', etc
names = ['None', 'De', 'Lan']  # Index 0 không dùng, ID 1 = 'Duong', ID 2 = 'Lan'

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video width
cam.set(4, 480) # set video height

# Check if camera is opened successfully
if not cam.isOpened():
    print("Error: Could not open camera")
    print("Please check if:")
    print("1. Camera is connected")
    print("2. Camera is not being used by another application")
    print("3. Camera permissions are granted")
    exit()

# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)

print("[INFO] Camera ready. Press ESC to exit...")

def simple_face_recognition(face_img):
    """Simple face recognition using template matching"""
    best_match_id = 0
    best_confidence = float('inf')
    
    # Resize input face to match training data size (if needed)
    for i, stored_face in enumerate(faces_data):
        try:
            # Resize both images to same size for comparison
            target_size = min(face_img.shape[0], face_img.shape[1], stored_face.shape[0], stored_face.shape[1])
            
            if target_size > 20:  # Minimum size check
                face_resized = cv2.resize(face_img, (target_size, target_size))
                stored_resized = cv2.resize(stored_face, (target_size, target_size))
                
                # Calculate similarity (lower is better)
                diff = np.mean(np.abs(face_resized.astype(float) - stored_resized.astype(float)))
                
                if diff < best_confidence:
                    best_confidence = diff
                    best_match_id = ids_data[i]
        except:
            continue
    
    # Convert to percentage confidence (higher is better)
    confidence = max(0, 100 - (best_confidence / 255 * 100))
    
    return best_match_id, confidence

while True:
    ret, img = cam.read()
    
    # Check if frame is read correctly
    if not ret or img is None:
        print("Error: Failed to capture image from camera")
        break
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
    )

    for(x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Extract face for recognition
        face_img = gray[y:y+h, x:x+w]
        
        # Recognize face
        id, confidence = simple_face_recognition(face_img)
        
        # Check if confidence is acceptable
        if confidence > 50:  # Threshold for recognition
            if id < len(names):
                name = names[id]
                confidence_text = f"  {confidence:.1f}%"
            else:
                name = f"ID: {id}"
                confidence_text = f"  {confidence:.1f}%"
        else:
            name = "Unknown"
            confidence_text = f"  {confidence:.1f}%"
        
        cv2.putText(img, str(name), (x+5, y-5), font, 1, (255, 255, 255), 2)
        cv2.putText(img, str(confidence_text), (x+5, y+h-5), font, 1, (255, 255, 0), 1)  
    
    cv2.imshow('Face Recognition', img) 
    
    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break

print("\n[INFO] Cleaning up...")
cam.release()
cv2.destroyAllWindows()