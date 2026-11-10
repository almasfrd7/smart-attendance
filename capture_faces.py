
import cv2
import os
import json
import time

# ==========================================
# CONFIGURATION
# ==========================================

DATASET_DIR = "dataset"
USERS_FILE = "users.json"
CASCADE_PATH = "haarcascade_frontalface_default.xml"

TOTAL_IMAGES = 50
CAPTURE_INTERVAL = 0.2

# Create dataset folder if it doesn't exist
os.makedirs(DATASET_DIR, exist_ok=True)


# ==========================================
# LOAD EXISTING USERS
# ==========================================

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as file:
        users = json.load(file)
else:
    users = {}


# ==========================================
# REGISTER USER
# ==========================================

user_id = input("Enter User ID (e.g. 1): ").strip()
name = input("Enter Your Name: ").strip()

if not user_id.isdigit() or not name:
    print("Invalid User ID or Name.")
    exit()

# Allow existing users to update their face images
users[user_id] = name

with open(USERS_FILE, "w") as file:
    json.dump(users, file, indent=4)

print(f"\nRegistered user: {name}")


# ==========================================
# LOAD FACE DETECTOR
# ==========================================

face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    print("\nERROR: Haar Cascade file could not be loaded.")
    print("Make sure the XML file is inside the project folder.")
    exit()

print("Face detector loaded successfully!")


# ==========================================
# OPEN WEBCAM
# ==========================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Cannot access webcam.")
    exit()

print("\nStarting face registration...")
print("Look at your webcam.")
print("Press Q to stop.\n")


# ==========================================
# CAPTURE FACE IMAGES
# ==========================================

image_count = 0
last_capture_time = 0

while image_count < TOTAL_IMAGES:

    success, frame = camera.read()

    if not success:
        print("Cannot read webcam.")
        break

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:

        # Draw green rectangle around face
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        # Crop detected face
        face = gray[y:y+h, x:x+w]

        # Resize face image
        face = cv2.resize(face, (200, 200))

        # Improve image contrast
        face = cv2.equalizeHist(face)

        current_time = time.time()

        # Capture image every 0.2 seconds
        if current_time - last_capture_time >= CAPTURE_INTERVAL:

            image_count += 1

            image_path = os.path.join(
                DATASET_DIR,
                f"user.{user_id}.{image_count}.jpg"
            )

            cv2.imwrite(image_path, face)

            last_capture_time = current_time

            print(f"Captured {image_count}/{TOTAL_IMAGES}")

        # Process only one face
        break

    # Display progress
    cv2.putText(
        frame,
        f"Images: {image_count}/{TOTAL_IMAGES}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("Face Registration", frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# CLEANUP
# ==========================================

camera.release()
cv2.destroyAllWindows()

print("\n================================")
print("FACE REGISTRATION COMPLETED")
print("================================")
print(f"User: {name}")
print(f"Images captured: {image_count}")
