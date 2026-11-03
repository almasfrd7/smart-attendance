
import cv2
import os
import json
import csv
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================

MODEL_PATH = "trainer/trainer.yml"
LABELS_PATH = "trainer/labels.json"

CASCADE_PATH = "haarcascade_frontalface_default.xml"

ATTENDANCE_DIR = "attendance"

ATTENDANCE_FILE = os.path.join(
    ATTENDANCE_DIR,
    "attendance.csv"
)

# Initial LBPH confidence threshold
CONFIDENCE_THRESHOLD = 70

os.makedirs(ATTENDANCE_DIR, exist_ok=True)


# ==========================================
# CHECK REQUIRED FILES
# ==========================================

required_files = [
    MODEL_PATH,
    LABELS_PATH,
    CASCADE_PATH
]

for file_path in required_files:

    if not os.path.exists(file_path):
        print(f"ERROR: Missing file: {file_path}")
        exit()


# ==========================================
# LOAD FACE RECOGNITION MODEL
# ==========================================

recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.read(MODEL_PATH)

# Load registered user names
with open(LABELS_PATH, "r") as file:
    users = json.load(file)


# ==========================================
# LOAD FACE DETECTOR
# ==========================================

face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    print("ERROR: Cannot load face detection model.")
    exit()


# ==========================================
# LOAD TODAY'S ATTENDANCE
# ==========================================

def load_marked_attendance():

    marked = set()

    if not os.path.exists(ATTENDANCE_FILE):
        return marked

    with open(
        ATTENDANCE_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["Date"] == datetime.now().strftime("%Y-%m-%d"):
                marked.add(row["User ID"])

    return marked


# ==========================================
# RECORD ATTENDANCE
# ==========================================

def mark_attendance(user_id, name):

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    # Check for duplicate attendance
    if str(user_id) in marked_today:
        return "Already Marked"

    file_exists = os.path.exists(ATTENDANCE_FILE)

    with open(
        ATTENDANCE_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # Add column headings for new CSV
        if not file_exists:
            writer.writerow([
                "User ID",
                "Name",
                "Date",
                "Time",
                "Status"
            ])

        writer.writerow([
            user_id,
            name,
            current_date,
            current_time,
            "Present"
        ])

    # Update today's attendance list
    marked_today.add(str(user_id))

    print(f"Attendance recorded: {name} - {current_time}")

    return "Attendance Marked"


# ==========================================
# INITIALISE ATTENDANCE
# ==========================================

marked_today = load_marked_attendance()


# ==========================================
# OPEN WEBCAM
# ==========================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Cannot access webcam.")
    exit()

print("\n================================")
print("SMART ATTENDANCE SYSTEM")
print("================================")
print("Webcam started.")
print("Press Q to quit.\n")


# ==========================================
# MAIN FACE RECOGNITION LOOP
# ==========================================

while True:

    success, frame = camera.read()

    if not success:
        print("Cannot read webcam.")
        break

    # Convert webcam image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:

        # Crop face
        face = gray[y:y+h, x:x+w]

        # Resize face
        face = cv2.resize(face, (200, 200))

        # Apply contrast enhancement
        face = cv2.equalizeHist(face)

        # Recognise face
        user_id, confidence = recognizer.predict(face)

        # Check identity and confidence
        if (
            confidence < CONFIDENCE_THRESHOLD
            and str(user_id) in users
        ):

            name = users[str(user_id)]

            # Record attendance
            status = mark_attendance(user_id, name)

            color = (0, 255, 0)

            label = f"{name} - {status}"

        else:

            color = (0, 0, 255)

            label = "Unknown Person"

        # Draw bounding box
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            2
        )

        # Display recognition result
        text_y = y - 10 if y > 30 else y + h + 25

        cv2.putText(
            frame,
            label,
            (x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        # Display confidence
        cv2.putText(
            frame,
            f"Confidence: {confidence:.1f}",
            (x, y + h + 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )

    # Display application title
    cv2.putText(
        frame,
        "SMART ATTENDANCE SYSTEM",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    # Display attendance count
    cv2.putText(
        frame,
        f"Present Today: {len(marked_today)}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # Show webcam
    cv2.imshow("Smart Attendance System", frame)

    # Press Q to close
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# CLEANUP
# ==========================================

camera.release()
cv2.destroyAllWindows()

print("\nSmart Attendance System Closed.")
print(f"Total attendance today: {len(marked_today)}")
