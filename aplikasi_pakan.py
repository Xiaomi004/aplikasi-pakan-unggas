import streamlit as st
import pandas as pd
import pulp

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Formulator Pakan",
    page_icon="🐔",
    layout="wide"
)

# --- Judul Aplikasi ---
st.title('🐔 Aplikasi Formulator Pakan Unggas')
st.write('Alat bantu cerdas untuk menyusun ransum pakan dengan biaya terendah.')

# --- FUNGSI KALKULASI FORMULASI (INTI APLIKASI) ---
def hitung_formulasi(df_bahan, target):
    # 1. Inisialisasi Masalah Optimasi
    # Kita ingin 'meminimalkan' (LpMinimize) biaya
    prob = pulp.LpProblem("Formulasi_Pakan_Biaya_Terendah", pulp.LpMinimize)

    # 2. Membuat Variabel Keputusan
    # Variabelnya adalah persentase setiap bahan pakan dalam campuran
    bahan_vars = pulp.LpVariable.dicts("Bahan", df_bahan['Nama Bahan'], lowBound=0, cat='Continuous')

    # 3. Menentukan Fungsi Tujuan (Objective Function)
    # Tujuannya adalah total biaya, yaitu jumlah dari (persentase bahan * harga bahan)
    prob += pulp.lpSum([bahan_vars[i] * df_bahan[df_bahan['Nama Bahan'] == i]['Harga (Rp/kg)'].iloc[0] for i in df_bahan['Nama Bahan']]), "Total Biaya"

    # 4. Menentukan Batasan (Constraints)
    # Aturan-aturan yang harus dipenuhi
    
    # Aturan 1: Total persentase semua bahan harus 100% (atau 1.0 dalam desimal)
    prob += pulp.lpSum([bahan_vars[i] for i in df_bahan['Nama Bahan']]) == 1.0, "Total Persentase"
    
    # Aturan 2-5: Nutrisi harus memenuhi target minimum
    # Total Protein >= Target Protein
    prob += pulp.lpSum([bahan_vars[i] * (df_bahan[df_bahan['Nama Bahan'] == i]['Protein Kasar (%)'].iloc[0] / 100.0) for i in df_bahan['Nama Bahan']]) >= (target['protein'] / 100.0), "Protein_Minimum"
    # Total Energi >= Target Energi
    prob += pulp.lpSum([bahan_vars[i] * df_bahan[df_bahan['Nama Bahan'] == i]['Energi (kkal/kg)'].iloc[0] for i in df_bahan['Nama Bahan']]) >= target['energi'], "Energi_Minimum"
    # Total Kalsium >= Target Kalsium
    prob += pulp.lpSum([bahan_vars[i] * (df_bahan[df_bahan['Nama Bahan'] == i]['Kalsium (%)'].iloc[0] / 100.0) for i in df_bahan['Nama Bahan']]) >= (target['kalsium'] / 100.0), "Kalsium_Minimum"
    # Total Fosfor >= Target Fosfor
    prob += pulp.lpSum([bahan_vars[i] * (df_bahan[df_bahan['Nama Bahan'] == i]['Fosfor (%)'].iloc[0] / 100.0) for i in df_bahan['Nama Bahan']]) >= (target['fosfor'] / 100.0), "Fosfor_Minimum"

    # 5. Menyelesaikan Masalah
    prob.solve()

    # 6. Mengembalikan Hasil
    return prob, bahan_vars

# --- Data Awal (Default) ---
default_bahan_pakan = {
    'Nama Bahan': ['Jagung Giling', 'Bungkil Kedelai (SBM)', 'Dedak Padi Halus', 'Minyak Sawit (CPO)'],
    'Harga (Rp/kg)': [5500, 8500, 3500, 15000], 'Protein Kasar (%)': [8.5, 46.0, 12.0, 0.0],
    'Energi (kkal/kg)': [3350, 2250, 2800, 8800], 'Kalsium (%)': [0.02, 0.30, 0.10, 0.0],
    'Fosfor (%)': [0.28, 0.65, 1.20, 0.0]
}
default_target_nutrisi = {"nama_ransum": "Broiler Starter (Default)", "protein": 23.0, "energi": 3200.0, "kalsium": 1.0, "fosfor": 0.5}

# Inisialisasi session state
if 'bahan_pakan' not in st.session_state:
    st.session_state.bahan_pakan = pd.DataFrame(default_bahan_pakan)

# --- Tata Letak Aplikasi ---
col1, col2 = st.columns([1, 1.5]) # Kolom kanan sedikit lebih lebar

with col1:
    st.header('Bahan Pakan')
    with st.expander("📝 Klik untuk Tambah Bahan Pakan Baru", expanded=False):
        with st.form(key='form_bahan_pakan', clear_on_submit=True):
            nama_bahan = st.text_input('Nama Bahan')
            harga = st.number_input('Harga (Rp/kg)', min_value=0)
            protein = st.number_input('Protein Kasar (%)', min_value=0.0, format='%.2f')
            energi = st.number_input('Energi (kkal/kg)', min_value=0)
            kalsium = st.number_input('Kalsium (%)', min_value=0.0, format='%.2f')
            fosfor = st.number_input('Fosfor (%)', min_value=0.0, format='%.2f')
            submitted = st.form_submit_button('Tambahkan Bahan')
            if submitted and nama_bahan:
                bahan_baru = pd.DataFrame([{'Nama Bahan': nama_bahan, 'Harga (Rp/kg)': harga, 'Protein Kasar (%)': protein, 'Energi (kkal/kg)': energi, 'Kalsium (%)': kalsium, 'Fosfor (%)': fosfor}])
                st.session_state.bahan_pakan = pd.concat([st.session_state.bahan_pakan, bahan_baru], ignore_index=True)
                st.success(f'Bahan "{nama_bahan}" berhasil ditambah!')
    st.dataframe(st.session_state.bahan_pakan, use_container_width=True)

with col2:
    st.header('Formulasi Ransum')
    with st.form(key='form_kebutuhan'):
        nama_ransum = st.text_input('Nama Ransum', value=default_target_nutrisi["nama_ransum"])
        target_protein = st.number_input('Target Protein Kasar (%)', min_value=0.0, value=default_target_nutrisi["protein"], format='%.2f')
        target_energi = st.number_input('Target Energi (kkal/kg)', min_value=0, value=int(default_target_nutrisi["energi"]))
        target_kalsium = st.number_input('Target Kalsium (%)', min_value=0.0, value=default_target_nutrisi["kalsium"], format='%.2f')
        target_fosfor = st.number_input('Target Fosfor (%)', min_value=0.0, value=default_target_nutrisi["fosfor"], format='%.2f')
        calculate_button = st.form_submit_button(label='Hitung Formulasi!')

    if calculate_button:
        # Mengambil data dari state
        df_bahan = st.session_state.bahan_pakan
        targets = {'protein': target_protein, 'energi': target_energi, 'kalsium': target_kalsium, 'fosfor': target_fosfor}

        # Memanggil fungsi kalkulasi
        problem, bahan_vars = hitung_formulasi(df_bahan, targets)
        
        st.subheader(f"Hasil Formulasi untuk: {nama_ransum}")
        
        # Cek status hasil
        if pulp.LpStatus[problem.status] == 'Optimal':
            hasil = []
            for var in bahan_vars:
                if bahan_vars[var].varValue > 0:
                    hasil.append({'Bahan Pakan': var, 'Persentase (%)': f"{bahan_vars[var].varValue*100:.2f}"})
            
            df_hasil = pd.DataFrame(hasil)
            st.dataframe(df_hasil, use_container_width=True, hide_index=True)

            total_biaya = pulp.value(problem.objective)
            st.metric(label="Total Biaya per 100 kg", value=f"Rp {total_biaya:,.2f}")
            st.metric(label="Total Biaya per kg", value=f"Rp {total_biaya/100:,.2f}")
            st.success("Formulasi optimal berhasil ditemukan!", icon="✅")
        else:
            st.error("Formulasi tidak ditemukan. Coba periksa kembali ketersediaan nutrisi pada bahan atau sesuaikan target Anda.", icon="❌")