import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from PIL import Image
import os
import json
from datetime import datetime
import gspread
from google.oauth2 import service_account
import time
import random

# --- FUNGSI NAVBAR/TASKBAR ATAS ---
def taskbar_navigasi():
    cols = st.columns(3) # Membagi layar jadi 3 kolom sejajar
    with cols[0]:
        st.page_link("app.py", label="🏠 Beranda Utama", use_container_width=True)
    # with cols[1]:
    #     st.page_link("pages/User_int.py", label="🔍 Coba Prediksi", use_container_width=True)
    # with cols[1]:
    #     st.page_link("pages/Admin.py", label="⚙️ Panel Admin", use_container_width=True)
    # st.markdown("---") # Garis pembatas bawah navbar

# Panggil fungsinya agar muncul di layar
taskbar_navigasi()
# --- KONFIGURASI GLOBAL ---
GSHEET_NAME = "feedback_prediksi_rumah_adat"

# --- CACHING FUNCTIONS ---
@st.cache_resource
def load_prediction_model():
    return tf.keras.models.load_model('model.h5')

@st.cache_data
def load_labels():
    with open('labels.json', 'r') as f:
        return json.load(f)

# --- INITIALIZATION GOOGLE SHEETS ---
# Pastikan kamu sudah mengatur secrets.toml untuk [gsheets_sa]
try:
    sheets_credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gsheets_sa"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(sheets_credentials)
    gsheets_connected = True
except Exception as e:
    st.sidebar.error("Koneksi Google Sheets belum diatur.")
    gsheets_connected = False

model = load_prediction_model()

# --- HELPER FUNCTIONS ---
def get_house_info(house_name):
    """Membaca info tambahan dari file lokal"""
    try:
        with open('info_tambahan.json', 'r') as f:
            house_info = json.load(f)
        return house_info.get(house_name, {})
    except FileNotFoundError:
        return {}

def get_reference_images(house_name, max_images=5):
    """Membaca maksimal 5 gambar acak dari folder lokal images-example/"""
    folder_path = os.path.join("images-example", house_name)
    images = []
    
    if os.path.exists(folder_path):
        # 1. Kumpulkan semua nama file gambar yang valid
        semua_file = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # 2. Acak urutannya agar gambar yang muncul bervariasi
        random.shuffle(semua_file)
        
        # 3. Ambil maksimal 5 file (atau sesuai jumlah max_images)
        file_terpilih = semua_file[:max_images]
        
        # 4. Buka dan proses gambar yang sudah terpilih
        for filename in file_terpilih:
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path)
            caption = os.path.splitext(filename)[0]
            images.append((img, caption))
            
    return images

# def preprocess_image(uploaded_file, target_size=(224, 224)):
#     img = Image.open(uploaded_file)
#     img = img.convert('RGB')
#     img = img.resize(target_size)
#     img_array = image.img_to_array(img)
#     img_array = img_array / 255.0
#     img_array = np.expand_dims(img_array, axis=0) 
#     return img_array

# --- BAGIAN ATAS (Fungsi Pengolah Gambar) ---
def preprocess_image(uploaded_file, target_size=(224, 224)):
    img = Image.open(uploaded_file)
    img = img.convert('RGB')
    img = img.resize(target_size)
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0 # <--- Kuncinya di sini
    img_array = np.expand_dims(img_array, axis=0) 
    return img_array

#
def submit_feedback(predicted_house, confidence, is_correct, suggestions, true_label, image_path):
    if not gsheets_connected:
        st.error("Gagal mengirim: Google Sheets belum terhubung.")
        return False
        
    try:
        spreadsheet = gc.open(GSHEET_NAME)
        worksheet = spreadsheet.sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        feedback_data = [
            timestamp, predicted_house, f"{confidence:.4%}",
            "Benar" if is_correct else "Salah",
            suggestions, true_label if true_label else predicted_house,
            image_path
        ]
        worksheet.append_row(feedback_data)
        return True
    except Exception as e:
        st.error(f"Error menyinkronkan ke Google Sheets: {str(e)}")
        return False

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Klasifikasi Rumah Adat", page_icon="🛖", layout="wide")

st.title("🛖 Sistem Klasifikasi Rumah Adat Indonesia")
st.markdown("---")

uploaded_file = st.file_uploader("Unggah gambar rumah adat (jpg, jpeg, png)...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    uploaded_img = Image.open(uploaded_file)
    st.image(uploaded_img, caption="Gambar yang Diunggah", width=400)
    
    # Session state agar tidak memprediksi ulang saat mengetik di form
    if 'prediction_result' not in st.session_state or st.session_state.current_file != uploaded_file.name:
        labels = load_labels()
        
        # Baca Threshold dari file config lokal
        try:
            with open('config.json', 'r') as f:
                threshold_value = json.load(f)["threshold"]
            threshold = float(threshold_value) / 100.0
        except FileNotFoundError:
            threshold = 0.60 # Fallback jika file config.json belum dibuat
        
        with st.spinner('⏳ Sedang menganalisis gambar rumah adat... Mohon tunggu.'):
            time.sleep(4)
            
        # Proses & Prediksi
        processed_image = preprocess_image(uploaded_file)
        predictions = model.predict(processed_image)[0]
        predicted_class = np.argmax(predictions)
        
        st.session_state.prediction_result = {
            "house": labels[predicted_class],
            "confidence": predictions[predicted_class],
            "threshold": threshold,
            "labels": labels
        }
        st.session_state.current_file = uploaded_file.name

    res = st.session_state.prediction_result
    
    if res["confidence"] >= res["threshold"]:
        predicted_house = res["house"]
        st.success(f"🧠 Prediksi Model: **{predicted_house}** | 📊 Tingkat Keyakinan: **{res['confidence'] * 100:.2f}%**")

        house_info = get_house_info(predicted_house)

        # Informasi Detail
        st.subheader("Informasi Detail")
        st.write(f"**Nama:** {house_info.get('Nama', 'Belum ada data')}")
        st.write(f"**Asal Daerah:** {house_info.get('Asal Daerah', 'Belum ada data')}")
        st.write(f"**Ciri Khas:** {house_info.get('Ciri Khas', 'Belum ada data')}")
        st.write(f"**Fungsi:** {house_info.get('Fungsi', 'Belum ada data')}")
        st.write(f"**Material Utama:** {house_info.get('Material Utama', 'Belum ada data')}")

        # Gambar Referensi Lokal
        st.subheader("Gambar Referensi")
        reference_images = get_reference_images(predicted_house)
        if reference_images:
            cols = st.columns(len(reference_images))
            for idx, (img, caption) in enumerate(reference_images):
                with cols[idx]:
                    st.image(img, width='stretch')
                    st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px;'>{caption.title()}</p>", unsafe_allow_html=True)
        else:
            st.info(f"Belum ada gambar referensi untuk {predicted_house} di folder lokal.")
        
        st.markdown("---")
        
        # Feedback Section
        st.header("📝 Berikan Feedback")
        st.write("Bantu kami meningkatkan akurasi model ini.")
        
        with st.form("feedback_form"):
            choice = st.radio("Apakah prediksi sistem ini benar?", ["Ya", "Tidak"], horizontal=True)
            true_label = None
            if choice == "Tidak":
                true_label = st.selectbox("Pilih rumah adat yang seharusnya:", res["labels"])
            
            suggestions = st.text_area("Saran atau komentar (opsional):")
            submit_btn = st.form_submit_button("Kirim Feedback")

            if submit_btn:
                # 1. Buat folder 'uploads' jika belum ada
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                
                # 2. Simpan gambar ke folder uploads/ lokal
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"uploads/{timestamp}_{predicted_house}.jpg"
                uploaded_img.convert('RGB').save(image_filename, "JPEG")
                
                # 3. Kirim data ke Google Sheets
                success = submit_feedback(
                    predicted_house, res["confidence"], (choice == "Ya"), 
                    suggestions, true_label, image_filename
                )
                
                if success:
                    st.success("✅ Terima kasih! Feedback kamu berhasil disimpan.")
    
    else:
        st.warning(f"🔍 Gambar tidak dikenali. Tingkat keyakinan ({res['confidence']:.2%}) berada di bawah batas minimum ({res['threshold']:.2%}).")