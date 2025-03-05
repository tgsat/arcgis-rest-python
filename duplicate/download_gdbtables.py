import os
import requests
import time
import configs

# 🔄 Fungsi buat bikin token baru kalau kedaluwarsa
def get_token(username, password, token_url):
    params = {
        "username": username,
        "password": password,
        "client": "referer",  # Ganti 'requestip' jadi 'referer'
        "referer": configs.REFERER,
        "f": "json",
        "expiration": 30
    }
    response = requests.post(token_url, data=params)
    if response.status_code == 200 and "token" in response.json():
        print("✅ Token berhasil diperbarui.")
        return response.json()["token"]
    else:
        print("❌ Gagal mendapatkan token:", response.text)
        return None


def create_replica(service_url, username, password, token_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    token = get_token(username, password, token_url)
    if not token:
        print("❌ Gagal mendapatkan token awal.")
        return

    replica_url = f"{service_url}/createReplica"
    params = {
        "f": "json",
        "replicaName": "Lampung_Replica",
        "layers": "9",  # Nomor layer, ganti sesuai kebutuhan
        "returnAttachments": "false",
        "returnAttachmentsDatabyURL": "false",
        "async": "true",
        "syncModel": "none",
        "dataFormat": "filegdb",
        "transportType": "esriTransportTypeUrl",
        "token": token
    }

    print("Mengakses URL:", replica_url)
    print("Dengan parameter:", params)

    # Buat replika
    response = requests.post(replica_url, data=params)
    if response.status_code != 200:
        print("❌ Gagal membuat replika:", response.status_code)
        print("Detail error:", response.text)
        return

    # Cek status async (karena pakai async true)
    status_url = response.json().get("statusUrl")
    if not status_url:
        print("❌ Gagal mendapatkan URL status:", response.json())
        return

    print("URL status ditemukan:", status_url)

    # Cek status hingga selesai
    while True:
        status_response = requests.get(status_url, params={"token": token, "f": "json"})
        status_data = status_response.json()
        if status_data.get("status") == "Completed":
            print("✅ Replika selesai dibuat!")
            replica_url = status_data.get("resultUrl")
            break
        elif status_data.get("status") == "Failed":
            print("❌ Gagal membuat replika:", status_data)
            return
        else:
            print("⏳ Menunggu replika selesai... (5 detik)")

            # 🔄 Cek kalau token kedaluwarsa
            if "Invalid Token" in status_response.text or status_response.status_code == 498:
                print("⚠️ Token invalid atau kedaluwarsa, memperbarui token...")
                token = get_token(username, password, token_url)
                if not token:
                    print("❌ Gagal memperbarui token.")
                    return

            time.sleep(5)

    # Download file .gdb.zip
    print("Link download ditemukan:", replica_url)
    zip_output = os.path.join(output_dir, f"{AttachmentFile}.gdb.zip")
    download_response = requests.get(replica_url, stream=True)
    with open(zip_output, "wb") as f:
        for chunk in download_response.iter_content(1024):
            f.write(chunk)

    print(f"✅ Berhasil mengunduh data: {zip_output}")


# 🛠️ Ganti ini sesuai URL layer, token URL, dan kredensial
service_url = configs.FEATURE_LAYER_URL
token_url = configs.TOKEN_URL
username = configs.GIS_USERNAME
password = configs.GIS_PASSWORD
output_dir = configs.SAVE_FOLDER
AttachmentFile = configs.OUTPUT_FILE

create_replica(service_url, username, password, token_url, output_dir)
