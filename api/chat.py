import openai
from services.database import supabase

def ask_spiz(question):
    # 1. Recupero massiccio (100 articoli) per trovare correlazioni nascoste
    res = supabase.table("articles").select("*").order("data", desc=True).limit(100).execute()
    articles = res.data

    if not articles:
        return "Database vuoto. Carica i dati per attivare l'analisi."

    # 2. Prepariamo i dati includendo esplicitamente GIORNALISTA e AVE
    ctx = ""
    for a in articles:
        ctx += f"DATA: {a['data']} | TESTATA: {a['testata']} | FIRMA: {a.get('giornalista','N.D.')}\n"
        ctx += f"TITOLO: {a['titolo']} | AVE: {a.get('ave', 0)} | TONO: {a.get('tone','Neutral')}\n"
        ctx += f"TESTO INTEGRALE: {a.get('testo_completo', '')[:1800]}\n" 
        ctx += "---\n"

    # 3. IL PROMPT "EXECUTIVE KILLER" (Ispirato al Report Snam)
    system_prompt = f"""
    Sei SPIZ, Senior Intelligence Analyst per il Top Management. 
    Il tuo compito NON è riassumere, ma fornire CONTRO-NARRATIVE STRATEGICHE.
    
    REGOLE DI RAGIONAMENTO (STILE REPORT SNAM):
    1. SMONTA IL GIORNALISTA: Se Marcello Lezzi (QN) attacca sui costi energetici, non suggerire "comunicazione proattiva". Trova nel testo i dati che usa lui e suggerisci come smentirli (es. "Citare l'abbattimento dei costi del 15% ottenuto con l'impianto X").
    2. PESO SPECIFICO: Distingui tra attacchi di testate locali (rischio territorio) e nazionali (rischio politico/borsa).
    3. NO FUFFA: Bandite frasi come "promuovere la trasparenza" o "collaborazione con stakeholder". Sostituiscile con azioni di lobby o media relation chirurgiche (es. "Organizzare un briefing tecnico riservato con il caposervizio economia di QN per correggere l'imprecisione sui polimeri").
    4. RAPPORTO SULLA MINACCIA: Identifica chi sta guidando il sentiment negativo e con quale forza (AVE).
    
    DATI DISPONIBILI:
    {ctx}
    """

    response = openai.chat.completions.create(
        model="gpt-4o", # Forza l'uso del modello più intelligente
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.1 # Zero creatività, solo analisi fredda
    )
    
    return response.choices[0].message.content