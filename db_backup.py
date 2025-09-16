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

# Validate required environment variables
required_vars = ['DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 
                 'BACKUP_DIR', 'RCLONE_REMOTE', 'RCLONE_BACKUP_DIR']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Ensure backup dir exists
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    logger.info(f"Using backup directory: {BACKUP_DIR}")
except Exception as e:
    logger.error(f"Failed to create backup directory {BACKUP_DIR}: {e}")
    sys.exit(1)

def create_db_backup():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_file = os.path.join(BACKUP_DIR, f"{DB_NAME}_{timestamp}.sql")
    compressed_file = f"{backup_file}.gz"
    
    try:
        if 'postgresql' in DB_ENGINE.lower():
            logger.info(f"Creating PostgreSQL backup for database {DB_NAME}")
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_PASSWORD
            cmd = [
                'pg_dump',
                '-h', DB_HOST,
                '-p', DB_PORT,
                '-U', DB_USER,
                '-d', DB_NAME,
                '--no-owner',  # Avoid ownership issues during restore
                '--no-acl'     # Don't include access privileges
            ]
            with open(backup_file, 'wb') as f:
                subprocess.run(cmd, env=env, stdout=f, check=True)
        elif 'mysql' in DB_ENGINE.lower():
            logger.info(f"Creating MySQL backup for database {DB_NAME}")
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
            logger.error(f"Unsupported database engine: {DB_ENGINE}")
            return None

        # Check if the backup file was created and has content
        if not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            logger.error(f"Backup file is empty or was not created: {backup_file}")
            return None
            
        # Compress using gzip
        logger.info(f"Compressing backup file: {backup_file}")
        subprocess.run(['gzip', '-f', backup_file], check=True)
        
        if not os.path.exists(compressed_file):
            logger.error(f"Compression failed, compressed file not found: {compressed_file}")
            return None
            
        logger.info(f"Backup created and compressed: {compressed_file}")
        return compressed_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup command failed: {e}")
        # Clean up any partial backup file
        if os.path.exists(backup_file):
            os.remove(backup_file)
        if os.path.exists(compressed_file):
            os.remove(compressed_file)
        return None
    except Exception as e:
        logger.error(f"Unexpected error during backup creation: {e}")
        # Clean up any partial backup file
        if os.path.exists(backup_file):
            os.remove(backup_file)
        if os.path.exists(compressed_file):
            os.remove(compressed_file)
        return None

def upload_to_gdrive(file_path):
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
    try:
        # Use rclone with explicit parameters to avoid backup-dir issues
        # First, create the destination directory if it doesn't exist
        mkdir_cmd = ['rclone', 'mkdir', remote_path]
        try:
            subprocess.run(mkdir_cmd, check=True)
            logger.info(f"Ensured remote directory exists: {remote_path}")
        except subprocess.CalledProcessError:
            logger.warning(f"Could not create directory {remote_path}, it may already exist")
        
        # Use copyto instead of copy to be more explicit about the destination
        filename = os.path.basename(file_path)
        cmd = ['rclone', 'copyto', file_path, f"{remote_path}/{filename}", '--no-traverse']
        subprocess.run(cmd, check=True)
        logger.info(f"Backup uploaded to Google Drive: {filename}")
        
        # Delete the local file after successful upload
        os.remove(file_path)
        logger.info(f"Local backup file removed: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upload backup: {e}")
        return False

def cleanup_old_backups():
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
    try:
        # First, ensure the remote directory exists
        mkdir_cmd = ['rclone', 'mkdir', remote_path]
        try:
            subprocess.run(mkdir_cmd, check=True)
            logger.info(f"Ensured remote directory exists: {remote_path}")
        except subprocess.CalledProcessError:
            # Directory likely already exists, continue
            pass
            
        # List all files in the backup directory with a more reliable command
        list_cmd = ['rclone', 'lsf', remote_path, '--format', 'tp']
        result = subprocess.run(list_cmd, capture_output=True, text=True)
        
        if result.returncode != 0 or not result.stdout.strip():
            logger.info(f"No files found in remote directory or directory is empty")
            return True  # No files to clean up
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Process each file
        deleted_count = 0
        for line in result.stdout.splitlines():
            parts = line.strip().split(';')
            if len(parts) != 2:
                continue
                
            timestamp, filename = parts
            # Extract date from filename (format: DBNAME_YYYY-MM-DD_HH-MM.sql.gz)
            try:
                date_part = filename.split('_')[1]  # Extract YYYY-MM-DD part
                if date_part < cutoff_str:
                    # Delete the file with a more explicit command
                    delete_cmd = ['rclone', 'delete', f"{remote_path}/{filename}", '--no-traverse']
                    subprocess.run(delete_cmd, check=True)
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {filename}")
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse date from filename: {filename}, error: {e}")
        
        logger.info(f"Cleaned up {deleted_count} backups older than {BACKUP_RETENTION_DAYS} days from Drive")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed cleanup on Drive: {e}")
        return False

def main():
    logger.info("Starting database backup process")
    
    # Step 1: Create database backup
    backup_file = create_db_backup()
    if not backup_file:
        logger.error("Backup creation failed, exiting")
        sys.exit(1)
    
    # Step 2: Upload to Google Drive
    upload_success = upload_to_gdrive(backup_file)
    if not upload_success:
        logger.error("Upload to Google Drive failed")
        logger.warning(f"Local backup file remains at: {backup_file}")
        # Don't exit here - still try to clean up old backups
    
    # Step 3: Clean up old backups (even if upload failed)
    cleanup_success = cleanup_old_backups()
    if not cleanup_success:
        logger.warning("Failed to clean up old backups from Google Drive")
    
    # Final status
    if upload_success and cleanup_success:
        logger.info("Database backup process completed successfully")
    else:
        logger.warning("Database backup process completed with warnings or errors")
        if not upload_success:
            logger.warning("The current backup was not uploaded to Google Drive")
        if not cleanup_success:
            logger.warning("Old backups were not cleaned up from Google Drive")

if __name__ == "__main__":
    main()
