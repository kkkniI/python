import streamlit as st
from PIL import Image

st.set_page_config(
    
    page_title="Klasifikasi Rumah adat",
    page_icon="assets/pngtree-rumah-adat-padang-minang-free-vector-and-png-png-image_5213636.png",
    layout="wide"
)


st.title("Website Klasifikasi Rumah Adat Indonesia")
st.image("assets/png-transparent-indonesia-blank-map-map-hand-monochrome-computer-wallpaper.png", use_container_width=True)
st.markdown("""
### Fitur:
- **Untuk Pengguna**: Unggah dan klasifikasikan gambar Rumah adat.
- **Untuk Admin**: Kelola threshold, informasi rumah adat, dan lihat feedback pengguna.
""")
st.write("Aplikasi ini merupakan sistem klasifikasi gambar Rumah adat Indonesia berbasis deep learning dengan arsitektur MobileNetV2.\
            Model telah dilatih untuk mengenali 5 jenis Rumah adat Indonesia dengan akurasi validasi lebih dari 93%.")

st.caption("Note: Saat ini klasifikasi terbatas pada 5 jenis Rumah adat, yaitu gadang, honai, joglo, panjang, tongkongan, " )

st.markdown("---")

# Main navigation
# --- BARIS 1: UNTUK JUDUL & TEKS ---
col_text1, col_text2 = st.columns(2)

with col_text1:
    st.header("👨‍💻 User")
    st.write("Masuk ke halaman klasifikasi untuk mencoba mendeteksi gambar rumah adat.")

with col_text2:
    st.header("🧑‍💼 Admin")
    st.write("Kelola pengaturan sistem seperti atur threshold, perbarui informasi dan gambar referensi Rumah adat, serta lihat umpan balik.")


# --- BARIS 2: UNTUK TOMBOL (Dijamin Sejajar!) ---
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🔍 Go to Page User", type="primary", use_container_width=True):
        st.switch_page("pages/User_int.py")

with col_btn2:
    if st.button("⚙️ Go to Page Admin", type="primary", use_container_width=True):
        st.switch_page("pages/Admin.py")
    
st.markdown("---")
