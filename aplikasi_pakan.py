# 1. IMPORT LIBRARY YANG DIBUTUHKAN
import streamlit as st
import pandas as pd
import pulp

# 2. KONFIGURASI HALAMAN APLIKASI
# Mengatur judul tab, ikon, dan tata letak halaman menjadi lebar
st.set_page_config(
    page_title="Irsan NutriTech (Streamlit)",
    page_icon="🐔",
    layout="wide"
)

# --- FUNGSI INTI: MESIN KALKULASI FORMULASI ---
def hitung_formulasi(df_bahan, targets, usage_limits):
    """
    Fungsi ini adalah jantung dari aplikasi. Ia menerima data bahan, target nutrisi,
    dan batasan penggunaan, lalu menghitung resep termurah menggunakan PuLP.
    """
    # Inisialisasi masalah: kita ingin meminimalkan biaya
    prob = pulp.LpProblem("Formulasi_Ransum_Optimal", pulp.LpMinimize)

    # Membuat variabel untuk setiap bahan pakan (persentase penggunaan)
    bahan_vars = pulp.LpVariable.dicts("Bahan", df_bahan['nama'], lowBound=0, upBound=1, cat='Continuous')

    # Fungsi Tujuan: Minimalkan total biaya (harga * persentase)
    prob += pulp.lpSum([bahan_vars[bahan['nama']] * bahan['harga_kg'] for _, bahan in df_bahan.iterrows()]), "Total Biaya"

    # --- BATASAN-BATASAN (CONSTRAINTS) ---
    # 1. Total persentase semua bahan harus tepat 100% (atau 1.0)
    prob += pulp.lpSum([bahan_vars[nama] for nama in df_bahan['nama']]) == 1.0, "Total_Persentase_100"

    # 2. Batasan Nutrisi (Protein, Energi, dll.)
    for key, (min_val, max_val) in targets.items():
        # Lewati jika target tidak diatur (nilai min dan max adalah 0)
        if min_val == 0 and max_val == 0:
            continue
        
        # Hitung total nutrisi dari campuran
        total_nutrient = pulp.lpSum([bahan_vars[bahan['nama']] * bahan[key] for _, bahan in df_bahan.iterrows()])
        
        # Aturan: Total nutrisi harus >= target minimum
        prob += total_nutrient >= min_val, f"Nutrisi_Min_{key}"
        # Aturan: Total nutrisi harus <= target maksimum
        prob += total_nutrient <= max_val, f"Nutrisi_Max_{key}"

    # 3. Batasan Penggunaan Bahan (Min/Max Use)
    for nama_bahan, limits in usage_limits.items():
        # Pastikan bahan ada di daftar variabel sebelum menambahkan batasan
        if nama_bahan in bahan_vars:
            # Aturan: Penggunaan bahan harus >= batas minimumnya
            prob += bahan_vars[nama_bahan] >= limits['min'] / 100.0, f"Min_Use_{nama_bahan.replace(' ', '_')}"
            # Aturan: Penggunaan bahan harus <= batas maksimumnya
            prob += bahan_vars[nama_bahan] <= limits['max'] / 100.0, f"Max_Use_{nama_bahan.replace(' ', '_')}"

    # Memecahkan masalah (menjalankan kalkulasi) tanpa menampilkan log solver
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # Mengembalikan hasil kalkulasi
    return prob, bahan_vars


# 3. DATABASE (DIEKSTRAK DARI FILE HTML ANDA)
# Menggunakan st.cache_data agar data tidak perlu dimuat ulang setiap kali ada interaksi
@st.cache_data
def load_data():
    """Memuat semua data awal (bahan, target, batasan) ke dalam memori."""
    bahan_pakan_data = {
        'nama': ["Jagung", "Dedak", "SBM", "PKM", "MBM", "CGM", "DDGS", "CPO", "MCP", "Garam", "T.Batu", "Choline C.", "Citric A.", "Toxin Binder", "Premik", "Min HC", "ViteL", "NeuTron", "VITHC", "EnzMix", "EnzFit", "Fenol", "Cu", "SalM", "Bctr"],
        'harga_kg': [6000, 3000, 8700, 2500, 10500, 12500, 7000, 16500, 13500, 3000, 400, 23000, 9000, 23000, 40000, 55000, 45000, 45000, 200000, 90000, 20000, 20000, 30000, 120000, 80000],
        'protein': [8.5, 11.5, 44, 15, 50, 60, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'energi_kcal_kg': [3350, 2400, 2400, 1800, 2150, 3750, 2800, 9000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'lemak': [3.8, 8, 1, 8, 10, 2.5, 10, 99.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'serat_kasar': [2.5, 9, 4.5, 17, 2.5, 2.5, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.5, 0.5, 0, 0, 0, 0, 0, 0, 0],
        'kalsium': [0.02, 0.06, 0.25, 0.2, 10, 0.1, 0.15, 0, 16, 0, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'fosfor': [0.12, 0.25, 0.35, 0.15, 5, 0.18, 0.45, 0, 21, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'metionin': [0.18, 0.28, 0.65, 0.27, 0.69, 1.44, 0.5, 0, 0, 0, 0, 0.05, 0.05, 0.1, 0, 99, 0, 0, 0.02, 0.035, 0.06, 0, 0, 0, 0.03],
        'sistin': [0.35, 0.45, 1.28, 0.45, 1.3, 2.35, 1.02, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'lisin': [0.25, 0.51, 2.88, 0.4, 2.6, 0.9, 0.85, 0, 0, 0, 0, 0, 0, 0, 0, 0, 99, 0, 0, 0, 0, 0, 0, 0, 0],
        'treonin': [0.29, 0.4, 1.75, 0.46, 1.8, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 98, 0, 0, 0, 0, 0, 0, 0],
        'asam_linoleat': [1.8, 1.5, 0.8, 1, 1.5, 1.2, 1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    df_bahan = pd.DataFrame(bahan_pakan_data)
    # Mengubah nama kolom agar sesuai dengan standar Python (tanpa spasi/simbol)
    df_bahan.columns = [col.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '') for col in df_bahan.columns]

    target_presets = {
        "Ayam Petelur": {"Starter": {"protein": [20.5, 20.5], "energi_kcal_kg": [2900, 2975], "serat_kasar": [3, 7], "kalsium": [1.08, 1.08], "fosfor": [0.45, 0.45], "metionin": [0.52, 0.52], "lisin": [1.16, 1.16], "treonin": [0.8, 0.8]}, "Grower": {"protein": [19, 19], "energi_kcal_kg": [2850, 2875], "serat_kasar": [3, 7], "kalsium": [1.1, 1.1], "fosfor": [0.42, 0.42], "metionin": [0.45, 0.45], "lisin": [0.98, 0.98], "treonin": [0.66, 0.66]}, "Developer": {"protein": [16.4, 16.4], "energi_kcal_kg": [2700, 2750], "serat_kasar": [3, 8], "kalsium": [1.2, 1.2], "fosfor": [0.42, 0.42], "metionin": [0.37, 0.37], "lisin": [0.77, 0.77], "treonin": [0.54, 0.54]}, "Pre-Layer": {"protein": [16.8, 16.8], "energi_kcal_kg": [2750, 2800], "serat_kasar": [5, 8], "kalsium": [2.1, 2.5], "fosfor": [0.45, 0.5], "metionin": [0.6, 0.6], "lisin": [0.81, 0.81], "treonin": [0.58, 0.58]}, "Layer 1": {"protein": [16.4, 16.4], "energi_kcal_kg": [2800, 2900], "serat_kasar": [3, 7], "kalsium": [3.39, 3.55], "fosfor": [0.55, 0.44], "metionin": [0.85, 0.85], "lisin": [0.81, 0.81], "treonin": [0.58, 0.58]}, "Layer 2": {"protein": [14.9, 14.9], "energi_kcal_kg": [2775, 2850], "serat_kasar": [7, 8], "kalsium": [3.5, 3.75], "fosfor": [0.5, 0.43], "metionin": [0.78, 0.78], "lisin": [0.81, 0.81], "treonin": [0.53, 0.53]}, "Layer 3": {"protein": [14, 14], "energi_kcal_kg": [2700, 2850], "serat_kasar": [3, 7], "kalsium": [3.58, 3.92], "fosfor": [0.5, 0.37], "metionin": [0.73, 0.73], "lisin": [0.81, 0.81], "treonin": [0.49, 0.49]}},
        "Ayam Broiler": {"Pre-Starter": {"protein": [22, 24], "energi_kcal_kg": [3000, 3200], "serat_kasar": [5, 7], "lemak": [0, 4], "kalsium": [0.9, 1.1], "fosfor": [0.45, 0.55], "metionin": [0.5, 0.55], "sistin": [0.9, 1], "lisin": [1.1, 1.25], "treonin": [0.8, 0.9]}, "Starter": {"protein": [20, 22], "energi_kcal_kg": [3100, 3200], "serat_kasar": [5, 7], "lemak": [0, 5], "kalsium": [0.8, 1], "fosfor": [0.4, 0.5], "metionin": [0.45, 0.5], "sistin": [0.85, 0.95], "lisin": [1, 1.15], "treonin": [0.7, 0.8]}, "Finisher": {"protein": [18, 20], "energi_kcal_kg": [3150, 3300], "serat_kasar": [4, 6], "lemak": [0, 6], "kalsium": [0.7, 0.9], "fosfor": [0.35, 0.45], "metionin": [0.38, 0.45], "sistin": [0.75, 0.85], "lisin": [0.9, 1.05], "treonin": [0.6, 0.7]}},
        "Itik Petelur": {"Starter & Grower": {"protein": [17, 18], "energi_kcal_kg": [2700, 2700], "serat_kasar": [7, 8], "kalsium": [0.9, 1.0], "fosfor": [0.6, 0.6], "metionin": [0.35, 0.35], "lisin": [0.7, 0.7], "treonin": [0.5, 0.5]}, "Layer": {"protein": [16, 17], "energi_kcal_kg": [2650, 2750], "serat_kasar": [7, 8], "kalsium": [2.9, 4.25], "fosfor": [0.6, 0.6], "metionin": [0.4, 0.4], "lisin": [0.7, 0.8], "treonin": [0.5, 0.5]}},
        "Puyuh Petelur": {"Starter & Grower": {"protein": [23, 24], "energi_kcal_kg": [2750, 2750], "serat_kasar": [6, 7], "kalsium": [0.8, 0.9], "fosfor": [0.6, 0.6], "metionin": [0.5, 0.5], "lisin": [1.2, 1.2], "treonin": [0.8, 0.8]}, "Layer": {"protein": [19, 20], "energi_kcal_kg": [2700, 2800], "serat_kasar": [6, 7], "kalsium": [2.5, 3.0], "fosfor": [0.6, 0.6], "metionin": [0.45, 0.45], "lisin": [1.0, 1.0], "treonin": [0.7, 0.7]}},
        "Unggas Lain": {"Buras Starter": {"protein": [18, 19], "energi_kcal_kg": [2600, 2600], "serat_kasar": [7, 7], "kalsium": [0.9, 1.2], "fosfor": [0.6, 0.6], "metionin": [0.4, 0.4], "lisin": [0.6, 0.9], "treonin": [0.6, 0.6]}, "Buras Grower": {"protein": [15, 15], "energi_kcal_kg": [2500, 2500], "serat_kasar": [7, 8], "kalsium": [0.9, 0.9], "fosfor": [0.6, 0.6], "metionin": [0.3, 0.3], "lisin": [0.5, 0.65], "treonin": [0.5, 0.5]}, "Buras Layer": {"protein": [14, 15], "energi_kcal_kg": [2600, 2700], "serat_kasar": [7, 8], "kalsium": [2.75, 4.25], "fosfor": [0.6, 0.6], "metionin": [0.35, 0.35], "lisin": [0.6, 0.7], "treonin": [0.49, 0.49]}}
    }

    usage_limits = {
        "Starter": { "Jagung": { "min": 0, "max": 60 }, "Dedak": { "min": 0, "max": 10 }, "SBM": { "min": 0, "max": 40 }, "PKM": { "min": 0, "max": 5 }, "MBM": { "min": 0, "max": 8 }, "CGM": { "min": 0, "max": 5 }, "DDGS": { "min": 0, "max": 10 }, "CPO": { "min": 0, "max": 3 }, "MCP": { "min": 0, "max": 2 }, "Garam": { "min": 0.45, "max": 0.45 }, "T.Batu": { "min": 0, "max": 5 }, "Choline C.": { "min": 0.05, "max": 0.05 }, "Citric A.": { "min": 0.05, "max": 0.05 }, "Toxin Binder": { "min": 0.1, "max": 0.1 }, "Premik": { "min": 0, "max": 0 }, "Min HC": { "min": 0, "max": 0.5 }, "ViteL": { "min": 0, "max": 0.5 }, "NeuTron": { "min": 0, "max": 0.5 }, "VITHC": { "min": 0.02, "max": 0.02 }, "EnzMix": { "min": 0.035, "max": 0.035 }, "EnzFit": { "min": 0.06, "max": 0.06 }, "Fenol": { "min": 0, "max": 0 }, "Cu": { "min": 0, "max": 0 }, "SalM": { "min": 0, "max": 0 }, "Bctr": { "min": 0.03, "max": 0.03 } },
        "Grower": { "Jagung": { "min": 0, "max": 60 }, "Dedak": { "min": 0, "max": 20 }, "SBM": { "min": 0, "max": 40 }, "PKM": { "min": 0, "max": 8 }, "MBM": { "min": 0, "max": 8 }, "CGM": { "min": 0, "max": 5 }, "DDGS": { "min": 0, "max": 10 }, "CPO": { "min": 0, "max": 3 }, "MCP": { "min": 0, "max": 2 }, "Garam": { "min": 0.45, "max": 0.45 }, "T.Batu": { "min": 0, "max": 5 }, "Choline C.": { "min": 0.1, "max": 0.1 }, "Citric A.": { "min": 0.1, "max": 0.1 }, "Toxin Binder": { "min": 0.1, "max": 0.1 }, "Premik": { "min": 0, "max": 0 }, "Min HC": { "min": 0, "max": 0.5 }, "ViteL": { "min": 0, "max": 0.5 }, "NeuTron": { "min": 0, "max": 0.5 }, "VITHC": { "min": 0.02, "max": 0.02 }, "EnzMix": { "min": 0.035, "max": 0.035 }, "EnzFit": { "min": 0.06, "max": 0.06 }, "Fenol": { "min": 0, "max": 0 }, "Cu": { "min": 0, "max": 0 }, "SalM": { "min": 0, "max": 0 }, "Bctr": { "min": 0, "max": 0 } },
        "Layer": { "Jagung": { "min": 0, "max": 60 }, "Dedak": { "min": 0, "max": 20 }, "SBM": { "min": 0, "max": 40 }, "PKM": { "min": 0, "max": 10 }, "MBM": { "min": 0, "max": 8 }, "CGM": { "min": 0, "max": 5 }, "DDGS": { "min": 0, "max": 10 }, "CPO": { "min": 0, "max": 3 }, "MCP": { "min": 0, "max": 2 }, "Garam": { "min": 0.45, "max": 0.45 }, "T.Batu": { "min": 0, "max": 15 }, "Choline C.": { "min": 0.1, "max": 0.1 }, "Citric A.": { "min": 0.1, "max": 0.1 }, "Toxin Binder": { "min": 0.1, "max": 0.1 }, "Premik": { "min": 0, "max": 0 }, "Min HC": { "min": 0, "max": 0.5 }, "ViteL": { "min": 0, "max": 0.5 }, "NeuTron": { "min": 0, "max": 0.5 }, "VITHC": { "min": 0.015, "max": 0.015 }, "EnzMix": { "min": 0, "max": 0 }, "EnzFit": { "min": 0.06, "max": 0.06 }, "Fenol": { "min": 0.015, "max": 0.015 }, "Cu": { "min": 0.02, "max": 0.02 }, "SalM": { "min": 0, "max": 0 }, "Bctr": { "min": 0, "max": 0 } }
    }
    return df_bahan, target_presets, usage_limits

# Memuat data sekali saja
df_bahan, target_presets, usage_limits = load_data()


# 4. TAMPILAN APLIKASI (USER INTERFACE)
st.title("🐔 Irsan NutriTech (Versi Streamlit)")
st.write("Menerjemahkan aplikasi formulasi ransum dari HTML ke Streamlit dengan Python.")

# Membuat dua kolom utama untuk tata letak
col1, col2 = st.columns([1, 1.5])

with col1:
    st.header("1. Pengaturan Formulasi")
    
    # Pilihan jenis unggas
    poultry_type = st.selectbox(
        "Pilih Kelompok Unggas:",
        options=list(target_presets.keys())
    )

    # Pilihan fase umur, opsinya akan berubah tergantung jenis unggas
    age_phase_options = list(target_presets[poultry_type].keys())
    age_phase = st.selectbox(
        "Pilih Standar Nutrisi (Fase):",
        options=age_phase_options
    )

    # Mengambil data target nutrisi berdasarkan pilihan pengguna
    selected_targets_raw = target_presets[poultry_type][age_phase]

    # Menentukan set batasan penggunaan bahan yang akan dipakai
    # Logika sederhana: jika fase mengandung 'starter', pakai batasan 'Starter', dst.
    limit_key = "Starter"
    if "grower" in age_phase.lower() or "developer" in age_phase.lower():
        limit_key = "Grower"
    elif "layer" in age_phase.lower() or "finisher" in age_phase.lower():
        limit_key = "Layer"
    selected_usage_limits = usage_limits[limit_key]
    
    st.info(f"Menggunakan set batasan bahan: **{limit_key}**")

    st.header("2. Target Nutrisi")
    st.write(f"Standar untuk: **{poultry_type} - {age_phase}**")

    # Formulir untuk menampung input target dan tombol hitung
    with st.form(key="nutrient_form"):
        # Membuat 2 kolom di dalam form agar lebih rapi
        form_col1, form_col2 = st.columns(2)
        
        # Dictionary untuk menyimpan input target dari pengguna
        final_targets = {}
        
        # Loop melalui semua nutrisi yang ada di preset untuk membuat input
        all_nutrient_keys = list(selected_targets_raw.keys())
        
        for i, key in enumerate(all_nutrient_keys):
            # Menentukan kolom mana yang akan digunakan (bergantian)
            current_col = form_col1 if i % 2 == 0 else form_col2
            
            # Mengambil nilai min dan max dari preset
            min_val, max_val = selected_targets_raw[key]
            
            # Membuat input rentang angka (slider)
            # Slider lebih interaktif daripada dua kotak input terpisah
            target_range = current_col.slider(
                f"Target {key.replace('_', ' ').title()} (% atau kkal/kg)",
                min_value=float(min_val * 0.8), # Beri sedikit ruang di bawah min
                max_value=float(max_val * 1.2), # Beri sedikit ruang di atas max
                value=(float(min_val), float(max_val)), # Nilai default dari preset
                step=0.01 if "kcal" not in key else 10.0 # Step yang sesuai
            )
            final_targets[key] = target_range

        # Tombol untuk mengirimkan form dan memulai kalkulasi
        calculate_button = st.form_submit_button(label="⚡ Hitung Formulasi Optimal")


# --- LOGIKA SETELAH TOMBOL DITEKAN ---
if calculate_button:
    # Memanggil fungsi inti untuk menghitung
    problem, bahan_vars = hitung_formulasi(df_bahan, final_targets, selected_usage_limits)

    # Menampilkan hasil di kolom kedua
    with col2:
        st.header("3. Hasil Formulasi")
        
        # Cek status hasil kalkulasi
        if pulp.LpStatus[problem.status] == 'Optimal':
            st.success("✅ Formulasi optimal berhasil ditemukan!")
            
            # Menampilkan total biaya
            total_biaya_per_100kg = pulp.value(problem.objective)
            st.metric(
                label="Biaya per kg Pakan",
                value=f"Rp {total_biaya_per_100kg / 100:,.2f}"
            )

            # Menyiapkan data untuk tabel hasil resep
            hasil_resep = []
            for nama_bahan, var in bahan_vars.items():
                persentase = var.varValue * 100
                if persentase > 0.001: # Hanya tampilkan bahan yang digunakan
                    hasil_resep.append({
                        "Bahan Pakan": nama_bahan,
                        "Persentase (%)": persentase
                    })
            
            df_hasil_resep = pd.DataFrame(hasil_resep).sort_values(by="Persentase (%)", ascending=False)
            st.subheader("Komposisi Ransum")
            st.dataframe(df_hasil_resep, hide_index=True, use_container_width=True)

            # Menyiapkan data untuk tabel analisis nutrisi
            st.subheader("Analisis Nutrisi Hasil Formulasi")
            hasil_nutrisi = []
            for key, (min_target, max_target) in final_targets.items():
                # Hitung nilai nutrisi aktual dari resep
                nilai_aktual = sum(bahan_vars[bahan['nama']].varValue * bahan[key] for _, bahan in df_bahan.iterrows())
                
                # Cek status (terpenuhi atau tidak)
                status = "✅"
                if nilai_aktual < min_target:
                    status = "🔻 Rendah"
                elif nilai_aktual > max_target:
                    status = "🔺 Tinggi"

                hasil_nutrisi.append({
                    "Nutrisi": key.replace('_', ' ').title(),
                    "Hasil Formulasi": f"{nilai_aktual:.2f}",
                    "Target": f"{min_target:.2f} - {max_target:.2f}",
                    "Status": status
                })
            
            df_hasil_nutrisi = pd.DataFrame(hasil_nutrisi)
            st.dataframe(df_hasil_nutrisi, hide_index=True, use_container_width=True)

        else:
            # Jika formulasi tidak ditemukan
            st.error(f"❌ Formulasi tidak dapat ditemukan. Status: {pulp.LpStatus[problem.status]}")
            st.warning("Coba periksa kembali batasan penggunaan bahan atau longgarkan sedikit target nutrisi Anda.")

# Tampilkan database bahan baku di kolom kedua sebagai referensi
with col2:
    with st.expander("Lihat Database Bahan Pakan", expanded=False):
        st.dataframe(df_bahan, use_container_width=True)

