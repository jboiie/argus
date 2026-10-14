import os
from dotenv import load_dotenv
load_dotenv("C:/Programming/Projects/argus/.env")
from supabase import create_client

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
try:
    resp = client.table("runs").select("*").limit(3).execute()
    print(f"READ OK: {len(resp.data)} rows fetched from 'runs'")
    for r in resp.data:
        print(" ", {k: r[k] for k in list(r.keys())[:4]})
except Exception as exc:
    print(f"READ FAILED: {type(exc).__name__}: {exc}")
