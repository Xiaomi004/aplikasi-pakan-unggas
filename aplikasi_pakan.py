hereimport streamlit as st
import pandas as pd
import pulp

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Formulator Pakan Presisi",
    page_icon="🧪",
    layout="wide"
)

# --- Judul Aplikasi ---
st.title('🧪 Aplikasi Formulator Pakan Presisi')
st.write('Menyusun ransum unggas dengan kendali asam amino, serat, dan lemak.')

# --- FUNGSI KALKULASI FORMULASI ---
def hitung_formulasi(df_bahan, target):
    # Inisialisasi Masalah
    prob = pulp.LpProblem("Formulasi_Pakan", pulp.LpMinimize)
    bahan_vars = pulp.LpVariable.dicts("Bahan", df_bahan['Nama Bahan'], lowBound=0, upBound=1, cat='Continuous')

    # Fungsi Tujuan: Minimalkan Biaya
    prob += pulp.lpSum([bahan_vars[i] * df_bahan.loc[df_bahan['Nama Bahan'] == i, 'Harga (Rp/kg)'].iloc[0] for i in df_bahan['Nama Bahan']]), "Total Biaya"

    # Batasan-batasan (Constraints)
    # Total persentase harus 100%
    prob += pulp.lpSum([bahan_vars[i] for i in df_bahan['Nama Bahan']]) == 1.0, "Total_Persentase"

    # Fungsi untuk membuat batasan nutrisi
    def add_constraint(nutrient_name, target_value, is_max=False):
        total_nutrient = pulp.lpSum([bahan_vars[i] * (df_bahan.loc[df_bahan['Nama Bahan'] == i, f'{nutrient_name} (%)'].iloc[0] / 100.0) for i in df_bahan['Nama Bahan']])
        if is_max:
            prob += total_nutrient <= (target_value / 100.0), f'{nutrient_name}_Maximum'
        else:
            prob += total_nutrient >= (target_value / 100.0), f'{nutrient_name}_Minimum'
    
    # Menambahkan batasan untuk setiap nutrisi
    prob += pulp.lpSum([bahan_vars[i] * df_bahan.loc[df_bahan['Nama Bahan'] == i, 'Energi (kkal/kg)'].iloc[0] for i in df_bahan['Nama Bahan']]) >= target['energi'], "Energi_Minimum"
    add_constraint('Protein Kasar', target['protein'])
    add_constraint('Kalsium', target['kalsium'])
    add_constraint('Fosfor', target['fosfor'])
    add_constraint('Lisin', target['lisin'])
    add_constraint('Metionin', target['metionin'])
    add_constraint('Treonin', target['treonin'])
    add_constraint('Serat Kasar', target['serat_kasar'], is_max=True) # Serat Kasar sebagai batas MAKSIMUM

    # Selesaikan masalah
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return prob, bahan_vars

# --- DATA BAHAN PAKAN (dengan penambahan LK, SK, Asam Amino) ---
default_bahan_pakan = {
    'Nama Bahan': ['Jagung Giling', 'Bungkil Kedelai', 'Dedak Padi', 'MBM', 'Pollard', 'CGM', 'Minyak Sawit', 'Kapur', 'DCP', 'Premix'],
    'Harga (Rp/kg)': [6000, 9000, 3500, 7500, 4500, 11000, 15000, 1500, 18000, 25000],
    'Protein Kasar (%)': [8.5, 46.0, 12.0, 50.0, 15.5, 60.0, 0.0, 0.0, 0.0, 0.0],
    'Energi (kkal/kg)': [3350, 2250, 2800, 2400, 1850, 3800, 8800, 0, 0, 0],
    'Kalsium (%)': [0.02, 0.30, 0.10, 8.5, 0.13, 0.05, 0.0, 38.0, 23.0, 0.0],
    'Fosfor (%)': [0.28, 0.65, 1.20, 4.5, 1.0, 0.2, 0.0, 0.01, 18.0, 0.0],
    'Lemak Kasar (%)': [3.9, 1.5, 13.0, 9.0, 4.5, 3.0, 99.0, 0.0, 0.0, 0.0],
    'Serat Kasar (%)': [2.2, 6.0, 12.0, 2.5, 9.0, 2.0, 0.0, 0.0, 0.0, 0.0],
    'Lisin (%)': [0.25, 2.9, 0.55, 2.8, 0.6, 1.6, 0.0, 0.0, 0.0, 0.0],
    'Metionin (%)': [0.18, 0.65, 0.25, 0.7, 0.25, 1.2, 0.0, 0.0, 0.0, 0.0],
    'Treonin (%)': [0.30, 1.8, 0.45, 1.8, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0]
}

# --- PRESET TARGET FORMULASI ---
target_presets = {
    "Broiler Starter": {"protein": 22.0, "energi": 3100.0, "kalsium": 1.0, "fosfor": 0.45, "serat_kasar": 4.0, "lisin": 1.25, "metionin": 0.55, "treonin": 0.85},
    "Broiler Finisher": {"protein": 20.0, "energi": 3200.0, "kalsium": 0.9, "fosfor": 0.35, "serat_kasar": 5.0, "lisin": 1.10, "metionin": 0.45, "treonin": 0.75},
    "Ayam Petelur": {"protein": 17.5, "energi": 2800.0, "kalsium": 4.2, "fosfor": 0.40, "serat_kasar": 6.0, "lisin": 0.90, "metionin": 0.42, "treonin": 0.65}
}

# Inisialisasi session state
if 'bahan_pakan' not in st.session_state:
    st.session_state.bahan_pakan = pd.DataFrame(default_bahan_pakan)

# --- Tata Letak Aplikasi ---
col1, col2 = st.columns([1.5, 1])

with col1:
    st.header("Database Bahan Pakan")
    st.dataframe(st.session_state.bahan_pakan, use_container_width=True, height=385)

with col2:
    st.header("Target Formulasi")
    pilihan_target = st.selectbox("Pilih Preset Formulasi:", options=list(target_presets.keys()))
    selected_preset = target_presets[pilihan_target]

    with st.form(key='form_kebutuhan'):
        st.write(f"**Preset untuk: {pilihan_target}**")
        c1, c2 = st.columns(2)
        target_protein = c1.number_input('Min. Protein (%)', value=selected_preset["protein"], format='%.2f')
        target_energi = c2.number_input('Min. Energi (kkal/kg)', value=int(selected_preset["energi"]))
        target_kalsium = c1.number_input('Min. Kalsium (%)', value=selected_preset["kalsium"], format='%.2f')
        target_fosfor = c2.number_input('Min. Fosfor (%)', value=selected_preset["fosfor"], format='%.2f')
        target_serat_kasar = c1.number_input('Maks. Serat Kasar (%)', value=selected_preset["serat_kasar"], format='%.2f')
        target_lisin = c2.number_input('Min. Lisin (%)', value=selected_preset["lisin"], format='%.2f')
        target_metionin = c1.number_input('Min. Metionin (%)', value=selected_preset["metionin"], format='%.2f')
        target_treonin = c2.number_input('Min. Treonin (%)', value=selected_preset["treonin"], format='%.2f')
        
        calculate_button = st.form_submit_button(label='⚡ Hitung Formulasi!')

# --- Tampilan Hasil ---
if calculate_button:
    df_bahan = st.session_state.bahan_pakan
    targets = {k: v for k, v in locals().items() if k.startswith('target_')}

    problem, bahan_vars = hitung_formulasi(df_bahan, targets)

    st.header(f"✅ Hasil Formulasi: {pilihan_target}")
    if pulp.LpStatus[problem.status] == 'Optimal':
        # Tampilkan Resep
        hasil = [{'Bahan Pakan': name, 'Persentase (%)': f"{var.varValue*100:.2f}"} for name, var in bahan_vars.items() if var.varValue > 0]
        df_hasil = pd.DataFrame(hasil).sort_values(by='Persentase (%)', ascending=False).reset_index(drop=True)
        st.dataframe(df_hasil, use_container_width=True, hide_index=True)

        # Tampilkan Biaya
        total_biaya = pulp.value(problem.objective)
        st.metric(label="Biaya per kg Pakan", value=f"Rp {total_biaya/100:,.2f}")

        # Tampilkan Ringkasan Nutrisi Hasil Formulasi
        with st.expander("Lihat Ringkasan Nutrisi Hasil Formulasi"):
            nutrients = [col for col in default_bahan_pakan.keys() if col not in ['Nama Bahan', 'Harga (Rp/kg)']]
            summary = {}
            for nutrient in nutrients:
                val = sum(bahan_vars[bahan['Nama Bahan']].varValue * bahan[nutrient] for index, bahan in df_bahan.iterrows())
                summary[nutrient] = f"{val:.2f}"
            st.json(summary)
        
        st.success("Formulasi optimal berhasil ditemukan!", icon="🎉")
    else:
        st.error(f"Formulasi tidak ditemukan ({pulp.LpStatus[problem.status]}). Coba periksa kembali data bahan atau target Anda.", icon="❌")
