#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if not os.path.exists(env_path):
    logger.error(f".env file not found at {env_path}")
    sys.exit(1)
load_dotenv(env_path)

# Get rclone settings from environment
RCLONE_REMOTE = os.getenv('RCLONE_REMOTE')
RCLONE_BACKUP_DIR = os.getenv('RCLONE_BACKUP_DIR')

def test_rclone_config():
    """Test if rclone is properly configured"""
    logger.info("Testing rclone configuration...")
    
    # Step 1: Check if rclone is installed
    try:
        result = subprocess.run(['rclone', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("rclone is not installed or not in PATH")
            return False
        logger.info(f"rclone version: {result.stdout.splitlines()[0]}")
    except FileNotFoundError:
        logger.error("rclone command not found. Please install rclone.")
        return False
    
    # Step 2: Check if the remote exists in config
    try:
        result = subprocess.run(['rclone', 'config', 'show'], capture_output=True, text=True)
        if RCLONE_REMOTE not in result.stdout:
            logger.error(f"Remote '{RCLONE_REMOTE}' not found in rclone config")
            logger.info("Please run 'rclone config' to set up the remote")
            return False
        logger.info(f"Remote '{RCLONE_REMOTE}' found in config")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check rclone config: {e}")
        return False
    
    # Step 3: Test listing the remote
    try:
        result = subprocess.run(['rclone', 'lsd', f"{RCLONE_REMOTE}:"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to list remote '{RCLONE_REMOTE}': {result.stderr}")
            return False
        logger.info(f"Successfully listed remote '{RCLONE_REMOTE}'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list remote: {e}")
        return False
    
    # Step 4: Test creating and removing a test directory
    test_dir = "RCLONE_TEST_DIR"
    try:
        # Create test directory
        subprocess.run(['rclone', 'mkdir', f"{RCLONE_REMOTE}:{test_dir}"], check=True)
        logger.info(f"Successfully created test directory '{test_dir}'")
        
        # Create a small test file
        test_file = "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test file for rclone.")
        
        # Upload the test file
        subprocess.run(['rclone', 'copy', test_file, f"{RCLONE_REMOTE}:{test_dir}"], check=True)
        logger.info(f"Successfully uploaded test file to '{test_dir}'")
        
        # Clean up
        os.remove(test_file)
        subprocess.run(['rclone', 'purge', f"{RCLONE_REMOTE}:{test_dir}"], check=True)
        logger.info(f"Successfully removed test directory '{test_dir}'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Test directory operations failed: {e}")
        return False
    
    # Step 5: Test the backup directory
    try:
        # Check if backup directory exists, create if not
        result = subprocess.run(
            ['rclone', 'lsd', f"{RCLONE_REMOTE}:"], 
            capture_output=True, text=True, check=True
        )
        
        backup_dir_exists = False
        for line in result.stdout.splitlines():
            if RCLONE_BACKUP_DIR in line:
                backup_dir_exists = True
                break
        
        if not backup_dir_exists:
            subprocess.run(['rclone', 'mkdir', f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"], check=True)
            logger.info(f"Created backup directory '{RCLONE_BACKUP_DIR}'")
        else:
            logger.info(f"Backup directory '{RCLONE_BACKUP_DIR}' already exists")
            
        # Test copy to backup directory
        test_file = "backup_test_file.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test backup file.")
            
        subprocess.run(['rclone', 'copy', test_file, f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"], check=True)
        logger.info(f"Successfully uploaded test file to backup directory '{RCLONE_BACKUP_DIR}'")
        
        # Clean up
        os.remove(test_file)
        subprocess.run(['rclone', 'delete', f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}/{test_file}"], check=True)
        logger.info(f"Successfully removed test file from backup directory")
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup directory operations failed: {e}")
        return False
    
    logger.info("All rclone tests passed successfully!")
    return True

if __name__ == "__main__":
    if test_rclone_config():
        logger.info("rclone is properly configured for database backups")
        sys.exit(0)
    else:
        logger.error("rclone configuration test failed")
        sys.exit(1)