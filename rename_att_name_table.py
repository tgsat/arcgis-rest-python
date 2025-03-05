import os
import re
import config
import pandas as pd

# 📌 Fungsi untuk rename kolom att_name di CSV
def rename_att_name_in_csv(csv_file_path):
    # Cek apakah file CSV ada
    if not os.path.exists(csv_file_path):
        print(f"❌ File CSV {csv_file_path} tidak ditemukan.")
        return

    # Baca CSV
    df = pd.read_csv(csv_file_path)

    # Cek apakah kolom att_name ada
    if 'att_name' not in df.columns:
        print("❌ Kolom 'att_name' tidak ditemukan dalam CSV.")
        return

    # Pola regex untuk mengganti nama
    pattern = re.compile(r'^([0-9a-fA-F-]+)_foto(.*\.jpg)$')

    # Fungsi untuk mengubah nama
    def rename_att_name(att_name):
        match = pattern.match(att_name)
        if match:
            globalid = match.group(1)
            sisa_nama = match.group(2)
            # Format baru dengan kurung kurawal
            return f"{{{globalid}}}{sisa_nama}"
        return att_name  # Jika tidak cocok, biarkan seperti semula

    # Terapkan perubahan ke kolom att_name
    df['att_name'] = df['att_name'].apply(rename_att_name)

    # Simpan kembali CSV
    df.to_csv(csv_file_path, index=False)
    print(f"✅ Berhasil mengubah nama di kolom 'att_name' pada CSV {csv_file_path}.")

# 📌 Panggil fungsi setelah semua proses selesai
csv_file_path = f"{config.SAVE_FOLDER2}/{config.OUTPUT_CSV}"
rename_att_name_in_csv(csv_file_path)
