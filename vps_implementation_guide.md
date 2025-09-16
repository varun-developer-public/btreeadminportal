# VPS Implementation Guide for Database Backup Fix

## Overview

This guide provides step-by-step instructions to fix the database backup issue on your VPS. The error `parameter to --backup-dir has to be on the same remote as destination` indicates a problem with the rclone command parameters.

## Implementation Steps

### 1. Update the Backup Script

```bash
# SSH into your VPS
ssh root@your_vps_ip

# Navigate to the project directory
cd /var/www/btreeadminportal/

# Create a backup of the current script
cp db_backup.py db_backup.py.bak

# Edit the db_backup.py file
nano db_backup.py
```

Locate the `upload_to_gdrive` function (around line 130) and modify it to match the following:

```python
def upload_to_gdrive(file_path):
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_BACKUP_DIR}"
    try:
        # Use rclone copy with proper parameters
        # The error was due to an implicit --backup-dir parameter or configuration
        # We'll use a simpler command without any backup-dir options
        cmd = ['rclone', 'copy', file_path, remote_path]
        subprocess.run(cmd, check=True)
        logger.info(f"Backup uploaded to Google Drive: {os.path.basename(file_path)}")
        
        # Delete the local file after successful upload
        os.remove(file_path)
        logger.info(f"Local backup file removed: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upload backup: {e}")
        return False
```

Save the file and exit the editor.

### 2. Test the Rclone Configuration

Upload the test script to your VPS:

```bash
# If using scp from your local machine
scp test_rclone.py root@your_vps_ip:/var/www/btreeadminportal/

# On the VPS, make it executable
chmod +x /var/www/btreeadminportal/test_rclone.py

# Run the test script
cd /var/www/btreeadminportal/
source venv/bin/activate
python3 test_rclone.py
```

If the test script reports any issues, refer to the rclone setup guide for troubleshooting.

### 3. Test the Backup Script

```bash
# Run the backup script
cd /var/www/btreeadminportal/
source venv/bin/activate
python3 db_backup.py

# Check the logs for any errors
tail -n 50 /var/www/btreeadminportal/db_backup.log
```

### 4. Check Rclone Configuration

If you're still experiencing issues, check your rclone configuration:

```bash
# View current rclone configuration
rclone config show

# If needed, reconfigure the Google Drive remote
rclone config
```

Follow the prompts to set up the Google Drive remote correctly.

### 5. Verify Backup in Google Drive

After a successful backup run, verify that the backup file appears in your Google Drive in the specified backup directory.

### 6. Set Up Automated Backups

Once everything is working correctly, ensure your cron job is properly set up:

```bash
# Edit crontab
crontab -e

# Add or verify the following line to run daily backups at 2 AM
0 2 * * * cd /var/www/btreeadminportal && source venv/bin/activate && python3 db_backup.py
```

## Troubleshooting

### Common Issues

1. **Authentication Problems**: If rclone can't authenticate with Google Drive, run `rclone config` and follow the OAuth flow again.

2. **Permission Issues**: Ensure the user running the backup script has permission to execute rclone and access the necessary directories.

3. **Path Issues**: Verify that all paths in the .env file are correct and accessible.

4. **Rclone Version**: Ensure you're using a recent version of rclone. Update if necessary with:
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   ```

### Getting Help

If you continue to experience issues, check the rclone documentation or forums:

- Rclone documentation: https://rclone.org/docs/
- Rclone forum: https://forum.rclone.org/

## Conclusion

By following these steps, you should be able to fix the database backup issue and ensure your PostgreSQL database is regularly backed up to Google Drive. The main fix involves simplifying the rclone command to avoid the `--backup-dir` parameter conflict.