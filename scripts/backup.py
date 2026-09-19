"""Database manual backup script.

TODO: Implement automated backup of chotu.db to BACKUP_DIR.
      Currently, daily backup is handled by the Scheduler class
      inside aniwife.core.scheduler.
"""

import os
import shutil
import time

from dotenv import load_dotenv


def main():
    load_dotenv()
    db_file = os.getenv("DATABASE_FILE", "data/nexus.db")
    backup_dir = os.getenv("BACKUP_DIR", "data/backups")

    if not os.path.exists(db_file):
        print(f"[!] Database file not found: {db_file}")
        return

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(backup_dir, f"nexus-{timestamp}.db")
    shutil.copy2(db_file, dest)
    print(f"[✓] Backup created: {dest}")



if __name__ == "__main__":
    main()
