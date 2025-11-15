# app/config.py
import os

# MCP widget için
MIME_TYPE = "text/html+skybridge"

# Dışarıdan erişilen asıl HTTPS adresin
# PROD'da bunu mutlaka env'den al:
#   BASE_URL = os.getenv("BASE_URL", "https://obasemarket.azurewebsites.net")
BASE_URL = os.getenv("BASE_URL", "https://obasemarket.azurewebsites.net")

# OAuth "resource" olarak kullanılacak canonical identifier
RESOURCE_ID = BASE_URL  # genelde aynısı
