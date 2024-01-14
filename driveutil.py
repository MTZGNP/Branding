import os
import hashlib
from typing import List
from dataclasses import dataclass
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

@dataclass
class DriveFile:
    name: str
    ID: str
    MD5: str
    local_path: str = None
    mime_type: str = None  # Add a metadata field

class DriveBrowser:
    def __init__(self, service_account_file, scopes):
        self.credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        self.service = build('drive', 'v3', credentials=self.credentials)

    def list_files(self, folder_id, recursive=False, files=None, tree=False, level=0) -> List[DriveFile]:
        if files is None:
            files = []

        def list_folder(id, level):
            page_token = None
            while True:
                query = f"'{id}' in parents and mimeType != 'application/vnd.google-apps.folder'"
                response = self.service.files().list(q=query, spaces='drive',
                                                     fields='nextPageToken, files(id, name, md5Checksum)',
                                                     pageToken=page_token, supportsAllDrives=True).execute()

                for item in response.get('files', []):
                    files.append(DriveFile(name=item['name'], ID=item["id"], MD5=item.get('md5Checksum', 'N/A')))
                    if tree:
                        print("    " * level + item['name'])

                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

            if recursive:
                folder_query = f"'{id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
                folder_results = self.service.files().list(q=folder_query, spaces='drive',
                                                           fields='nextPageToken, files(id, name)',
                                                           supportsAllDrives=True).execute()
                for folder in folder_results.get('files', []):
                    if tree:
                        print("    " * level + folder['name'])
                    list_folder(folder['id'], level + 1)

        list_folder(folder_id, level)

        return files
    def writeMIME(self, drive_file: DriveFile) -> DriveFile:
        try:
            # Retrieve the file metadata from Google Drive
            file_metadata = self.service.files().get(fileId=drive_file.ID, fields='mimeType').execute()
            # Update the MIME type in the DriveFile object
            drive_file.mime_type = file_metadata.get('mimeType')
            return drive_file
        except Exception as e:
            print(f"Failed to retrieve or update MIME type. Reason: {e}")
            return drive_file

    def download_file(self, drive_file: DriveFile, download_path: str) -> None:
        file_id = drive_file.ID
        request = self.service.files().get(fileId=file_id)
        file_metadata = request.execute()

        if file_metadata.get('mimeType').startswith('application/vnd.google-apps.'):
            request = self.service.files().export(fileId=file_id, mimeType='application/pdf')
        else:
            request = self.service.files().get_media(fileId=file_id)

        with open(download_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                try:
                    status, done = downloader.next_chunk()
                except Exception as e:
                    print(f"Failed to download file. Reason: {e}")
                    return

        drive_file.local_path = download_path

    def upload_file(self, local_file_path, parent_id=None):
        file_metadata = {'name': os.path.basename(local_file_path)}
        if parent_id:
            file_metadata['parents'] = [parent_id]

        media = MediaFileUpload(local_file_path)

        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            new_file_id = file.get('id')
            new_file_md5 = self.calculate_md5(local_file_path)
            return new_file_id, new_file_md5
        except Exception as e:
            print(f"Failed to upload file. Reason: {e}")
            return None, None

    def replace_with_local(self, drive_file: DriveFile) -> None:
        if drive_file.local_path is None:
            print("No local file path provided.")
            return

        if not os.path.exists(drive_file.local_path):
            print(f"Local file {drive_file.local_path} does not exist.")
            return

        file_metadata = self.service.files().get(fileId=drive_file.ID, fields='mimeType, parents').execute()
        if file_metadata.get('mimeType').startswith('application/vnd.google-apps.'):
            try:
                self.service.files().delete(fileId=drive_file.ID).execute()
            except Exception as e:
                print(f"Failed to delete original file. Reason: {e}")
                return

            parent_id = file_metadata.get('parents', [None])[0] if file_metadata.get('parents') else None
            new_file_id, new_file_md5 = self.upload_file(drive_file.local_path, parent_id)
            if new_file_id:
                print(f"Google Docs file replaced with {drive_file.local_path}. New file ID: {new_file_id}")
                drive_file.ID = new_file_id
                drive_file.MD5 = new_file_md5
            else:
                print("Failed to upload the new file.")
            return

        media = MediaFileUpload(drive_file.local_path)

        try:
            self.service.files().update(
                fileId=drive_file.ID,
                media_body=media
            ).execute()
            drive_file.MD5 = self.calculate_md5(drive_file.local_path)
            print(f"File '{drive_file.name}' has been replaced successfully.")
        except Exception as e:
            print(f"Failed to replace file. Reason: {e}")

    def calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

