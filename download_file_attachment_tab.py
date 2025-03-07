from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import os
import time
import requests
import config
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


# 🔹 Muat variabel dari file .env
config.load_dotenv()

# 🔹 Ambil kredensial dari config
username = config.GIS_USERNAME
password = config.GIS_PASSWORD
feature_layer_url = config.FEATURE_LAYER_URL
save_folder = config.SAVE_FOLDER
save_folder_offset = config.LOCAL_FOLDER
jatahmu = config.RECORD_COUNT
attachment_file = os.path.join(save_folder, "attachment.tab")
offset_file = os.path.join(save_folder_offset, "offset.txt")  # ⬅️ File untuk menyimpan offset terakhir

# 🔹 Pastikan folder penyimpanan tersedia
os.makedirs(save_folder, exist_ok=True)
os.makedirs(save_folder_offset, exist_ok=True)

# 🔹 Token Management
TOKEN_EXPIRY = 50 * 60  # 50 menit

def get_token():
    params = {"username": username, "password": password, "referer": "https://www.arcgis.com", "f": "json"}
    response = requests.post(config.TOKEN_URL, data=params)
    data = response.json()
    if "token" in data:
        print(f"🔑 Token diperbarui: {data['token'][:10]}...")
        return data["token"], time.time() + TOKEN_EXPIRY
    raise Exception("Gagal mendapatkan token")

token, token_expires = get_token()

# 🔹 Inisialisasi GIS & Layer
gis = GIS("https://www.arcgis.com", token=token)
layer = FeatureLayer(feature_layer_url, gis)

# 🔹 Baca last_objectid dari file offset
def get_last_objectid():
    if os.path.exists(offset_file):
        with open(offset_file, "r") as f:
            return int(f.read().strip())
    return 0  # Jika tidak ada file, mulai dari 0

# 🔹 Simpan last_objectid ke file offset
def save_last_objectid(objectid):
    with open(offset_file, "w") as f:
        f.write(str(objectid))

def save_attachment_metadata(data):
    file_exists = os.path.exists(attachment_file)
    
    with open(attachment_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        if not file_exists:
            writer.writerow(["attachment_id", "globalid", "content_type", "att_name"])  # Hapus parent_globalid dari header
        writer.writerows(data)

# 🔹 Fungsi unduhan menggunakan ThreadPoolExecutor
def download_attachment(object_id, globalid, attachment, suffix):
    attachment_id = attachment["id"]
    content_type = attachment["contentType"]
    original_name = attachment["name"]
    
    file_name = f"{globalid}_foto_{suffix}.jpg"
    file_path = os.path.join(save_folder, file_name)

    if os.path.exists(file_path):
        print(f"⏭️ Skip: {file_name} sudah ada.")
        return attachment_id, content_type, file_name  # Skip jika sudah ada

    try:
        response = layer.attachments.download(object_id, attachment_id, save_folder)
        if response and os.path.exists(os.path.join(save_folder, original_name)):
            os.rename(os.path.join(save_folder, original_name), file_path)
            print(f"✅ Berhasil: {file_name}")
            return attachment_id, content_type, file_name
        else:
            print(f"⚠️ Tidak ditemukan: {original_name}")
    except Exception as e:
        print(f"❌ Gagal mengunduh {file_name}: {e}")
    return attachment_id, content_type, None

# 🔹 Loop utama untuk fetching & downloading
last_objectid = get_last_objectid()
metadata_records = []
download_tasks = defaultdict(list)

while True:
    try:
        if time.time() > token_expires:
            print("🔄 Memperbarui token...")
            token, token_expires = get_token()
            gis = GIS("https://www.arcgis.com", token=token)
            layer = FeatureLayer(feature_layer_url, gis)

        print(f"🔄 Mengambil data dari OBJECTID >= {last_objectid}...")

        features = layer.query(
            where=f"OBJECTID >= {last_objectid}",
            out_fields="*",
            return_attachments=True,
            order_by_fields="OBJECTID ASC",
            result_record_count=jatahmu
        )

        if not features.features:
            print("🎉 Semua attachments berhasil diunduh!")
            break

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            
            for feature in features:
                object_id = feature.attributes["OBJECTID"]
                globalid = feature.attributes.get("GLOBALID") or feature.attributes.get("GlobalID") or "UNKNOWN"

                print(f"📷 ObjectID {object_id} - GlobalID: {globalid}")

                attachments = layer.attachments.get_list(object_id)

                print(f"📷 ObjectID {object_id} punya {len(attachments)} lampiran.")

                for i, attachment in enumerate(attachments):
                    suffix = i + 1
                    futures[executor.submit(download_attachment, object_id, globalid, attachment, suffix)] = (
                        object_id, globalid, attachment["id"]
                    )

            for future in as_completed(futures):
                object_id, globalid, attachment_id = futures[future]
                try:
                    attachment_id, content_type, file_name = future.result()
                    if file_name:
                        metadata_records.append([attachment_id, globalid, content_type, file_name])
                        save_last_objectid(object_id)  # ⬅️ Simpan last_objectid setelah sukses
                    else:
                        print(f"❌ Gagal mengunduh attachment {attachment_id}")
                except Exception as e:
                    print(f"❌ Error pada attachment {attachment_id}: {e}")

        # Simpan metadata setiap batch
        if metadata_records:
            save_attachment_metadata(metadata_records)
            metadata_records = []

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)

# Pastikan metadata terakhir tersimpan
if metadata_records:
    save_attachment_metadata(metadata_records)
