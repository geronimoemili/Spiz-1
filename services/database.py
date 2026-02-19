import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def upsert_article(data):
    # On_conflict usa l'hash per evitare doppioni se ricarichi lo stesso file
    return supabase.table("articles").upsert(data, on_conflict="content_hash").execute()