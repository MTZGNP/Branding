import json
import os

from dirutil import purge
from driveutil import DriveBrowser
from pdfutil import is_first_page_identical, prepend_page

directory = "tmp"
if not os.path.exists(directory):
    os.mkdir(directory)

TEMPLATE_PATH = "signet.pdf"

SCOPES = ['https://www.googleapis.com/auth/drive']
service_account_file = "servicekey.json"
browser = DriveBrowser(service_account_file, SCOPES)
folder_id = "..."

hash_file = 'hashes.json'
try:
    with open(hash_file, 'r') as file:
        hashes = json.load(file)
except FileNotFoundError:
    with open(hash_file, 'w') as file:
        hashes = []
        json.dump(hashes, file)

PDF_files = browser.list_files(folder_id, recursive=True, tree=False)
56
print(f"found {len(PDF_files)} files")
for i, File in enumerate(PDF_files):
    browser.writeMIME(File)
PDF_files = [f for f in PDF_files if (f.mime_type == "application/pdf" or f.name.endswith(".pdf"))]
print(f"found {len(PDF_files)} files with extension .pdf:")
for i, File in enumerate(PDF_files):
    print(f"#{i + 1}, {File.name}")
    if not File.name.endswith(".pdf"):
        File.name = File.name + ".pdf"
for i, File in enumerate(PDF_files):
    try:
        print(f"\n ~~~~ \n*processing {i + 1} out of {len(PDF_files)}\nBeing: {File.name}, aka {File.MD5}")
        if File.MD5 in hashes:
            print(f"signature            {File.MD5} found, skipping file")
            continue
        print(f"signature not found, downloading")
        browser.download_file(File, f"tmp/{File.name}")
        if is_first_page_identical(File.local_path, TEMPLATE_PATH):
            print(f"branding found, memorizing signature, skipping file")
            hashes.append(File.MD5)
            continue
        print("no branding found, processing!!")
        prepend_page(TEMPLATE_PATH, File.local_path)
        print("branding added")
        browser.replace_with_local(File)
        print("file uploaded")
    except Exception as error:
        print("error occurred", error)

# save hashes
print("\n\n******")
with open(hash_file, "w") as file:
    json.dump(hashes, file)
print("updated hashes")
purge("tmp")
print("purged tmp, initial state restored")
