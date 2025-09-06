#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/www/btreeadminportal/db_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load .env
env_path = '/var/www/btreeadminportal/.env'
if not os.path.exists(env_path):
    logger.error(f".env file not found at {env_path}")
    sys.exit(1)
load_dotenv(env_path)

# Environment variables
DB_ENGINE = os.getenv('DB_ENGINE')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
BACKUP_DIR = os.getenv('BACKUP_DIR')
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
RCLONE_REMOTE = os.getenv('RCLONE_REMOTE')
RCLONE_BACKUP_DIR = os.getenv('RCLONE_BACKUP_DIR')

# Ensure backup dir exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_db_backup():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_file = os.path.join(BACKUP_DIR, f"{DB_NAME}_{timestamp}.sql")
    compressed_file = f"{backup_file}.gz"

    if 'postgresql' in DB_ENGINE.lower():
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD
        cmd = ['pg_dump', '-h', DB_HOST, '-p', DB_PORT, '-U', DB_USER, '-d', DB_NAME]
        with open(backup_file, 'wb') as f:
            subprocess.run(cmd, env=env, stdout=f, check=True)
    elif 'mysql' in DB_ENGINE.lower():
        cmd = [
            'mysqldump',
            f"--host={DB_HOST}",
            f"--port={DB_PORT}",
            f"--user={DB_USER}",
            f"--password={DB_PASSWORD}",
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            DB_NAME
        ]
        with open(backup_file, 'wb') as f:
            subprocess.run(cmd, stdout=f, check=True)
    else:
        logger.error(f"Unsupported DB engine: {DB_ENGINE}")
        return None

    # Compress using gzip
    subprocess.run(['gzip', '-f', backup_file], check=True)
    logger.info(f"Backup created and compressed: {compressed_file}")
    return compressed_file

def upload_to_gdrive(file_path):
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
    try:
        # Use rclone move: uploads and deletes local file in one step
        cmd = ['rclone', 'move', file_path, remote_path, '--transfers', '4', '--checkers', '8']
        subprocess.run(cmd, check=True)
        logger.info(f"Backup uploaded to Google Drive: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upload backup: {e}")
        return False

def cleanup_old_backups():
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
    try:
        # Delete files older than retention days
        cmd = ['rclone', 'delete', remote_path, '--min-age', f'{BACKUP_RETENTION_DAYS}d']
        subprocess.run(cmd, check=True)
        logger.info(f"Cleaned up backups older than {BACKUP_RETENTION_DAYS} days from Drive")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed cleanup on Drive: {e}")
        return False

def main():
    logger.info("Starting DB backup process")
    backup_file = create_db_backup()
    if not backup_file:
        logger.error("Backup creation failed, exiting")
        sys.exit(1)

    if upload_to_gdrive(backup_file):
        logger.info("Upload successful")

    cleanup_old_backups()
    logger.info("DB backup process completed")

if __name__ == "__main__":
    main()
