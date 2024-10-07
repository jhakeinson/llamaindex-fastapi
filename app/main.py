from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from llama_index.readers.google import GoogleDriveReader
import os
import pickle

app = FastAPI()

# Middleware to allow cross-origin requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths to the credentials and token files
CREDENTIALS_FILE = "./auth-configs/credentials.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# OAuth 2.0 Flow setup
flow = Flow.from_client_secrets_file(
    CREDENTIALS_FILE, scopes=SCOPES, redirect_uri="https://if.ngrok.app/auth/callback"
)


@app.get("/")
def root():
    return {"message": "Welcome to FastAPI Google Drive Integration!"}


@app.get("/login")
def login():
    # Generate the Google OAuth URL for user authentication
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def callback(request: Request):
    # Retrieve authorization response URL
    authorization_response = str(request.url)

    # Complete the OAuth flow and obtain the credentials
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials

    # Save the token for future use
    with open(TOKEN_FILE, "wb") as token_file:
        pickle.dump(creds, token_file)

    return {"message": "Authentication complete! You can now use the Google Drive API."}


@app.get("/load_documents")
async def load_documents(folder_id: str):
    # Load the saved token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token_file:
            creds = pickle.load(token_file)
    else:
        raise HTTPException(
            status_code=401, detail="You need to authenticate first. Visit /login."
        )

    # Refresh the token if it's expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())

    authorized_user = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
    }

    # Initialize GoogleDriveReader with the credentials
    reader = GoogleDriveReader(
        folder_id=folder_id, authorized_user_info=authorized_user
    )

    # Load data from Google Drive
    try:
        documents = reader.list_resources()
        return {"message": f"Successfully loaded {len(documents)} documents!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
