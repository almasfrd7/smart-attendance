# Smart Attendance System

A local face-recognition attendance system built with Python and OpenCV. It captures a user's face from a webcam, trains a model, and then recognizes the person to mark attendance automatically.

This project is designed for classroom or office attendance tracking where users are registered once and then identified by their face when they appear in front of the webcam.

## Features

- User registration with webcam face capture
- Face dataset collection for each user
- Model training using OpenCV LBPH face recognizer
- Real-time face recognition from the webcam
- Automatic attendance logging to CSV
- Web-based attendance record viewer and editor
- Easy reset of user data, dataset, and attendance records

## Tech Stack

- Python 3.10
- OpenCV
- NumPy
- XAMPP / Apache for the web UI
- CSV-based attendance storage

## How it Works

1. Register a user by running `capture_faces.py`
2. Capture multiple face images from the webcam
3. Train the recognition model using `train_model.py`
4. Start `attendance.py` to detect and recognize faces in real time
5. Attendance is saved to `attendance/attendance.csv`
6. View and manage attendance records in `attendance.html`

## Project Structure

```text
smart-attendance/
├── attendance.py
├── attendance.html
├── attendance_api.php
├── capture_faces.py
├── train_model.py
├── users.json
├── requirements.txt
├── haarcascade_frontalface_default.xml
├── dataset/
├── trainer/
├── attendance/
└── .venv/
