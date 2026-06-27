# ✌️ Peace Sign Blur Camera

Aplikasi webcam Python yang mendeteksi **peace sign** (✌️) dan memberikan efek **blur aesthetic** seperti blur jepretan kamera, sambil memutar lagu.

## Fitur
- 🎥 Real-time webcam dengan mirror effect
- ✌️ Deteksi peace sign (1 atau 2 tangan) pakai MediaPipe Tasks API
- 🎨 Blur aesthetic: motion blur + radial blur + vignette + chromatic aberration
- 🎵 Trigger lagu saat peace sign pertama kali terdeteksi
- 🔄 Lagu tetap berjalan walau tangan diangkat/turun, blur tetap aktif sampai lagu selesai
- ⏳ Setelah lagu habis, baru bisa trigger lagi

## Cara Install

```bash
# 1. Clone repo ini
git clone https://github.com/username/peace-sign-blur.git
cd peace-sign-blur

# 2. Install dependency
pip install -r requirements.txt
```

## Cara Input Lagu Kamu

1. **Siapkan lagu** ~15 detik (bisa potong di [mp3cut.net](https://mp3cut.net) atau aplikasi edit audio)
2. **Format**: `.mp3`, `.wav`, atau `.ogg`
3. **Taruh file** di folder `assets/`
4. **Rename** jadi `your_music.mp3` (atau edit `MUSIC_FILE` di `main.py`)

```
peace-sign-blur/
├── main.py
├── requirements.txt
├── README.md
└── assets/
    ├── your_music.mp3       <-- TARUH LAGU KAMU DI SINI
    └── hand_landmarker.task <-- (auto-download saat pertama kali run)
```

## Cara Pakai

```bash
python main.py
```

- Saat pertama kali run, program akan **auto-download model** `hand_landmarker.task` (~10MB)
- Tunjukkan **peace sign** (✌️) ke kamera
- Tahan sebentar sampai counter penuh (5 frame)
- **Blur aesthetic** aktif + **lagu** mulai berputar
- Lagu akan tetap jalan & blur tetap aktif sampai lagu selesai
- Setelah lagu habis, bisa trigger lagi dengan peace sign baru
- Tekan **Q** untuk keluar

## Konfigurasi

Edit bagian `KONFIGURASI` di `main.py`:

```python
MUSIC_FILE = "assets/your_music.mp3"   # Ganti nama file lagumu
BLUR_KERNEL_SIZE = 25                  # Ukuran blur (semakin besar = semakin blur)
TRIGGER_FRAMES = 5                     # Berapa frame peace sign berturut-turut sebelum trigger
```

## Efek Blur

Efek blur yang digunakan:
1. **Gaussian Blur** - base blur
2. **Motion Blur** - simulasi shutter kamera
3. **Radial Blur** - zoom effect dari tengah
4. **Ghosting** - long exposure effect dari frame sebelumnya
5. **Vignette** - gelap di pinggir layar
6. **Chromatic Aberration** - RGB shift ringan

## Catatan Penting

- **Python**: Harus Python 3.9 atau lebih baru
- **MediaPipe**: Menggunakan Tasks API (`mediapipe.tasks.vision.HandLandmarker`) - kompatibel versi 0.10.30+
- **Model**: Auto-download `hand_landmarker.task` saat pertama kali run (butuh internet)
- **Pencahayaan**: Pastikan cukup terang agar deteksi tangan akurat
- **Peace Sign**: Telunjuk & jari tengah terbuka, jari manis & kelingking tertutup
- **Ibu Jari**: Bebas (bisa terbuka/tutup)

## Troubleshooting

### Error "No module named 'mediapipe'"
```bash
pip install mediapipe
```

### Error "Could not find a version"
```bash
pip install --upgrade pip
pip install mediapipe
```

### Model tidak terdownload
Bisa download manual dari:
https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

Taruh di folder `assets/hand_landmarker.task`
