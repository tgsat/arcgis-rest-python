from dotenv import load_dotenv
import os

# NOte :
# GIS_LOCAL_ICON_PJA
# App = 8
# TIANG = 13
# TRAFOGD = 14

# LAMPUNG_gdb
# 0 = TRAFO
# 1 = TIANGTR
# 2 = APP

TOKEN_URL = "https://www.arcgis.com/sharing/rest/generateToken"
REFERER =  "https://petirindojayaabd.maps.arcgis.com"
LOADENV = load_dotenv("/home/satrio/Documents/Coding/ARCGIS/.env")

GIS_USERNAME = os.getenv("ARC_USERNAME")
GIS_PASSWORD = os.getenv("ARC_PASSWORD")
LOCAL_FOLDER = "/home/satrio/Documents/Coding/ARCGIS/cache"


FOLDER_NAME = "LAMPUNG"
SUBFOLDER_NAME = "TIANGTR"
DATA_FORMAT = "gdb"
OUTPUT_FILE_CSV = f"attachment_data_{SUBFOLDER_NAME}"
OUTPUT_CSV = f"{OUTPUT_FILE_CSV.lower()}.csv"


#==================== Jika anda ingin mengubah url jangan lupa pastikan id perusahaan, feature services dan layer id disesuakan terlebih dahulu =========================#
COMPANYID = os.getenv("COMPANYID")
SAVE_FOLDER = f"/media/satrio/TOSHIBA/NEW/{FOLDER_NAME}/{SUBFOLDER_NAME}" #Sesuaikan dengan layer yang ingin di unduh
SAVE_FOLDER2 = f"/media/satrio/TOSHIBA/NEW/{FOLDER_NAME}" #Sesuaikan dengan layer yang ingin di unduh
FEATURE_LAYER_URL = f"https://services6.arcgis.com/{COMPANYID}/arcgis/rest/services/{FOLDER_NAME}_gdb/FeatureServer" #Ubah ID akhir untuk memilih layer