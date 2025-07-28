import cv2
import face_recognition
import face_recognition_models
import os
import pymysql
from datetime import datetime, timedelta
import sys
import numpy as np
from ultralytics import YOLO

face_recognition_models.MODELS_BASE_PATH = "/home/mitzaaa/InfoEdu/faceenv/lib/python3.12/site-packages/face_recognition_models/models"
os.environ["QT_QPA_PLATFORM"] = "xcb"
enable_display = not ("--headless" in sys.argv)

PHOTO_FOLDER = "student_photos"
encodari_cunoscute = []
studenti_cunoscute = []

conn = pymysql.connect(host="localhost", user="root", password="yournewpassword", database="school")
cursor = conn.cursor()
cursor.execute("SELECT id, first_name, last_name, photo FROM students WHERE photo IS NOT NULL")
students = cursor.fetchall()

for student_id, first_name, last_name, photo_filename in students:
    full_name = f"{first_name} {last_name}"
    photo_path = os.path.join(PHOTO_FOLDER, photo_filename)
    if photo_filename and os.path.exists(photo_path):
        try:
            imagine = face_recognition.load_image_file(photo_path)
            encodari = face_recognition.face_encodings(imagine)
            if encodari:
                encodari_cunoscute.append(encodari[0])
                studenti_cunoscute.append((student_id, full_name))
            else:
                print(f"-- Fața nu a fost detectată în {photo_path} pentru {full_name}")
        except Exception as e:
            print(f"-- Eroare la încărcarea {photo_path}: {e}")
    else:
        print(f"-- Poză lipsă: {photo_path} pentru {full_name}")

timp_prezenti = {}
durata_prezenta = timedelta(minutes=50)
log_lines, max_log_lines = [], 15
log_visible = True
log_width, log_height = 450, 150
font_scale = 0.5
line_height = 18
exit_requested = False
unknown_face_recent = False

last_unknown_face_time = datetime.min
reset_check_interval = timedelta(minutes=1)
last_reset_check = datetime.now()


# Camera switching

def list_available_cameras(max_index=5):
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available


camera_indices = list_available_cameras(5)
if not camera_indices:
    raise Exception("No available cameras detected!")
current_cam_idx = 0


def open_camera(idx):
    cam = cv2.VideoCapture(idx)
    if cam.isOpened():
        print(f"Switched to camera {idx}")
        return cam
    else:
        print(f"Camera at index {idx} not available.")
        return None


camera = open_camera(camera_indices[current_cam_idx])
if camera is None:
    raise Exception("No camera available!")

if enable_display:
    cv2.namedWindow("Recunoaștere facială", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
    cv2.resizeWindow("Recunoaștere facială", 600, 454)
    if log_visible:
        cv2.namedWindow("Jurnal", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow("Jurnal", log_width, log_height)

# Load YOLO model
yolo_model = YOLO("yolov8n.pt")
target_object = "chair"
mode = "face"  # Default mode
last_logged_chair_count = -1

while True:
    if exit_requested:
        break

    ret, frame = camera.read()
    if not ret:
        break

    if mode == "face":
        mic = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_mic = cv2.cvtColor(mic, cv2.COLOR_BGR2RGB)

        fete_locatii = face_recognition.face_locations(rgb_mic)
        fete_encodari = face_recognition.face_encodings(rgb_mic, fete_locatii)

        current_unknown = False
        acum = datetime.now()

        if (acum - last_reset_check) >= reset_check_interval:
            last_reset_check = acum
            de_resetat = []
            for nume, timp in list(timp_prezenti.items()):
                if (acum - timp) > durata_prezenta:
                    match = next(((sid, fname) for sid, fname in studenti_cunoscute if fname == nume), None)
                    if match:
                        student_id = match[0]
                        try:
                            cursor.execute("""
                                           UPDATE attendance_current
                                           SET present=0
                                           WHERE student_id = %s
                                           """, (student_id,))
                            conn.commit()
                            log_lines.append(f"-- {nume} a fost resetat după 50 de minute.")
                            log_lines = log_lines[-max_log_lines:]
                            de_resetat.append(nume)
                        except Exception as e:
                            print(f"-- Eroare resetare pentru {nume}: {e}")
            for nume in de_resetat:
                del timp_prezenti[nume]

        for encodare, locatie in zip(fete_encodari, fete_locatii):
            potriviri = face_recognition.compare_faces(encodari_cunoscute, encodare)
            nume = "Necunoscut"
            distante = face_recognition.face_distance(encodari_cunoscute, encodare)
            if len(distante) > 0:
                index_min = np.argmin(distante)
                if potriviri[index_min]:
                    nume = studenti_cunoscute[index_min][1]

            if nume == "Necunoscut":
                current_unknown = True
            else:
                if nume not in timp_prezenti or (acum - timp_prezenti[nume]) > durata_prezenta:
                    timp_prezenti[nume] = acum
                    match = next(((sid, fname) for sid, fname in studenti_cunoscute if fname == nume), None)
                    if match:
                        student_id = match[0]
                        try:
                            cursor.execute("""
                                           INSERT INTO attendance_current (student_id, present)
                                           VALUES (%s, 1) ON DUPLICATE KEY
                                           UPDATE present=1
                                           """, (student_id,))
                            conn.commit()
                            msg = f"-- {nume} a fost marcat prezent la {acum.strftime('%H:%M:%S')}"
                        except Exception as e:
                            msg = f"-- Eroare BD pentru {nume}: {e}"
                    else:
                        msg = f"-- Elev negăsit: {nume}"
                    log_lines.append(msg)
                    log_lines = log_lines[-max_log_lines:]

            top, right, bottom, left = [v * 4 for v in locatie]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, nume, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if current_unknown:
            if not unknown_face_recent:
                log_lines.append(f"-- Necunoscut detectat la {datetime.now().strftime('%H:%M:%S')}")
                log_lines = log_lines[-max_log_lines:]
                unknown_face_recent = True
                last_unknown_face_time = datetime.now()
        else:
            # resetăm flagul dacă necunoscutul a dispărut
            if unknown_face_recent and (datetime.now() - last_unknown_face_time).total_seconds() > 3:
                unknown_face_recent = False

    elif mode == "chair":
        object_counts = 0
        results = yolo_model(frame)[0]
        for i, box in enumerate(results.boxes.data.tolist()):
            x1, y1, x2, y2, score, cls_id = box
            class_name = results.names[int(cls_id)]
            if class_name.lower() == target_object:
                object_counts += 1
                label = f"Chair #{object_counts}"
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        if object_counts != last_logged_chair_count:
            log_lines.append(f"-- {object_counts} chair(s) detected.")
            log_lines = log_lines[-max_log_lines:]
            last_logged_chair_count = object_counts

    
    if log_visible:
        log_frame = np.ones((log_height, log_width, 3), dtype=np.uint8) * 255
        lines_to_show = log_lines[-(log_height // line_height - 1):]
        y = line_height
        for line in lines_to_show:
            cv2.putText(log_frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1)
            y += line_height
        cv2.imshow("Jurnal", log_frame)

    cv2.rectangle(frame, (10, 10), (600, 40), (255, 255, 255), -1)
    cv2.putText(frame, f"1 = Iesire | 2 = Afiseaza/ascunde jurnal | 3 = Schimba camera | 4 = Mod",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)

    if enable_display:
        try:
            cv2.imshow("Recunoaștere facială", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('2'):
                log_visible = not log_visible
                if log_visible:
                    cv2.namedWindow("Jurnal", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
                    cv2.resizeWindow("Jurnal", log_width, log_height)
                else:
                    cv2.destroyWindow("Jurnal")
            elif key == ord('1'):
                exit_requested = True
            elif key == ord('3'):
                camera.release()
                if len(camera_indices) > 1:
                    current_cam_idx = (current_cam_idx + 1) % len(camera_indices)
                    camera = open_camera(camera_indices[current_cam_idx])
            elif key == ord('4'):
                mode = "chair" if mode == "face" else "face"
                log_lines.append(f"-- Modul schimbat: {mode}")
                log_lines = log_lines[-max_log_lines:]
        except cv2.error:
            print("-- Eroare interfață grafică, se trece pe mod headless.")
            enable_display = False

camera.release()
if enable_display:
    cv2.destroyAllWindows()
cursor.close()
conn.close()
