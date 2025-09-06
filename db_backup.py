#!/usr/bin/env python3
"""
Database Backup Script for BTree Admin Portal

This script performs the following operations:
1. Creates a database backup (PostgreSQL or MySQL)
2. Compresses the backup with gzip
3. Uploads the backup to Google Drive using rclone
4. Deletes local backup after successful upload
5. Removes backups older than the retention period from Google Drive

Requirements:
- python-dotenv
- rclone configured with Google Drive
- PostgreSQL or MySQL client tools installed
"""

import os
import sys
import subprocess
import datetime
import logging
import shutil
from pathlib import Path
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

# Load environment variables from .env file
env_path = '/var/www/btreeadminportal/.env'
if not os.path.exists(env_path):
    logger.error(f"Environment file not found at {env_path}")
    sys.exit(1)

load_dotenv(env_path)

# Get database configuration from environment variables
DB_ENGINE = os.getenv('DB_ENGINE')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Get backup configuration
BACKUP_DIR = os.getenv('BACKUP_DIR')
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
RCLONE_REMOTE = os.getenv('RCLONE_REMOTE')
RCLONE_BACKUP_DIR = os.getenv('RCLONE_BACKUP_DIR')

# Validate required environment variables
required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'BACKUP_DIR', 'RCLONE_REMOTE', 'RCLONE_BACKUP_DIR']
for var in required_vars:
    if not os.getenv(var):
        logger.error(f"Required environment variable {var} is not set")
        sys.exit(1)

# Create backup directory if it doesn't exist
if not os.path.exists(BACKUP_DIR):
    try:
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory: {BACKUP_DIR}")
    except Exception as e:
        logger.error(f"Failed to create backup directory: {e}")
        sys.exit(1)


def create_db_backup():
    """Create a database backup based on the configured engine"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_filename = f"{DB_NAME}_{timestamp}.sql"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)
    compressed_filepath = f"{backup_filepath}.gz"
    
    # Determine which database engine to use
    if 'postgresql' in DB_ENGINE:
        # PostgreSQL backup
        logger.info("Creating PostgreSQL backup")
        pg_env = os.environ.copy()
        pg_env['PGPASSWORD'] = DB_PASSWORD
        
        cmd = [
            'pg_dump',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-U', DB_USER,
            '-d', DB_NAME,
            '-f', backup_filepath,
            '--no-owner',
            '--no-acl'
        ]
        
        try:
            subprocess.run(cmd, env=pg_env, check=True)
            logger.info(f"PostgreSQL backup created at {backup_filepath}")
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            return None
            
    elif 'mysql' in DB_ENGINE:
        # MySQL backup
        logger.info("Creating MySQL backup")
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
        
        try:
            with open(backup_filepath, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            logger.info(f"MySQL backup created at {backup_filepath}")
        except subprocess.CalledProcessError as e:
            logger.error(f"MySQL backup failed: {e}")
            return None
    else:
        logger.error(f"Unsupported database engine: {DB_ENGINE}")
        return None
    
    # Compress the backup file
    try:
        with open(backup_filepath, 'rb') as f_in:
            with subprocess.Popen(['gzip'], stdin=subprocess.PIPE, stdout=open(compressed_filepath, 'wb')) as proc:
                proc.stdin.write(f_in.read())
        
        # Remove the uncompressed file
        os.remove(backup_filepath)
        logger.info(f"Backup compressed to {compressed_filepath}")
        return compressed_filepath
    except Exception as e:
        logger.error(f"Failed to compress backup: {e}")
        return None


def upload_to_gdrive(backup_filepath):
    """Upload the backup file to Google Drive using rclone"""
    try:
        # Ensure the remote path exists
        remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
        
        # Check if the remote directory exists, create if it doesn't
        check_cmd = ['rclone', 'lsf', remote_path]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Directory doesn't exist, create it
            mkdir_cmd = ['rclone', 'mkdir', remote_path]
            subprocess.run(mkdir_cmd, check=True)
            logger.info(f"Created remote directory: {remote_path}")
        
        # Upload the file
        upload_cmd = ['rclone', 'copy', backup_filepath, remote_path]
        subprocess.run(upload_cmd, check=True)
        
        logger.info(f"Backup uploaded to Google Drive: {os.path.basename(backup_filepath)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upload backup to Google Drive: {e}")
        return False


def cleanup_old_backups():
    """Remove backups older than the retention period from Google Drive"""
    try:
        # Get list of files in the backup directory
        remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
        list_cmd = ['rclone', 'lsf', '--format', 'tp', remote_path]
        result = subprocess.run(list_cmd, capture_output=True, text=True, check=True)
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Process each file
        for line in result.stdout.splitlines():
            parts = line.strip().split(';')
            if len(parts) != 2:
                continue
                
            timestamp, filename = parts
            # Extract date from filename (format: DBNAME_YYYY-MM-DD_HH-MM.sql.gz)
            try:
                date_part = filename.split('_')[1]  # Extract YYYY-MM-DD part
                if date_part < cutoff_str:
                    # Delete the file
                    delete_cmd = ['rclone', 'delete', f"{remote_path}/{filename}"]
                    subprocess.run(delete_cmd, check=True)
                    logger.info(f"Deleted old backup: {filename}")
            except (IndexError, ValueError):
                logger.warning(f"Could not parse date from filename: {filename}")
        
        logger.info("Cleanup of old backups completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to cleanup old backups: {e}")
        return False


def main():
    """Main function to orchestrate the backup process"""
    logger.info("Starting database backup process")
    
    # Create database backup
    backup_filepath = create_db_backup()
    if not backup_filepath:
        logger.error("Backup creation failed, exiting")
        sys.exit(1)
    
    # Upload to Google Drive
    upload_success = upload_to_gdrive(backup_filepath)
    
    # Remove local backup file if upload was successful
    if upload_success:
        try:
            os.remove(backup_filepath)
            logger.info(f"Local backup file removed: {backup_filepath}")
        except Exception as e:
            logger.error(f"Failed to remove local backup file: {e}")
    
    # Cleanup old backups
    cleanup_success = cleanup_old_backups()
    
    if upload_success and cleanup_success:
        logger.info("Database backup process completed successfully")
    else:
        logger.warning("Database backup process completed with warnings")


if __name__ == "__main__":
    main()