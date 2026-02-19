import pandas as pd
from services.database import supabase
import datetime

def process_csv(file_path):
    try:
        # Caricamento flessibile del CSV
        try:
            df = pd.read_csv(file_path, sep=None, engine='python')
        except:
            df = pd.read_csv(file_path)
        
        # Pulizia nomi colonne CSV (togliamo spazi e minuscole)
        df.columns = [c.strip().lower() for c in df.columns]
        
        print(f"--- DEBUG: Colonne CSV rilevate: {df.columns.tolist()} ---")

        records = []
        for _, row in df.iterrows():
            # Estraiamo l'autore dal CSV (colonna 'autore')
            # Se la colonna non esiste, mettiamo 'N.D.'
            valore_autore = row.get('autore') if 'autore' in df.columns else "Autore non indicato"
            
            # Prepariamo il record per Supabase usando i nomi COLONNA del DB
            record = {
                "titolo": str(row.get('titolo', "Senza Titolo")),
                "testata": str(row.get('testata', "N.D.")),
                "data": str(row.get('data', datetime.date.today().isoformat())),
                
                # QUI IL FIX: Mappiamo 'autore' (CSV) su 'giornalista' (DB)
                "giornalista": str(valore_autore) if pd.notna(valore_autore) else "N.D.",
                
                "testo_completo": str(row.get('testo_completo', row.get('testo', ""))),
                "occhiello": str(row.get('occhiello', "")),
                "sottotitolo": str(row.get('sottotitolo', "")),
                "ave": float(row.get('ave', 0)) if pd.notna(row.get('ave')) else 0,
                "tone": "Neutral",
                "reputational_risk": "None"
            }
            records.append(record)

        if records:
            # Inserimento nel database
            supabase.table("articles").insert(records).execute()
            return {"status": "success", "message": f"Caricati {len(records)} articoli. Giornalisti mappati correttamente!"}
        
        return {"status": "error", "message": "CSV vuoto."}

    except Exception as e:
        print(f"ERRORE INGESTION: {str(e)}")
        return {"status": "error", "message": str(e)}