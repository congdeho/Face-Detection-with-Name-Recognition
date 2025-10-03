''''
Simple Face Training using numpy only - no external ML libraries needed
	==> Each face should have a unique numeric integer ID as 1, 2, 3, etc                       
	==> Model will be saved as numpy arrays in trainer/ directory

Based on original code by Anirban Kar: https://github.com/thecodacus/Face-Recognition    
Modified to use simple numpy-based face matching
'''

import cv2
import numpy as np
from PIL import Image
import os

# Path for face image database
path = 'dataset'

detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

def getImagesAndLabels(path):
    imagePaths = [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.jpg')]     
    faceSamples = []
    ids = []
    
    print(f"Processing {len(imagePaths)} images...")
    
    for imagePath in imagePaths:
        try:
            PIL_img = Image.open(imagePath).convert('L') # convert it to grayscale
            img_numpy = np.array(PIL_img,'uint8')
            
            # Get ID from filename (format: User.ID.count.jpg)
            filename = os.path.basename(imagePath)
            id = int(filename.split(".")[1])
            
            # Use the whole face image (already cropped from dataset creation)
            faceSamples.append(img_numpy)
            ids.append(id)
            
            print(f"Processed: {filename} -> ID: {id}")
            
        except Exception as e:
            print(f"Error processing {imagePath}: {e}")
            continue

    return faceSamples, ids

print("\n [INFO] Training faces. It will take a few seconds. Wait ...")

# Create trainer directory if it doesn't exist
if not os.path.exists('data/trainer'):
    os.makedirs('data/trainer')

# Check if dataset folder exists
if not os.path.exists(path):
    print(f"[ERROR] Dataset folder '{path}' not found!")
    print("Make sure you have run 01_face_dataset.py first")
    exit()

faces, ids = getImagesAndLabels(path)

if len(faces) > 0:
    # Convert to numpy arrays
    faces_array = np.array(faces, dtype=object)  # Use object dtype for variable-sized arrays
    ids_array = np.array(ids)
    
    # Save the training data as numpy files
    np.save('data/trainer/faces_data.npy', faces_array)
    np.save('data/trainer/ids_data.npy', ids_array)
    
    # Create a simple mapping file
    unique_ids = np.unique(ids_array)
    print(f"\n [INFO] {len(unique_ids)} unique faces trained: {unique_ids}")
    print(f"[INFO] Total samples: {len(faces)}")
    print(f"[INFO] Training data saved to data/trainer/ folder")
    print("[INFO] Files created:")
    print("  - data/trainer/faces_data.npy")
    print("  - data/trainer/ids_data.npy")
    
else:
    print("[ERROR] No faces found in dataset folder!")
    print("Make sure you have:")
    print("1. Run 01_face_dataset.py first")
    print("2. Images saved in dataset/ folder")
    print("3. Images named in format: User.ID.count.jpg")