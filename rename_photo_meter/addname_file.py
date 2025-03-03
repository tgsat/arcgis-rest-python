import os
import imghdr

# Ganti dengan path folder tempat gambar berada
folder_path = "/media/satrio/USBData/zRUMAH"

# Keterangan yang ingin ditambahkan di depan nama file
prefix = "Rumah_"

# Loop melalui semua file di folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    
    # Periksa apakah file adalah gambar
    if imghdr.what(file_path):  # Memeriksa tipe file gambar
        new_filename = prefix + filename  # Tambahkan prefix di depan nama file
        new_path = os.path.join(folder_path, new_filename)
        
        os.rename(file_path, new_path)  # Ubah nama file

print("Rename selesai!")
