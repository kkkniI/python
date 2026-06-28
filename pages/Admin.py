import streamlit as st
import json
import os
import shutil
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image

# --- KONFIGURASI GLOBAL ---
GSHEET_NAME = "feedback_prediksi_rumah_adat"
PASSWORD_ADMIN = "admin123" # Ubah password ini sesuai keinginanmu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Admin Panel - Rumah Adat", page_icon="⚙️", layout="wide")

# --- SISTEM LOGIN SEDERHANA ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.title("🔒 Login Admin")
    password_input = st.text_input("Masukkan Password Admin:", type="password")
    if st.button("Login"):
        if password_input == PASSWORD_ADMIN:
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Password salah!")
    st.stop() # Hentikan eksekusi kode di bawah ini jika belum login

# Jika sudah login, tampilkan tombol logout di sidebar
with st.sidebar:
    st.success("👨‍💻 Admin Aktif")
    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

st.title("⚙️ Panel Kelola Sistem")
st.markdown("---")

# Buat Tab untuk navigasi yang rapi
tab1, tab2, tab3, tab4 = st.tabs([
    "🎛️ Pengaturan Threshold", 
    "📝 Kelola Informasi", 
    "🖼️ Kelola Gambar", 
    "📊 Umpan Balik (Feedback)"
])

# ==========================================
# TAB 1: PENGATURAN THRESHOLD
# ==========================================
with tab1:
    st.header("Pengaturan Batas Keyakinan (Threshold)")
    st.write("Tentukan nilai minimal confidence model untuk menampilkan hasil prediksi.")
    
    # Baca config.json
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as f:
            current_threshold = int(json.load(f).get("threshold", 60))
    except (FileNotFoundError, json.JSONDecodeError):
        current_threshold = 60 # Default

    with st.form("threshold_form"):
        new_threshold = st.slider("Nilai Threshold (%)", min_value=1, max_value=100, value=current_threshold)
        submit_threshold = st.form_submit_button("Simpan Pengaturan")
        
        if submit_threshold:
            with open(config_path, 'w') as f:
                json.dump({"threshold": str(new_threshold)}, f)
            st.success(f"✅ Threshold berhasil diperbarui menjadi {new_threshold}%!")

# ==========================================
# TAB 2: KELOLA INFORMASI RUMAH ADAT
# ==========================================
with tab2:
    st.header("Kelola Informasi Detail Rumah Adat")
    
    info_path = 'info_tambahan.json'
    try:
        with open(info_path, 'r') as f:
            house_info_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        house_info_data = {}

    labels_path = 'labels.json'
    try:
        with open(labels_path, 'r') as f:
            labels = json.load(f)
    except FileNotFoundError:
        labels = []

    if not labels:
        st.warning("File labels.json tidak ditemukan atau kosong.")
    else:
        selected_house = st.selectbox("Pilih Rumah Adat untuk diedit:", labels)
        
        current_info = house_info_data.get(selected_house, {})
        
        with st.form("info_form"):
            nama = st.text_input("Nama Rumah Adat", value=current_info.get("Nama", ""))
            asal = st.text_input("Asal Daerah", value=current_info.get("Asal Daerah", ""))
            ciri = st.text_area("Ciri Khas", value=current_info.get("Ciri Khas", ""))
            fungsi = st.text_area("Fungsi", value=current_info.get("Fungsi", ""))
            material = st.text_area("Material Utama", value=current_info.get("Material Utama", ""))
            
            submit_info = st.form_submit_button("Simpan Informasi")
            
            if submit_info:
                house_info_data[selected_house] = {
                    "Nama": nama,
                    "Asal Daerah": asal,
                    "Ciri Khas": ciri,
                    "Fungsi": fungsi,
                    "Material Utama": material
                }
                with open(info_path, 'w') as f:
                    json.dump(house_info_data, f, indent=4)
                st.success(f"✅ Informasi {selected_house} berhasil disimpan!")

# ==========================================
# TAB 3: KELOLA GAMBAR REFERENSI
# ==========================================
with tab3:
    st.header("Kelola Gambar Referensi Lokal")
    st.write("Gambar ini akan muncul sebagai contoh setelah user melakukan prediksi.")
    
    if labels:
        selected_house_img = st.selectbox("Pilih folder Rumah Adat:", labels, key="img_select")
        folder_path = os.path.join("images-example", selected_house_img)
        
        # Buat folder jika belum ada
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # Form Upload Gambar Baru
        uploaded_new_img = st.file_uploader(f"Tambahkan gambar referensi untuk {selected_house_img}", type=['jpg', 'jpeg', 'png'])
        img_caption = st.text_input("Judul/Caption Gambar (Opsional)", placeholder="Misal: Tampak Depan")
        
        if st.button("Unggah Gambar", type="primary"):
            if uploaded_new_img is not None:
                if not img_caption:
                    img_caption = f"referensi_{len(os.listdir(folder_path)) + 1}"
                
                # Bersihkan nama file dari spasi dan karakter aneh
                safe_caption = "".join([c if c.isalnum() else "_" for c in img_caption])
                file_extension = uploaded_new_img.name.split(".")[-1]
                save_path = os.path.join(folder_path, f"{safe_caption}.{file_extension}")
                
                img = Image.open(uploaded_new_img).convert('RGB')
                img.save(save_path)
                st.success("✅ Gambar berhasil ditambahkan!")
                st.rerun()
            else:
                st.error("Pilih gambar terlebih dahulu.")
                
        st.markdown("---")
        st.subheader("Gambar Saat Ini")
        
        # Tampilkan Gambar yang ada beserta tombol hapus
        existing_images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if existing_images:
            cols = st.columns(3)
            for idx, img_file in enumerate(existing_images):
                with cols[idx % 3]:
                    img_path = os.path.join(folder_path, img_file)
                    st.image(img_path, caption=img_file, use_container_width=True)
                    if st.button(f"🗑️ Hapus", key=f"del_{img_file}"):
                        os.remove(img_path)
                        st.success("Gambar dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada gambar referensi di folder ini.")

# ==========================================
# TAB 4: LIHAT UMPAN BALIK (GOOGLE SHEETS)
# ==========================================
with tab4:
    st.header("📊 Data Umpan Balik Pengguna")
    
    if st.button("🔄 Segarkan Data (Refresh)"):
        st.rerun()
        
    try:
        sheets_credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gsheets_sa"],
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(sheets_credentials)
        
        spreadsheet = gc.open(GSHEET_NAME)
        worksheet = spreadsheet.sheet1
        
        # Ambil semua data
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Tampilkan statistik singkat
            st.subheader("Statistik Singkat")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Feedback", len(df))
            
            if 'Status' in df.columns or 'Benar/Salah' in df.columns:
                # Menyesuaikan nama kolom status dari user_int
                status_col = 'Status' if 'Status' in df.columns else df.columns[3] 
                benar = len(df[df[status_col] == "Benar"])
                col2.metric("Prediksi Benar", benar)
                col3.metric("Akurasi User", f"{(benar/len(df))*100:.1f}%")
        else:
            st.info("Belum ada data umpan balik di Google Sheets.")
            
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets. Pastikan koneksi dan nama file benar. Error: {e}")