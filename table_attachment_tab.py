import os
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
import subprocess
import sys
import threading


TOKEN_EXPIRY = 50 * 60  # 50 menit

save_folder_offset = config.LOCAL_FOLDER
offset_file = os.path.join(save_folder_offset, "offset.txt")

config.LOADENV
print("Variabel dari file .env berhasil dimuat.")

username = config.GIS_USERNAME
password = config.GIS_PASSWORD

if not username or not password:
    print("Username atau password tidak ditemukan dalam file .env")
    exit(1)

lock = threading.Lock()  # 🔒 Lock untuk penguncian akses ke offset.txt

# 🔄 Cek dan buat offset.txt jika belum ada
if not os.path.exists(offset_file):
    os.makedirs(save_folder_offset, exist_ok=True)  # Buat folder jika belum ada
    with open(offset_file, "w") as f:
        f.write("0")
    print(f"📂 offset.txt dibuat dengan nilai awal 0 di lokasi: {os.path.abspath(offset_file)}")
else:
    print(f"📂 offset.txt ditemukan di lokasi: {os.path.abspath(offset_file)}")


def get_token():
    token_url = config.TOKEN_URL
    token_params = {
        "username": username,
        "password": password,
        "referer": config.REFERER,
        "f": "json"
    }
    try:
        token_response = requests.post(token_url, data=token_params)
        if token_response.status_code == 200:
            token_data = token_response.json()
            print("🔑 Token berhasil didapatkan.")
            return token_data.get('token')
        else:
            print(f"Error mendapatkan token: {token_response.status_code}")
    except Exception as e:
        print(f"Exception saat mendapatkan token: {e}")
    return None

def is_skipped(attachment_id, csv_file_path):
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path, usecols=["attachment_id"])
        if attachment_id in df['attachment_id'].values:
            print(f"⏭️ Skip: Attachment ID {attachment_id} sudah ada.")
            return True
    return False

def save_last_objectid(objectid):
    """Simpan last_objectid ke file offset.txt dengan mode 'w' untuk overwrite"""
    try:
        with lock:  # 🔒 Menggunakan lock saat menulis file
            with open(offset_file, "w") as f:
                f.write(str(objectid))
        print(f"✅ Last OBJECTID diperbarui: {objectid}")
    except Exception as e:
        print(f"❌ Gagal menyimpan last_objectid: {e}")

def save_attachment_data(attachment_info, csv_file_path, object_id):
    df = pd.DataFrame([attachment_info])
    df.to_csv(csv_file_path, mode='a', header=not os.path.exists(csv_file_path), index=False)
    print(f"✅ Berhasil Disimpan: Data attachment {attachment_info['attachment_id']}.")

    # 🔄 Perbarui offset.txt setelah data attachment berhasil disimpan
    save_last_objectid(object_id)  # Gunakan object_id (integer) untuk offset.txt

def get_last_objectid():
    if os.path.exists(offset_file):
        try:
            with open(offset_file, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    last_id = int(content)
                    print(f"🔄 Last OBJECTID ditemukan: {last_id}")
                    return last_id
        except Exception as e:
            print(f"❌ Gagal membaca offset.txt: {e}")
    print("📂 offset.txt tidak ditemukan atau kosong. Menggunakan OBJECTID = 0")
    return 0

def get_attachments(layer_url, object_id, token, csv_file_path):
    attachment_url = f"{layer_url}/{object_id}/attachments"
    params = {"f": "json", "token": token}

    try:
        response = requests.get(attachment_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'attachmentInfos' in data:
                print(f"Attachments ditemukan untuk OBJECTID: {object_id}")
                
                for attachment in data['attachmentInfos']:
                    attachment_id = int(attachment.get("id"))

                    if is_skipped(attachment_id, csv_file_path):
                        continue

                    parent_globalid = attachment.get("parentGlobalId")
                    att_name = attachment.get("name")

                    if att_name:
                        photo_count = data['attachmentInfos'].index(attachment) + 1
                        att_name = f"{parent_globalid}_foto_{photo_count}.jpg"
                    else:
                        att_name = ""

                    attachment_info = {
                        "attachment_id": attachment_id,
                        "globalid": attachment.get("globalId"),
                        "parent_globalid": parent_globalid,
                        "content_type": attachment.get("contentType"),
                        "att_name": att_name,
                        "data_size": attachment.get("size"),
                        "size": attachment.get("size")
                    }

                    # 🔄 Berikan object_id ke save_attachment_data
                    save_attachment_data(attachment_info, csv_file_path, object_id)
            else:
                print(f"Tidak ada attachment untuk OBJECTID: {object_id}")
        else:
            print(f"Gagal mendapatkan attachments untuk OBJECTID : {object_id}, Error code : {response.status_code}")
    except Exception as e:
        print(f"Error saat mengambil attachments: {e}")

def download_attachments(object_ids, layer_url, token, csv_file_path):
    if not object_ids:
        print("⚠️ Tidak ada OBJECTID untuk diproses.")
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(get_attachments, layer_url, object_id, token, csv_file_path): object_id
            for object_id in object_ids
        }

        for future in as_completed(futures):
            object_id = futures[future]
            try:
                future.result()
                print(f"Info: Attachment untuk OBJECTID {object_id} selesai diproses.")
                
                # 🔄 Perbarui offset.txt setelah semua attachment untuk OBJECTID ini selesai
                save_last_objectid(object_id)  # ⬅️ Pindahkan perintah ini ke sini
                
            except Exception as e:
                print(f"Error saat memproses OBJECTID {object_id}: {e}")

layer_url = config.FEATURE_LAYER_URL
last_objectid = get_last_objectid()

token = get_token()
if not token:
    print("Gagal Mendapatkan token atau periksa koneksi anda.")
    exit(1)

csv_file_path = f"{config.SAVE_FOLDER2}/{config.OUTPUT_CSV}"

def get_object_ids(layer_url, token, last_objectid):
    query_url = f"{layer_url}/query"
    params = {
        "where": f"OBJECTID >= {last_objectid}",
        "outFields": "OBJECTID",
        "f": "json",
        "token": token
    }

    try:
        response = requests.get(query_url, params=params)
        if response.status_code == 200:
            data = response.json()
            object_ids = [int(feature['attributes']['OBJECTID']) for feature in data.get('features', [])]
            print(f"Object IDs berhasil didapatkan: {len(object_ids)} item.")
            return object_ids
        else:
            print(f"Error mendapatkan object IDs: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    return []

object_ids = get_object_ids(layer_url, token, last_objectid)

if object_ids:
    download_attachments(object_ids, layer_url, token, csv_file_path)
else:
    print("Tidak ada object_id yang ditemukan.")
