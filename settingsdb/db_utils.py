import re
import csv
import os
import tempfile
import subprocess
from django.db import connections, transaction
from django.conf import settings
import sqlparse
import logging

logger = logging.getLogger(__name__)

def get_current_db_engine():
    """
    Detect the current database engine being used by Django.
    Returns a string: 'sqlite', 'postgresql', 'mysql', or 'unknown'
    """
    engine = connections['default'].vendor
    if engine == 'sqlite':
        return 'sqlite'
    elif engine == 'postgresql':
        return 'postgresql'
    elif engine == 'mysql':
        return 'mysql'
    else:
        return 'unknown'

def parse_sql_file(file_path):
    """
    Parse a SQL file and return a list of SQL statements.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()
    
    # Log the size of the file for debugging
    logger.info(f"Parsing SQL file with {len(sql_content)} characters")
    
    # Parse the SQL content into individual statements
    statements = sqlparse.split(sql_content)
    valid_statements = [stmt for stmt in statements if stmt.strip()]
    
    logger.info(f"Found {len(valid_statements)} SQL statements in file")
    
    # Log a sample of statements for debugging
    if valid_statements:
        logger.debug(f"First statement: {valid_statements[0][:100]}...")
        if len(valid_statements) > 1:
            logger.debug(f"Second statement: {valid_statements[1][:100]}...")
    
    return valid_statements

def convert_postgres_to_sqlite(sql_statement):
    """
    Convert PostgreSQL SQL statements to SQLite compatible format.
    """
    # Log the original SQL for debugging
    logger.debug(f"Converting PostgreSQL SQL to SQLite: {sql_statement[:100]}...")
    
    # Skip comments and empty statements
    if not sql_statement.strip() or sql_statement.strip().startswith('--'):
        return None
        
    # Skip PostgreSQL-specific operations that don't apply to SQLite
    if re.search(r'\bCREATE\s+SEQUENCE\b|\bALTER\s+SEQUENCE\b|\bSELECT\s+setval\b|\bCREATE\s+INDEX\b|\bALTER\s+INDEX\b|\bCOMMENT\s+ON\b|\bSET\s+\w+\b|\bset_config\b|\bSELECT\s+set_config\b', sql_statement, flags=re.IGNORECASE):
        logger.debug(f"Skipping PostgreSQL-specific statement: {sql_statement[:100]}...")
        return None
    
    # Remove schema references (public.table_name -> table_name)
    sql = re.sub(r'\b\w+\.(\w+)', r'\1', sql_statement)
    
    # Handle CREATE TABLE statements
    if re.search(r'\bCREATE\s+TABLE\b', sql, flags=re.IGNORECASE):
        logger.debug(f"Converting CREATE TABLE statement: {sql[:100]}...")
        # Replace data types
        sql = re.sub(r'\btimestamp\s+with\s+time\s+zone\b', 'DATETIME', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\btimestamp\s+without\s+time\s+zone\b', 'DATETIME', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\btimestamp\b', 'DATETIME', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bserial\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bbigserial\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bsmallserial\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\binteger\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bbigint\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bsmallint\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\breal\b', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdouble\s+precision\b', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bnumeric\b', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\btext\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bvarchar\(\d+\)\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bchar\(\d+\)\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bboolean\b', 'BOOLEAN', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bjsonb\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bjson\b', 'TEXT', sql, flags=re.IGNORECASE)
        
        # Replace PostgreSQL-specific column constraints
        sql = re.sub(r'\bPRIMARY\s+KEY\s+DEFAULT\s+nextval\([^)]+\)\b', 'PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bDEFAULT\s+nextval\([^)]+\)\b', 'AUTOINCREMENT', sql, flags=re.IGNORECASE)
        
        # Remove PostgreSQL-specific table constraints
        sql = re.sub(r'\bCONSTRAINT\s+\w+\s+FOREIGN\s+KEY[^,;]+', '', sql, flags=re.IGNORECASE)
        
        # Remove ON UPDATE/ON DELETE clauses
        sql = re.sub(r'\bON\s+UPDATE\s+\w+\s+ON\s+DELETE\s+\w+\b', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bON\s+DELETE\s+\w+\b', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bON\s+UPDATE\s+\w+\b', '', sql, flags=re.IGNORECASE)
        
        # Fix trailing commas before closing parenthesis (common issue after removing constraints)
        sql = re.sub(r',\s*\)', ')', sql)
        
        logger.debug(f"Converted CREATE TABLE result: {sql[:100]}...")
    
    # Handle COPY statements
    elif re.search(r'\bCOPY\b', sql, flags=re.IGNORECASE):
        logger.debug(f"Converting COPY statement: {sql[:100]}...")
        
        # Extract table name and columns from COPY statement
        copy_match = re.search(r'COPY\s+([\w\.]+)\s+\((.*?)\)\s+FROM\s+stdin;', sql, re.DOTALL | re.IGNORECASE)
        if not copy_match:
            return None
            
        table_name = copy_match.group(1).split('.')[-1]
        columns = [col.strip() for col in copy_match.group(2).split(',')]
        
        # Extract data from the COPY statement
        data_lines = sql.splitlines()[1:-1] # Exclude COPY line and '\.'
        
        # Generate INSERT statements
        insert_statements = []
        for line in data_lines:
            # Use csv module to handle tab-separated data robustly
            # This handles escaped characters and quotes better.
            reader = csv.reader([line], delimiter='\t', quotechar='"')
            values = next(reader)

            if len(values) != len(columns):
                logger.warning(f"Skipping line due to column mismatch. Expected {len(columns)}, got {len(values)}. Line: {line}")
                continue

            formatted_values = []
            for val in values:
                if val == r'\N':
                    formatted_values.append('NULL')
                else:
                    # Escape single quotes for SQL
                    val = val.replace("'", "''")
                    # Handle boolean values
                    if val.lower() == 't':
                        formatted_values.append('1')
                    elif val.lower() == 'f':
                        formatted_values.append('0')
                    else:
                        formatted_values.append(f"'{val}'")
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(formatted_values)});"
            insert_statements.append(insert_sql)
            
        return "\n".join(insert_statements)
    
    return sql

def convert_postgres_to_mysql(sql_statement):
    """
    Convert PostgreSQL SQL statements to MySQL compatible format.
    """
    # Remove schema references (public.table_name -> table_name)
    sql = re.sub(r'\b\w+\.(\w+)', r'\1', sql_statement)
    
    # Replace data types
    sql = re.sub(r'\btimestamp\s+with\s+time\s+zone\b', 'DATETIME', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\btimestamp\s+without\s+time\s+zone\b', 'DATETIME', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\btimestamp\b', 'DATETIME', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bserial\b', 'INT AUTO_INCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bbigserial\b', 'BIGINT AUTO_INCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bsmallserial\b', 'SMALLINT AUTO_INCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\btext\b', 'LONGTEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bjsonb\b', 'JSON', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bjson\b', 'JSON', sql, flags=re.IGNORECASE)
    
    # Replace PostgreSQL-specific syntax
    sql = re.sub(r'\bDEFAULT\s+nextval\([^)]+\)\b', 'AUTO_INCREMENT', sql, flags=re.IGNORECASE)
    
    # Remove PostgreSQL-specific sequence operations
    if re.search(r'\bCREATE\s+SEQUENCE\b|\bALTER\s+SEQUENCE\b|\bSELECT\s+setval\b', sql, flags=re.IGNORECASE):
        return None
    
    # Remove PostgreSQL-specific comments
    if sql.strip().startswith('--'):
        return None
    
    return sql

def import_sql_backup(file_path, user):
    """
    Import a SQL backup file into the current database.
    Detects the current DB engine and converts the SQL statements if necessary.
    
    Args:
        file_path: Path to the SQL backup file
        user: The user who initiated the import
        
    Returns:
        tuple: (success, message, tables_affected)
    """
    current_engine = get_current_db_engine()
    logger.info(f"Current database engine: {current_engine}")
    
    # Assume the backup is from PostgreSQL (most common production DB)
    source_engine = 'postgresql'
    
    # Parse the SQL file
    try:
        # Log file details for debugging
        file_size = os.path.getsize(file_path)
        logger.info(f"SQL file size: {file_size} bytes")
        
        # Read the first few lines to check content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(1000)
            logger.debug(f"SQL file sample: {sample}")
        
        sql_statements = parse_sql_file(file_path)
        logger.info(f"Parsed {len(sql_statements)} SQL statements")
        
        # Validate that we have statements to process
        if not sql_statements:
            logger.warning("No valid SQL statements found in the file")
            return False, "No valid SQL statements found in the file", {}
    except Exception as e:
        logger.error(f"Error parsing SQL file: {str(e)}")
        return False, f"Error parsing SQL file: {str(e)}", {}
    
    # If the current engine is PostgreSQL, we can directly import the backup
    if current_engine == 'postgresql' and source_engine == 'postgresql':
        try:
            # For PostgreSQL, it's better to use the psql command-line tool
            db_settings = settings.DATABASES['default']
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            cmd = [
                'psql',
                '-h', db_settings['HOST'],
                '-p', db_settings['PORT'],
                '-U', db_settings['USER'],
                '-d', db_settings['NAME'],
                '-f', file_path
            ]
            
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f"Error importing PostgreSQL backup: {error_msg}")
                return False, f"Error importing PostgreSQL backup: {error_msg}", {}
                
            # Extract affected tables from the SQL statements
            tables_affected = extract_affected_tables(sql_statements)
            return True, "Backup imported successfully", tables_affected
            
        except Exception as e:
            logger.error(f"Error importing PostgreSQL backup: {str(e)}")
            return False, f"Error importing PostgreSQL backup: {str(e)}", {}
    
    # For other engines, we need to convert the SQL statements
    converted_statements = []
    tables_affected = {}
    
    for stmt in sql_statements:
        if not stmt.strip():
            continue
            
        # Skip statements that are not relevant for data import
        if re.search(r'\bCOMMENT\s+ON\b|\bALTER\s+SEQUENCE\b|\bCREATE\s+SEQUENCE\b', stmt, flags=re.IGNORECASE):
            continue
            
        # Extract table name for CREATE TABLE and INSERT statements
        table_match = re.search(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\'`]?([\w\.]+)["\'`]?', stmt, flags=re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1).split('.')[-1]  # Remove schema if present
            if table_name not in tables_affected:
                tables_affected[table_name] = {'created': True, 'rows_inserted': 0}
                
        insert_match = re.search(r'\bINSERT\s+INTO\s+["\'`]?([\w\.]+)["\'`]?', stmt, flags=re.IGNORECASE)
        if insert_match:
            table_name = insert_match.group(1).split('.')[-1]  # Remove schema if present
            if table_name not in tables_affected:
                tables_affected[table_name] = {'created': False, 'rows_inserted': 0}
            tables_affected[table_name]['rows_inserted'] += 1
        
        # Convert statement based on target engine
        if current_engine == 'sqlite':
            converted_stmt = convert_postgres_to_sqlite(stmt)
        elif current_engine == 'mysql':
            converted_stmt = convert_postgres_to_mysql(stmt)
        else:
            # For unknown engines, keep the statement as is
            converted_stmt = stmt
            
        if converted_stmt:
            # The conversion might return multiple statements (e.g., for COPY)
            converted_statements.extend(converted_stmt.splitlines())
    
    # Define the correct insertion order based on model dependencies
    insertion_order = [
        'accounts_customuser', 'consultantdb_consultant', 'coursedb_coursecategory', 'settingsdb_sourceofjoining',
        'settingsdb_paymentaccount', 'placementdrive_company', 'trainersdb_trainer',
        'consultantdb_consultantprofile', 'consultantdb_goal', 'consultantdb_achievement', 'coursedb_course',
        'settingsdb_usersettings', 'settingsdb_dbbackupimport', 'settingsdb_transactionlog',
        'batchdb_batch', 'coursedb_coursemodule', 'coursedb_topic', 'paymentdb_payment', 'placementdb_placement',
        'placementdrive_resumesharedstatus', 'studentsdb_student',
        'batchdb_batchstudent', 'batchdb_batchtransaction', 'batchdb_trainerhandover', 'batchdb_transferrequest',
        'placementdb_companyinterview', 'placementdrive_interview',
        'placementdrive_interviewstudent'
    ]

    # Group statements by table
    grouped_statements = {table: [] for table in insertion_order}
    for stmt in converted_statements:
        match = re.search(r'INSERT\s+INTO\s+([\w_]+)', stmt, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            if table_name in grouped_statements:
                grouped_statements[table_name].append(stmt)

    # Execute the converted statements
    try:
        success_count = 0
        error_count = 0
        error_messages = []
        skipped_count = 0
        
        # Get database connection
        connection = connections['default']
        
        # Use transaction.atomic() to ensure all statements are committed
        with transaction.atomic():
            cursor = connection.cursor()
            
            # Log the number of statements to execute
            logger.info(f"Executing {len(converted_statements)} SQL statements within a transaction")

            # For SQLite, disable foreign keys for the entire import
            if current_engine == 'sqlite':
                cursor.execute('PRAGMA foreign_keys = OFF;')
            
            for table_name in insertion_order:
                for i, stmt in enumerate(grouped_statements[table_name]):
                    if not stmt or not stmt.strip():
                        skipped_count += 1
                        continue
                        
                    try:
                        # Log the statement for debugging
                        logger.debug(f"Executing statement for {table_name}: {stmt[:100]}...")
                        
                        cursor.execute(stmt)
                        success_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Error executing statement for {table_name}: {str(e)}\nStatement: {stmt[:200]}..."
                        logger.warning(error_msg)
                        error_messages.append(error_msg)
                        # Continue with next statement instead of failing completely
                        continue

            # For SQLite, re-enable foreign keys
            if current_engine == 'sqlite':
                cursor.execute('PRAGMA foreign_keys = ON;')
        
        # Log summary
        logger.info(f"SQL import transaction completed: {success_count} statements succeeded, {error_count} failed, {skipped_count} skipped")
        
        if error_count > 0:
            # If there were some errors but also some successes, return partial success
            if success_count > 0:
                return True, f"Backup imported with {error_count} errors. {success_count} statements executed successfully.", tables_affected
            else:
                # If all statements failed, return failure
                return False, f"Failed to import backup. All {error_count} statements failed. First error: {error_messages[0] if error_messages else 'Unknown error'}", {}
        else:
            return True, f"Backup imported successfully. {success_count} statements executed.", tables_affected
    except Exception as e:
        logger.error(f"Error importing backup: {str(e)}")
        return False, f"Error importing backup: {str(e)}", {}

def extract_affected_tables(sql_statements):
    """
    Extract the tables affected by the SQL statements.
    
    Args:
        sql_statements: List of SQL statements
        
    Returns:
        dict: Dictionary of table names and their status
    """
    tables_affected = {}
    
    for stmt in sql_statements:
        # Extract table name for CREATE TABLE statements
        table_match = re.search(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\'`]?([\w\.]+)["\'`]?', stmt, flags=re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1).split('.')[-1]  # Remove schema if present
            if table_name not in tables_affected:
                tables_affected[table_name] = {'created': True, 'rows_inserted': 0}
                
        # Extract table name for INSERT statements
        insert_match = re.search(r'\bINSERT\s+INTO\s+["\'`]?([\w\.]+)["\'`]?', stmt, flags=re.IGNORECASE)
        if insert_match:
            table_name = insert_match.group(1).split('.')[-1]  # Remove schema if present
            if table_name not in tables_affected:
                tables_affected[table_name] = {'created': False, 'rows_inserted': 0}
            tables_affected[table_name]['rows_inserted'] += 1
    
    return tables_affected