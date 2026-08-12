import os
from flask import Flask, request
import requests
from huggingface_hub import InferenceClient

app = Flask(__name__)

# --- I TOKEN SONO NASCOSTI E AL SICURO SU RENDER ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 
WEBHOOK_URL = f"{RENDER_URL}/webhook"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

hf_client = InferenceClient(token=HF_TOKEN)

@app.route('/')
def home():
    return "Il Bot Pokédex è online su Render! 🤖🐾"

def invia_messaggio(chat_id, testo):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "HTML"}
    r = requests.post(url, json=payload)
    print(f"-> Status invio Telegram: {r.status_code}")

def ottieni_url_file(file_id):
    url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
    risposta = requests.get(url).json()
    if risposta.get("ok"):
        file_path = risposta["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    return None

def analizza_pokemon(image_bytes):
    try:
                # Usiamo un modello ufficiale di Google per testare la connessione
        result = hf_client.image_classification(
            image=image_bytes, 
            model="google/vit-base-patch16-224"
        )
        print(f"-> Dati ricevuti dall'AI: {result}")
        if result and len(result) > 0:
            try:
                pokemon_nome = result[0].label
                sicurezza = round(result[0].score * 100, 1)
            except AttributeError:
                pokemon_nome = result[0]['label']
                sicurezza = round(result[0]['score'] * 100, 1)
                
            return f"È un <b>{pokemon_nome.capitalize()}</b>! (Sicurezza: {sicurezza}%)"
            
        return "Sensore disturbato. Non sono riuscito a identificare il Pokémon."
    except Exception as e:
        print(f"-> Errore di connessione AI: {e}")
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
    
