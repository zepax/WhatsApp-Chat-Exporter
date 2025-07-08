#!/usr/bin/python3

import shutil
import sqlite3
import os
import time
import getpass
import threading
from Whatsapp_Chat_Exporter.utility import WhatsAppIdentifier
try:
    from iphone_backup_decrypt import EncryptedBackup, RelativePath
    from iphone_backup_decrypt import FailedToDecryptError
except ModuleNotFoundError:
    support_encrypted = False
else:
    support_encrypted = True


def extract_encrypted(base_dir, password, identifiers, bplist_reader=None):
    backup = EncryptedBackup(backup_directory=base_dir, passphrase=password, cleanup=False, check_same_thread=False)
    print("Decrypting WhatsApp database...", end="")
    try:
        backup.extract_file(
            relative_path=RelativePath.WHATSAPP_MESSAGES,
            domain=identifiers.DOMAIN,
            output_filename=identifiers.MESSAGE
        )
        backup.extract_file(
            relative_path=RelativePath.WHATSAPP_CONTACTS,
            domain=identifiers.DOMAIN,
            output_filename=identifiers.CONTACT
        )
    except FailedToDecryptError:
        print("Failed to decrypt backup: incorrect password?")
        exit()
    else:
        print("Done")
    extract_thread = threading.Thread(
        target=backup.extract_files_by_domain,
        args=(identifiers.DOMAIN, identifiers.DOMAIN, bplist_reader)
    )
    extract_thread.daemon = True
    extract_thread.start()
    dot = 0
    while extract_thread.is_alive():
        print(f"Decrypting and extracting files{'.' * dot}{' ' * (3 - dot)}", end="\r")
        if dot < 3:
            dot += 1
            time.sleep(0.5)
        else:
            dot = 0
            time.sleep(0.4)
    print(f"All required files decrypted and extracted.", end="\n")
    extract_thread.handled = True
    return backup


def is_encrypted(base_dir):
    with sqlite3.connect(os.path.join(base_dir, "Manifest.db")) as f:
        c = f.cursor()
        try:
            c.execute("""SELECT count()
                    FROM Files
                    """)
        except sqlite3.OperationalError as e:
            raise e  # These error cannot be used to determine if the backup is encrypted
        except sqlite3.DatabaseError:
            return True
        else:
            return False


def extract_media(base_dir, identifiers, preserve_timestamp=False):
    if preserve_timestamp:
        from Whatsapp_Chat_Exporter.bplist import BPListReader 
        preserve_timestamp = BPListReader
    if is_encrypted(base_dir):
        if not support_encrypted:
            print("You don't have the dependencies to handle encrypted backup.")
            print("Read more on how to deal with encrypted backup:")
            print("https://github.com/KnugiHK/Whatsapp-Chat-Exporter/blob/main/README.md#usage")
            return False
        print("Encryption detected on the backup!")
        password = getpass.getpass("Enter the password for the backup:")
        extract_encrypted(base_dir, password, identifiers, preserve_timestamp)
    else:
        wts_db = os.path.join(base_dir, identifiers.MESSAGE[:2], identifiers.MESSAGE)
        contact_db = os.path.join(base_dir, identifiers.CONTACT[:2], identifiers.CONTACT)
        if not os.path.isfile(wts_db):
            if identifiers is WhatsAppIdentifier:
                print("WhatsApp database not found.")
            else:
                print("WhatsApp Business database not found.")
            exit()
        else:
            shutil.copyfile(wts_db, identifiers.MESSAGE)
        if not os.path.isfile(contact_db):
            print("Contact database not found.")
            exit()
        else:
            shutil.copyfile(contact_db, identifiers.CONTACT)
        _wts_id = identifiers.DOMAIN
        with sqlite3.connect(os.path.join(base_dir, "Manifest.db")) as manifest:
            manifest.row_factory = sqlite3.Row
            c = manifest.cursor()
            c.execute(
                f"""SELECT count()
                    FROM Files
                    WHERE domain = '{_wts_id}'"""
            )
            total_row_number = c.fetchone()[0]
            print(f"Extracting WhatsApp files...(0/{total_row_number})", end="\r")
            c.execute(f"""SELECT fileID,
                                relativePath,
                                flags,
                                file AS metadata,
                                ROW_NUMBER() OVER(ORDER BY relativePath) AS _index
                        FROM Files
                        WHERE domain = '{_wts_id}'
                        ORDER BY relativePath""")
            if not os.path.isdir(_wts_id):
                os.mkdir(_wts_id)
            row = c.fetchone()
            while row is not None:
                if row["relativePath"] == "":
                    row = c.fetchone()
                    continue
                destination = os.path.join(_wts_id, row["relativePath"])
                hashes = row["fileID"]
                folder = hashes[:2]
                flags = row["flags"]
                if flags == 2:
                    try:
                        os.mkdir(destination)
                    except FileExistsError:
                        pass
                elif flags == 1:
                    shutil.copyfile(os.path.join(base_dir, folder, hashes), destination)
                    if preserve_timestamp:
                        metadata = BPListReader(row["metadata"]).parse()
                        creation = metadata["$objects"][1]["Birth"]
                        modification = metadata["$objects"][1]["LastModified"]
                        os.utime(destination, (modification, modification))
                if row["_index"] % 100 == 0:
                    print(f"Extracting WhatsApp files...({row['_index']}/{total_row_number})", end="\r")
                row = c.fetchone()
            print(f"Extracting WhatsApp files...({total_row_number}/{total_row_number})", end="\n")
