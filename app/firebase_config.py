import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.core.config import get_settings

settings = get_settings()

def initialize_firebase():
    """
    Initializes Firebase Admin SDK using the credentials defined in environment variables.
    If the app is already initialized, it simply returns the existing app.
    """
    if not firebase_admin._apps:
        # Load the credentials from the settings
        cred_dict = settings.firebase_credentials
        
        # Check if project_id is provided, otherwise initialize without explicitly providing credentials
        # (This may rely on the environment being set correctly, e.g., GOOGLE_APPLICATION_CREDENTIALS)
        if cred_dict.get("project_id"):
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback for environments with pre-configured GOOGLE_APPLICATION_CREDENTIALS
            firebase_admin.initialize_app()
    
    return firebase_admin.get_app()

def get_db():
    """
    Returns a Firestore client instance.
    """
    return firestore.client()

def get_auth():
    """
    Returns a Firebase Auth client instance.
    """
    return auth
