# ... inside main.py ...
# Core Firebase Admin SDK imports
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json # ADD THIS LINE TO HANDLE JSON STRING

# ... configuration and helper functions remain the same ...

# --- FIREBASE SETUP ---
try:
    if not firebase_admin._apps:
        # Check if the credentials variable exists
        creds_json = os.environ.get('FIREBASE_CREDENTIALS')
        
        if creds_json:
            # Load credentials from the environment variable JSON string
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
        # Fallback to default if creds_json is not set, but this usually fails on Render
        else:
            firebase_admin.initialize_app()
            
    db = firestore.client()
    print("Firestore initialized successfully.")
except Exception as e:
    print(f"FATAL ERROR: Firebase initialization failed. Persistence will not work. Error: {e}")
    db = None
# ... rest of the main.py code ...
