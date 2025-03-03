import os
import re
import config

# Path folder foto
photo_dir = config.SAVE_FOLDER

# Dapatkan daftar file di folder
files = os.listdir(photo_dir)

# Pola regex untuk globalid dan bagian _foto
pattern = re.compile(r'^([0-9a-fA-F-]+)_foto(.*\.jpg)$')

# Loop setiap file
for file in files:
    match = pattern.match(file)
    if match:
        globalid = match.group(1)
        sisa_nama = match.group(2)  # Bagian setelah _foto (termasuk _1, _2, dst)
        
        # Buat nama file baru dengan {} dan sisa nama
        new_name = f"{{{globalid}}}{sisa_nama}"
        
        # Path lama dan baru
        old_path = os.path.join(photo_dir, file)
        new_path = os.path.join(photo_dir, new_name)
        
        # Ganti nama file
        os.rename(old_path, new_path)
        print(f"Renamed: {file} ➡️ {new_name}")
    else:
        print(f"Skipped: {file}")
