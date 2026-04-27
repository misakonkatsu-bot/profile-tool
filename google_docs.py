from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]
TOKEN_FILE = Path("token.json")
CREDENTIALS_FILE = Path("credentials.json")


def is_configured() -> bool:
    return CREDENTIALS_FILE.exists()


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def extract_folder_id(folder_url_or_id: str) -> str:
    """GoogleドライブのフォルダURLまたはIDからフォルダIDを取得する"""
    s = folder_url_or_id.strip()
    if "folders/" in s:
        return s.split("folders/")[-1].split("?")[0].strip()
    return s


def save_to_google_docs(title: str, content: str, folder_id: str = "") -> str:
    creds = get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc.get("documentId")

    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": content,
            }
        }
    ]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()

    if folder_id:
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents="root",
            fields="id, parents",
        ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"
