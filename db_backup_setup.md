# Database Backup System Setup

This document provides instructions for setting up the automated database backup system for the BTree Admin Portal.

## 1. Environment Setup

### 1.1 Create .env File

Create a `.env` file at `/var/www/btreeadminportal/.env` using the provided template:

```bash
cp /var/www/btreeadminportal/.env.template /var/www/btreeadminportal/.env
```

Edit the file to ensure all values are correct for your environment:

```bash
nano /var/www/btreeadminportal/.env
```

### 1.2 Install Required Packages

```bash
# Install python-dotenv
pip install python-dotenv

# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Ensure database client tools are installed
# For PostgreSQL
sudo apt-get install postgresql-client

# For MySQL (if using MySQL instead)
# sudo apt-get install mysql-client
```

## 2. Configure rclone with Google Drive

### 2.1 Initial rclone Setup

Run the following command to start the configuration process:

```bash
rclone config
```

Follow these steps:

1. Select `n` for "New remote"
2. Name: Enter `gdrive` (or whatever you specified in your .env file)
3. Storage: Select `drive` for Google Drive
4. Client ID: Leave blank for default
5. Client Secret: Leave blank for default
6. Scope: Select `1` for full access
7. Root folder ID: Leave blank
8. Service account credentials: Leave blank
9. Edit advanced config: `n` for no
10. Use auto config: 
   - If you have a desktop environment: `y` for yes
   - If you're on a headless server: `n` for no, then follow the link provided to authorize
11. Configure as team drive: `n` for no
12. Confirm the configuration: `y` for yes

### 2.2 Verify rclone Configuration

Test your rclone configuration:

```bash
rclone lsd gdrive:
```

This should list the top-level directories in your Google Drive.

## 3. Create Backup Directory

Create the local backup directory specified in your .env file:

```bash
mkdir -p /var/www/btreeadminportal/backups
chmod 750 /var/www/btreeadminportal/backups
```

## 4. Set Up Cron Job

Edit the crontab to add a daily backup job:

```bash
sudo crontab -e
```

Add the following line to run the backup every day at 2 AM:

```
0 2 * * * /usr/bin/python3 /var/www/btreeadminportal/db_backup.py >> /var/www/btreeadminportal/db_backup.log 2>&1
```

## 5. Test the Backup System

Run the backup script manually to ensure it works correctly:

```bash
python3 /var/www/btreeadminportal/db_backup.py
```

Check the log file for any errors:

```bash
cat /var/www/btreeadminportal/db_backup.log
```

Verify that the backup was uploaded to Google Drive:

```bash
rclone ls gdrive:DB_Backups
```

## 6. Security Considerations

1. Ensure the `.env` file has restricted permissions:

```bash
chmod 600 /var/www/btreeadminportal/.env
```

2. Make the backup script executable:

```bash
chmod 750 /var/www/btreeadminportal/db_backup.py
```

3. Ensure the log file has appropriate permissions:

```bash
touch /var/www/btreeadminportal/db_backup.log
chmod 640 /var/www/btreeadminportal/db_backup.log
```

## 7. Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify database credentials in the `.env` file
   - Ensure the database server allows connections from the backup host

2. **rclone Authentication Issues**:
   - Run `rclone config` again to reconfigure Google Drive access
   - Check if the authentication token has expired

3. **Permission Denied Errors**:
   - Ensure the script has execute permissions
   - Check that the backup directory is writable

4. **Cron Job Not Running**:
   - Verify cron service is running: `systemctl status cron`
   - Check system logs: `grep CRON /var/log/syslog`

## 8. Maintenance

- Periodically check the backup log file for any errors
- Verify that backups are being created and uploaded successfully
- Test the restoration process occasionally to ensure backups are valid