
import cv2
import os
import json
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================

DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"
USERS_FILE = "users.json"

MODEL_PATH = os.path.join(TRAINER_DIR, "trainer.yml")
LABELS_PATH = os.path.join(TRAINER_DIR, "labels.json")

os.makedirs(TRAINER_DIR, exist_ok=True)


# ==========================================
# CHECK USER INFORMATION
# ==========================================

if not os.path.exists(USERS_FILE):
    print("ERROR: users.json not found.")
    exit()

with open(USERS_FILE, "r") as file:
    users = json.load(file)

if not users:
    print("No registered users found.")
    exit()


# ==========================================
# LOAD TRAINING IMAGES
# ==========================================

faces = []
labels = []

print("\nLoading face images...\n")

for filename in os.listdir(DATASET_DIR):

    # Expected format: user.ID.COUNT.jpg
    parts = filename.split(".")

    if len(parts) != 4 or parts[0] != "user":
        continue

    user_id = parts[1]

    # Ignore images belonging to unregistered users
    if user_id not in users:
        continue

    image_path = os.path.join(DATASET_DIR, filename)

    # Read image as grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        continue

    # Resize to standard dimensions
    image = cv2.resize(image, (200, 200))

    # Apply contrast enhancement
    image = cv2.equalizeHist(image)

    faces.append(image)
    labels.append(int(user_id))

    print(f"Loaded: {filename}")


# ==========================================
# CHECK TRAINING DATA
# ==========================================

if len(faces) == 0:
    print("\nNo training images found.")
    print("Run capture_faces.py first.")
    exit()

print(f"\nTotal images loaded: {len(faces)}")


# ==========================================
# TRAIN LBPH MODEL
# ==========================================

if not hasattr(cv2, "face"):
    print("ERROR: OpenCV face module is unavailable.")
    exit()

recognizer = cv2.face.LBPHFaceRecognizer_create()

labels = np.array(labels, dtype=np.int32)

print("\nTraining model...")

recognizer.train(faces, labels)


# ==========================================
# SAVE MODEL
# ==========================================

recognizer.write(MODEL_PATH)

# Save registered user information
with open(LABELS_PATH, "w") as file:
    json.dump(users, file, indent=4)


# ==========================================
# COMPLETED
# ==========================================

print("\n================================")
print("MODEL TRAINING COMPLETED!")
print("================================")

print(f"Training images: {len(faces)}")
print(f"Registered users: {len(users)}")
print(f"Model location: {MODEL_PATH}")
