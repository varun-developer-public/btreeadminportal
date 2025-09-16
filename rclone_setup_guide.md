# Rclone Setup Guide for Database Backups

## Issue Diagnosis

The error message `parameter to --backup-dir has to be on the same remote as destination` indicates that there might be an issue with your rclone configuration or the way rclone is being called.

## Checking Rclone Configuration

1. **Verify rclone installation**:
   ```bash
   rclone version
   ```

2. **Check existing rclone configuration**:
   ```bash
   rclone config show
   ```
   Look for the `gdrive` remote configuration.

3. **Verify Google Drive remote**:
   ```bash
   rclone lsd gdrive:
   ```
   This should list directories in your Google Drive without errors.

## Fixing Rclone Configuration

If the `gdrive` remote is not properly configured, follow these steps:

1. **Create or modify the rclone configuration**:
   ```bash
   rclone config
   ```
   - Choose `n` for new remote
   - Name: `gdrive`
   - Storage type: `drive` (Google Drive)
   - Follow the prompts to authenticate with Google

2. **Test the configuration**:
   ```bash
   # Create a test directory
   rclone mkdir gdrive:DB_Backups_Test
   
   # List directories to verify
   rclone lsd gdrive:
   
   # Remove test directory
   rclone rmdir gdrive:DB_Backups_Test
   ```

3. **Check for conflicting rclone configuration**:
   Look for any global rclone settings that might be adding a `--backup-dir` parameter automatically:
   ```bash
   cat ~/.config/rclone/rclone.conf
   ```

## Testing the Backup Script

After fixing the configuration:

1. **Run the backup script**:
   ```bash
   cd /var/www/btreeadminportal/
   source venv/bin/activate
   python3 db_backup.py
   ```

2. **Check the logs for any errors**:
   ```bash
   tail -n 50 /var/www/btreeadminportal/db_backup.log
   ```

## Additional Troubleshooting

If you're still experiencing issues:

1. **Try a manual rclone copy**:
   ```bash
   # Create a test file
   echo "test" > /tmp/test_file.txt
   
   # Try to copy it to Google Drive
   rclone copy /tmp/test_file.txt gdrive:DB_Backups
   
   # Verify it was copied
   rclone ls gdrive:DB_Backups
   ```

2. **Check for rclone environment variables**:
   ```bash
   env | grep RCLONE
   ```

3. **Ensure the Google Drive API is enabled** in your Google Cloud Console for the project associated with your rclone authentication.

## Setting Up Automated Backups

Once everything is working correctly, set up a cron job to run the backup script automatically:

```bash
# Edit crontab
crontab -e

# Add a line to run the backup daily at 2 AM
0 2 * * * cd /var/www/btreeadminportal && source venv/bin/activate && python3 db_backup.py
```

This will ensure your database is backed up daily to Google Drive.