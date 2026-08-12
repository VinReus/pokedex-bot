import os
from flask import Flask, request
import requests

app = Flask(__name__)

# --- TOKEN ---
TELEGRAM_TOKEN = "8797428568:AAFZ98i1zkPvxedkGuBf1edq1t-X6Qw_jRw"
HF_TOKEN = "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"

RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 
WEBHOOK_URL = f"{RENDER_URL}/webhook"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
HF_API_URL = "https://api-inference.huggingface.co/models/imjeffhi/pokemon_classifier"

@app.route('/')
def home():
    return "Il Bot Pokédex è online su Render! 🤖🐾"

def invia_messaggio(chat_id, testo):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    # Modificato in HTML per evitare crash di Telegram con gli asterischi!
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "HTML"}
    r = requests.post(url, json=payload)
    # Questo ci farà vedere nei log se Telegram rifiuta il messaggio
    print(f"-> Status invio Telegram: {r.status_code} - Dettagli: {r.text}")

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
        print("-> Inviando la foto all'Intelligenza Artificiale...")
        # Aumentato il tempo di attesa interno
        response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=60)
        print(f"-> Risposta AI (Codice): {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"-> Dati ricevuti dall'AI: {result}")
            if isinstance(result, list) and len(result) > 0:
                pokemon_nome = result[0]['label']
                sicurezza = round(result[0]['score'] * 100, 1)
                # Usiamo <b> invece di ** per il grassetto
                return f"È un <b>{pokemon_nome.capitalize()}</b>! (Sicurezza: {sicurezza}%)"
                
        return f"Sensore disturbato. L'AI ha risposto: {response.text}"
    except Exception as e:
        print(f"-> Errore di connessione: {e}")
        return f"Errore di comunicazione con l'Intelligenza Artificiale."

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and "message" in update and "photo" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        print(f"-> Nuova foto ricevuta! Chat ID: {chat_id}")
        
        invia_messaggio(chat_id, "Sto analizzando l'immagine nel Pokédex... 🔍")
        
        foto = update["message"]["photo"][-1]
        file_url = ottieni_url_file(foto["file_id"])
        
        if file_url:
            img_data = requests.get(file_url).content
            risposta = analizza_pokemon(img_data)
            invia_messaggio(chat_id, risposta)
            
    return "OK", 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    if not RENDER_URL:
        return "Attendere: URL non ancora pronto."
    url = f"{TELEGRAM_API_URL}/setWebhook?url={WEBHOOK_URL}"
    risposta = requests.get(url)
    return risposta.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
