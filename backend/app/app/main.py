from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import logging

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- VirusTotal API ---
API_KEY = "4f2c92dbc66e56c87a9c4e7b7f56a68ea5680d5c17953f87ac2a44c35111762c"
HEADERS = {"x-apikey": API_KEY}
VT_URL_SUBMIT = "https://www.virustotal.com/api/v3/urls"
VT_REPORT = "https://www.virustotal.com/api/v3/urls/{}"
TIMEOUT = 5  # секунд

app = FastAPI()

# --- CORS для расширения ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Вспомогательные функции ---

def url_to_id(url: str) -> str:
    """Преобразует URL в base64-id для VirusTotal"""
    url_bytes = url.encode("utf-8")
    return base64.urlsafe_b64encode(url_bytes).decode("utf-8").strip("=")


def get_verdict(stats: dict) -> str:
    """На основе статистики VT определяет статус"""
    if stats["malicious"] > 0:
        return "malicious"
    elif stats["suspicious"] > 0:
        return "suspicious"
    elif stats["harmless"] > 0 and stats["malicious"] == 0:
        return "clean"
    else:
        return "unknown"


# --- Основной эндпоинт ---
@app.post("/api/check")
async def check_site(request: Request):
    try:
        data = await request.json()
        input_value = data.get("url")
        if not input_value:
            return {"error": "Не передан параметр 'url'"}

        logging.info(f"[INCOMING] URL received: {input_value}")  # 🟢 лог входящего запроса

        # Определение ID
        if input_value.startswith("http://") or input_value.startswith("https://"):
            vt_id = url_to_id(input_value)
        elif "." in input_value and "/" not in input_value:
            vt_id = url_to_id("http://" + input_value)
        elif len(input_value) > 30 and "_" not in input_value:
            vt_id = input_value
        else:
            return {"error": "Не удалось определить тип данных"}

        # Пытаемся получить отчет
        try:
            resp = requests.get(VT_REPORT.format(vt_id), headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                report = resp.json()
                stats = report["data"]["attributes"]["last_analysis_stats"]
                verdict = get_verdict(stats)
                logging.info(f"[RESULT] verdict for {input_value}: {verdict}")
                return {"status": verdict}
            else:
                logging.warning(f"[VT] Report error {resp.status_code} for {input_value}")
        except requests.exceptions.RequestException as e:
            logging.error(f"[VT] Report exception: {e}")
            return {"error": "VirusTotal недоступен (report)", "detail": str(e)}

        # Пытаемся отправить URL на анализ
        try:
            resp = requests.post(VT_URL_SUBMIT, headers=HEADERS, data={"url": input_value}, timeout=TIMEOUT)
            if resp.status_code == 200:
                logging.info(f"[VT] Submitted URL for scanning: {input_value}")
                return {"status": "pending"}
            else:
                logging.warning(f"[VT] Submit error {resp.status_code} for {input_value}")
                return {
                    "error": "Ошибка при отправке URL на анализ",
                    "status_code": resp.status_code,
                }
        except requests.exceptions.RequestException as e:
            logging.error(f"[VT] Submit exception: {e}")
            return {"error": "VirusTotal недоступен (submit)", "detail": str(e)}

    except Exception as e:
        logging.exception(f"[SERVER] Непредвиденная ошибка: {e}")
        return {"error": "Внутренняя ошибка сервера", "detail": str(e)}