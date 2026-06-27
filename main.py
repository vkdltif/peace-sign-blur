"""
Peace Sign Blur Camera
----------------------
Aplikasi webcam yang mendeteksi peace sign dan memberikan efek blur aesthetic
seperti blur jepretan kamera, sambil memutar lagu.

Cara pakai:
1. Taruh lagu MP3/WAV kamu di folder assets/ (rename jadi your_music.mp3 atau sesuaikan di config)
2. Install dependency: pip install -r requirements.txt
3. Jalankan: python main.py
4. Tunjukkan PEACE SIGN (✌️) ke kamera untuk trigger blur + lagu
5. Lagu akan tetap berjalan & blur tetap aktif sampai lagu selesai

NOTE: Menggunakan MediaPipe Tasks API (HandLandmarker) - kompatibel versi 0.10.30+
"""

import cv2
import numpy as np
import pygame
import time
import os
import urllib.request
from collections import deque

# ==================== KONFIGURASI ====================
# GANTI NAMA FILE LAGU KAMU DI SINI
# Taruh file lagu kamu di folder assets/
# Format yang didukung: .mp3, .wav, .ogg
MUSIC_FILE = "assets/your_music.mp3"  # <-- GANTI INI dengan nama file lagumu

# Ukuran blur (semakin besar semakin blur, tapi berat)
BLUR_KERNEL_SIZE = 25

# Threshold deteksi jari (0.0 - 1.0, semakin kecil semakin sensitif)
FINGER_THRESHOLD = 0.05

# Berapa frame peace sign berturut-turut sebelum trigger (anti-noise)
TRIGGER_FRAMES = 5

# ==================== INISIALISASI MEDIAPIPE ====================
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

# Download model kalau belum ada
MODEL_PATH = "assets/hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

def download_model():
    if not os.path.exists(MODEL_PATH):
        os.makedirs("assets", exist_ok=True)
        print(f"[INFO] Downloading model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"[INFO] Model downloaded: {MODEL_PATH}")

download_model()

# Setup HandLandmarker
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==================== INISIALISASI PYGAME ====================
pygame.mixer.init()

# Variabel state
music_playing = False
blur_active = False
peace_counter = 0
last_trigger_time = 0

# History frame untuk motion blur
frame_history = deque(maxlen=5)

# ==================== FUNGSI DETEKSI ====================
def is_finger_extended(landmarks, tip_idx, pip_idx):
    """Cek apakah jari terbuka (tip di atas pip untuk jari telunjuk, tengah, manis, kelingking)"""
    return landmarks[tip_idx].y < landmarks[pip_idx].y - FINGER_THRESHOLD

def is_peace_sign(landmarks):
    """
    Deteksi peace sign: 
    - Telunjuk (8) terbuka
    - Jari tengah (12) terbuka  
    - Jari manis (16) tertutup
    - Kelingking (20) tertutup
    - Ibu jari (4) bebas (bisa terbuka/tutup)
    """
    index_open = is_finger_extended(landmarks, 8, 6)       # Telunjuk
    middle_open = is_finger_extended(landmarks, 12, 10)    # Jari tengah
    ring_closed = not is_finger_extended(landmarks, 16, 14)  # Jari manis
    pinky_closed = not is_finger_extended(landmarks, 20, 18) # Kelingking

    return index_open and middle_open and ring_closed and pinky_closed

def draw_landmarks_on_image(rgb_image, detection_result):
    """Gambar landmark tangan di frame"""
    hand_landmarks_list = detection_result.hand_landmarks
    annotated_image = np.copy(rgb_image)

    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]

        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) 
            for landmark in hand_landmarks
        ])

        solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style()
        )

    return annotated_image

# ==================== FUNGSI BLUR ====================
def apply_aesthetic_blur(frame):
    """
    Efek blur aesthetic seperti blur jepretan kamera.
    Menggabungkan:
    1. Gaussian blur besar
    2. Motion blur horizontal (kayak shutter kamera)
    3. Radial blur ringan (zoom effect)
    4. Vignette gelap di pinggir
    5. Sedikit chromatic aberration
    """
    h, w = frame.shape[:2]

    # 1. Gaussian blur besar sebagai base
    blurred = cv2.GaussianBlur(frame, (BLUR_KERNEL_SIZE, BLUR_KERNEL_SIZE), 0)

    # 2. Motion blur horizontal (simulasi shutter kamera / gerakan)
    kernel_size = 21
    kernel_motion = np.zeros((kernel_size, kernel_size))
    kernel_motion[int((kernel_size-1)/2), :] = np.ones(kernel_size)
    kernel_motion = kernel_motion / kernel_size
    motion_blurred = cv2.filter2D(blurred, -1, kernel_motion)

    # 3. Radial blur (zoom dari tengah)
    center_x, center_y = w // 2, h // 2
    radial = np.zeros_like(frame, dtype=np.float32)

    for i in range(5):
        scale = 1.0 + i * 0.03
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale)
        temp = cv2.warpAffine(blurred.astype(np.float32), M, (w, h), borderMode=cv2.BORDER_REFLECT)
        radial += temp

    radial = (radial / 5).astype(np.uint8)

    # Gabungkan motion + radial
    aesthetic = cv2.addWeighted(motion_blurred, 0.5, radial, 0.5, 0)

    # 4. Tambahkan frame history untuk ghosting effect (kayak long exposure)
    if len(frame_history) > 0:
        ghost = np.mean(list(frame_history), axis=0).astype(np.uint8)
        aesthetic = cv2.addWeighted(aesthetic, 0.7, ghost, 0.3, 0)

    # 5. Vignette effect (gelap di pinggir)
    X_resultant_kernel = cv2.getGaussianKernel(w, w/2)
    Y_resultant_kernel = cv2.getGaussianKernel(h, h/2)
    kernel = Y_resultant_kernel * X_resultant_kernel.T
    mask = kernel / kernel.max()
    mask = np.dstack([mask] * 3)

    aesthetic = (aesthetic * mask).astype(np.uint8)

    # 6. Chromatic aberration ringan (RGB shift)
    b, g, r = cv2.split(aesthetic)
    M_shift = np.float32([[1, 0, 3], [0, 1, 0]])
    b_shifted = cv2.warpAffine(b, M_shift, (w, h))
    M_shift = np.float32([[1, 0, -3], [0, 1, 0]])
    r_shifted = cv2.warpAffine(r, M_shift, (w, h))
    aesthetic = cv2.merge([b_shifted, g, r_shifted])

    return aesthetic

def draw_ui(frame, status_text, color, h, w):
    """Gambar status text di pojok kiri atas"""
    cv2.putText(frame, status_text, (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3, cv2.LINE_AA)
    cv2.putText(frame, "Tunjukkan PEACE SIGN (✌️) untuk trigger", (20, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    # Progress bar lagu (jika sedang diputar)
    if music_playing and pygame.mixer.music.get_busy():
        pos = pygame.mixer.music.get_pos() / 1000.0  # detik
        bar_w = 300
        bar_x = 20
        bar_y = h - 40
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 10), (50, 50, 50), -1)
        progress = min(pos / 15.0, 1.0)  # asumsi 15 detik
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + 10), color, -1)
        cv2.putText(frame, f"Playing: {pos:.1f}s", (bar_x, bar_y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    return frame

# ==================== MAIN LOOP ====================
def main():
    global music_playing, blur_active, peace_counter, last_trigger_time

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Webcam tidak terdeteksi!")
        return

    # Set resolusi (bisa disesuaikan)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Buat HandLandmarker
    with vision.HandLandmarker.create_from_options(options) as landmarker:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)  # Mirror
            h, w = frame.shape[:2]

            # Simpan frame untuk ghosting effect
            frame_history.append(frame.copy())

            # Konversi ke MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

            # Deteksi tangan
            detection_result = landmarker.detect(mp_image)

            # Cek apakah lagu masih playing
            if music_playing and not pygame.mixer.music.get_busy():
                music_playing = False
                blur_active = False
                peace_counter = 0
                print("[INFO] Lagu selesai. Siap trigger lagi.")

            # Deteksi peace sign (hanya jika lagu tidak sedang playing)
            peace_detected = False
            annotated_frame = frame.copy()

            if not music_playing and detection_result.hand_landmarks:
                for hand_landmarks in detection_result.hand_landmarks:
                    if is_peace_sign(hand_landmarks):
                        peace_detected = True
                        # Gambar landmark hijau untuk peace sign
                        annotated_frame = draw_landmarks_on_image(frame, detection_result)
                        break
                    else:
                        # Gambar landmark biasa
                        annotated_frame = draw_landmarks_on_image(frame, detection_result)

            # Logic trigger dengan counter (anti-noise)
            if peace_detected:
                peace_counter += 1
                cv2.putText(annotated_frame, f"Detecting: {peace_counter}/{TRIGGER_FRAMES}", (20, 130), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

                if peace_counter >= TRIGGER_FRAMES:
                    # TRIGGER!
                    if os.path.exists(MUSIC_FILE):
                        pygame.mixer.music.load(MUSIC_FILE)
                        pygame.mixer.music.play()
                        music_playing = True
                        blur_active = True
                        peace_counter = 0
                        last_trigger_time = time.time()
                        print(f"[TRIGGER] Peace sign terdeteksi! Memutar: {MUSIC_FILE}")
                    else:
                        print(f"[ERROR] File tidak ditemukan: {MUSIC_FILE}")
                        print("[ERROR] Silakan taruh file lagu kamu di folder assets/")
            else:
                peace_counter = max(0, peace_counter - 1)

            # Apply blur jika aktif
            if blur_active:
                display_frame = apply_aesthetic_blur(frame)
                status = "BLUR AKTIF - Lagu Playing"
                color = (255, 100, 200)  # Pink
            else:
                display_frame = annotated_frame
                if peace_detected:
                    status = "Peace Sign Terdeteksi!"
                    color = (0, 255, 0)  # Hijau
                else:
                    status = "Standby - Tunjukkan Peace Sign"
                    color = (200, 200, 200)  # Abu-abu

            display_frame = draw_ui(display_frame, status, color, h, w)

            cv2.imshow("Peace Sign Blur Camera", display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()
    print("[INFO] Program selesai.")

if __name__ == "__main__":
    main()
