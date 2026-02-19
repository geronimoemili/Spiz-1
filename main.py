import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

# Import moduli interni
try:
    from api.ingestion import process_csv
    from services.database import supabase
    from api.chat import ask_spiz
except ImportError as e:
    print(f"❌ ERRORE IMPORTAZIONE: {e}")
    print("Assicurati che le cartelle api/ e services/ contengano i file .py")

app = FastAPI(title="SPIZ Intelligence Dashboard")

# --- CONFIGURAZIONE AMBIENTE ---
# Crea le cartelle necessarie se non esistono
os.makedirs("data/raw", exist_ok=True)
os.makedirs("web", exist_ok=True)

# Monta la cartella static se hai file CSS/JS esterni (opzionale)
# app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    question: str

# --- ROTTE NAVIGAZIONE ---

@app.get("/")
async def index():
    """Pagina principale della Dashboard"""
    return FileResponse('web/index.html')

@app.get("/clienti")
async def clienti_page():
    """Pagina gestione keywords clienti"""
    return FileResponse('web/clienti.html')

# --- API CORE ---

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Gestisce il caricamento del CSV e l'ingestion su Supabase"""
    try:
        print(f"📂 Ricevuto file: {file.filename}")
        path = f"data/raw/{file.filename}"
        
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Elaborazione tramite il modulo dedicato
        result = process_csv(path)
        
        # Pulizia file temporaneo
        if os.path.exists(path):
            os.remove(path)
            
        return result
    except Exception as e:
        print(f"❌ Errore in Upload: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Interfaccia con l'AI (ask_spiz)"""
    try:
        print(f"💬 Domanda ricevuta: {req.question}")
        answer = ask_spiz(req.question)
        return {"answer": answer}
    except Exception as e:
        print(f"❌ Errore AI: {e}")
        return {"answer": f"Sistemi in sovraccarico. Dettaglio: {str(e)}"}

# --- API GESTIONE CLIENTI & MENTION ---

@app.get("/api/get-clients")
async def get_clients():
    res = supabase.table("clients").select("*").order("name").execute()
    return res.data

@app.post("/api/add-client")
async def add_client(data: dict):
    # Esempio data: {"name": "Snam", "keywords": "idrogeno, metano, rete"}
    res = supabase.table("clients").insert(data).execute()
    return {"status": "success"}

@app.delete("/api/delete-client/{client_id}")
async def delete_client(client_id: str):
    supabase.table("clients").delete().eq("id", client_id).execute()
    return {"status": "success"}

@app.get("/api/today-mentions")
async def get_today_mentions():
    """Calcola le menzioni basate sulle keyword dei clienti caricate"""
    try:
        from datetime import date
        today = date.today().isoformat()
        
        # Recupero dati da Supabase
        clients = supabase.table("clients").select("*").execute().data
        articles = supabase.table("articles").eq("data", today).execute().data
        
        results = []
        if clients and articles:
            for client in clients:
                keywords = [k.strip().lower() for k in (client.get('keywords') or "").split(',')]
                count = 0
                for art in articles:
                    # Cerca nel titolo e nel testo
                    text_to_scan = f"{art.get('titolo', '')} {art.get('testo_completo', '')}".lower()
                    if any(kw in text_to_scan for kw in keywords if kw):
                        count += 1
                if count > 0:
                    results.append({"name": client['name'], "mentions": count})
        
        return {"client_mentions": results}
    except Exception as e:
        print(f"⚠️ Errore menzioni: {e}")
        return {"client_mentions": []}

# --- AVVIO ---

if __name__ == "__main__":
    # Uvicorn è il server che Replit preferisce per FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)