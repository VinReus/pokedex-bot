import os
from flask import Flask, request
import requests

app = Flask(__name__)

# --- CONFIGURAZIONI SICURE ---
# I token vengono letti in automatico dalle variabili di Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Render ci fornisce automaticamente l'URL pubblico del nostro bot!
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 
WEBHOOK_URL = f"{RENDER_URL}/webhook"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
HF_API_URL = "https://api-inference.huggingface.co/models/imjeffhi/pokemon_classifier"

@app.route('/')
def home():
    return "Il Bot Pokédex è online su Render! 🤖🐾"

def invia_messaggio(chat_id, testo):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def ottieni_url_file(file_id):
    url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
    risposta = requests.get(url).json()
    if risposta.get("ok"):
        file_path = risposta["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    return None

def analizza_pokemon(image_bytes):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                pokemon_nome = result[0]['label']
                sicurezza = round(result[0]['score'] * 100, 1)
                return f"È un **{pokemon_nome.capitalize()}**! (Sicurezza: {sicurezza}%)"
        return f"Sensore disturbato: codice errore {response.status_code}"
    except requests.exceptions.Timeout:
        return "Tempo scaduto! Il server AI sta impiegando troppo tempo."
    except Exception as e:
        return f"Errore di connessione con l'AI: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and "message" in update and "photo" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        invia_messaggio(chat_id, "Sto analizzando l'immagine nel Pokédex... 🔍")
        
        foto = update["message"]["photo"][-1]
        file_id = foto["file_id"]
        
        file_url = ottieni_url_file(file_id)
        if file_url:
            img_data = requests.get(file_url).content
            risposta = analizza_pokemon(img_data)
            invia_messaggio(chat_id, risposta)
            
    return "OK", 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    url = f"{TELEGRAM_API_URL}/setWebhook?url={WEBHOOK_URL}"
    risposta = requests.get(url)
    return risposta.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
  
