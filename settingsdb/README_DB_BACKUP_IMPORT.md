# Database Backup Import Feature

## Overview

This feature allows superadmins to import SQL database backups into the current database, regardless of the database engine being used. It supports cross-database imports, meaning a PostgreSQL backup can be imported into SQLite or MySQL, and vice versa.

## Features

- Import SQL backup files (.sql) into the current database
- Support for different database engines (SQLite, PostgreSQL, MySQL)
- Cross-database compatibility (import PostgreSQL backup into SQLite, etc.)
- Restricted access to superadmins only
- Validation of uploaded files (only .sql files allowed)
- Success/error feedback after import
- Import history tracking

## Usage

1. Log in as a superadmin
2. Navigate to the Admin Settings dashboard
3. Click on "Import DB Backup"
4. Upload a .sql file (database backup)
5. Click "Import Backup"
6. Wait for the import to complete
7. View the success/error message

## Technical Details

### Database Engine Detection

The system automatically detects the current database engine being used by examining the Django settings. It supports:

- SQLite
- PostgreSQL
- MySQL

### Cross-Database Compatibility

When importing a backup from one database engine into another, the system performs the following operations:

1. Parses the SQL file to extract table creation and data insertion statements
2. Converts PostgreSQL-specific syntax to be compatible with SQLite or MySQL
3. Executes the converted statements on the current database

### Security

- Access is restricted to superadmins only using Django's `user_passes_test` decorator
- SQL files are validated to ensure they have the correct extension
- File size is limited to 50MB to prevent server overload
- All operations are performed within a database transaction to ensure atomicity

### Error Handling

The system provides detailed error messages for various scenarios:

- Invalid file format
- SQL syntax errors
- Database constraint violations
- Permission issues

## Testing

A comprehensive test suite is included to verify the functionality of the DB backup import feature:

- Access control tests
- Database engine detection tests
- SQL import success/failure tests
- File validation tests

To run the tests:

```bash
python manage.py test settingsdb.tests.DBBackupImportTest
```

Additionally, a manual test script is provided for testing with real database engines:

```bash
python settingsdb/test_db_import.py
```

## Troubleshooting

### Common Issues

1. **Import fails with syntax errors**
   - Ensure the SQL file is valid and compatible with the source database engine
   - Check for database-specific syntax that might not be properly converted

2. **Permission denied errors**
   - Ensure the user running the Django application has write permissions to the database

3. **Import takes too long**
   - Large SQL files may take a long time to import
   - Consider breaking up the import into smaller files

### Logs

Import history and errors are logged in the `DBBackupImport` model, which can be viewed in the Django admin interface.