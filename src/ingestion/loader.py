from llama_index.readers.google import GoogleDriveReader

def create_loader(service_account_json_path: str) -> GoogleDriveReader:
    return GoogleDriveReader(service_account_key_path=service_account_json_path)

def load_folder(loader: GoogleDriveReader, folder_id: str) -> list:
    return loader.load_data(folder_id=folder_id)

def load_file(loader: GoogleDriveReader, file_id: str) -> list:
    return loader.load_data(file_ids=[file_id])
