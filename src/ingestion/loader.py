import io
import os
import tempfile

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from llama_index.core import SimpleDirectoryReader

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Direct-download MIME types → file extension
_BINARY_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}

# Google Workspace types → (export MIME type, extension)
_EXPORT_TYPES = {
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"
    ),
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
}


def create_loader(service_account_json_path: str):
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=_SCOPES)
    return build("drive", "v3", credentials=creds)


def load_folder(service, folder_id: str) -> list:
    files = _collect_files(service, folder_id)
    return _download_and_parse(service, files)


def load_file(service, file_id: str) -> list:
    meta = service.files().get(
        fileId=file_id, fields="id,name,mimeType,shortcutDetails"
    ).execute()
    mime = meta["mimeType"]
    name = meta["name"]
    if mime == "application/vnd.google-apps.shortcut":
        target = meta.get("shortcutDetails", {})
        file_id = target.get("targetId", "")
        mime = target.get("targetMimeType", "")
    if not file_id or (mime not in _BINARY_TYPES and mime not in _EXPORT_TYPES):
        return []
    return _download_and_parse(service, [{"id": file_id, "name": name, "mimeType": mime}])


def _collect_files(service, folder_id: str) -> list[dict]:
    """Recursively collect downloadable files, resolving shortcuts and subfolders."""
    files = []
    page_token = None
    while True:
        result = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=100,
            **({"pageToken": page_token} if page_token else {}),
        ).execute()

        for f in result.get("files", []):
            mime = f["mimeType"]
            if mime == "application/vnd.google-apps.folder":
                files.extend(_collect_files(service, f["id"]))
            elif mime == "application/vnd.google-apps.shortcut":
                meta = service.files().get(
                    fileId=f["id"], fields="shortcutDetails"
                ).execute()
                target = meta.get("shortcutDetails", {})
                t_id = target.get("targetId", "")
                t_mime = target.get("targetMimeType", "")
                if not t_id:
                    continue
                if t_mime == "application/vnd.google-apps.folder":
                    files.extend(_collect_files(service, t_id))
                elif t_mime in _BINARY_TYPES or t_mime in _EXPORT_TYPES:
                    files.append({"id": t_id, "name": f["name"], "mimeType": t_mime})
            elif mime in _BINARY_TYPES or mime in _EXPORT_TYPES:
                files.append({"id": f["id"], "name": f["name"], "mimeType": mime})

        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return files


def _download_and_parse(service, files: list[dict]) -> list:
    """Download files to a temp dir and parse with SimpleDirectoryReader."""
    documents = []
    with tempfile.TemporaryDirectory() as tmpdir:
        downloaded = []
        for f in files:
            mime = f["mimeType"]
            ext = _BINARY_TYPES.get(mime) or _EXPORT_TYPES.get(mime, (None, ""))[1]
            dest = os.path.join(tmpdir, f["id"] + ext)
            if _fetch_file(service, f["id"], mime, dest):
                downloaded.append(dest)
                print(f"  loaded: {f['name']}")
        if downloaded:
            documents = SimpleDirectoryReader(input_files=downloaded).load_data()
    return documents


def _fetch_file(service, file_id: str, mime_type: str, dest_path: str) -> bool:
    try:
        if mime_type in _BINARY_TYPES:
            request = service.files().get_media(fileId=file_id)
        else:
            export_mime = _EXPORT_TYPES[mime_type][0]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        with io.FileIO(dest_path, mode="wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"  skip {file_id}: {e}")
        return False
