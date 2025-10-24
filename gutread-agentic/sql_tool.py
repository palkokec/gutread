import subprocess
import os
import logging
import psycopg2
import tempfile
from fastmcp import FastMCP
from dotenv import load_dotenv
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
load_dotenv()
sql_mcp = FastMCP(name="SQLTool")

@sql_mcp.tool   
def get_schema():
  os.environ['PGPASSWORD'] = os.getenv("DB_PASSWORD")
  with tempfile.NamedTemporaryFile() as output_file_path:
    pg_dump_command = [
        'pg_dump',
        '--schema-only', # Only dump the schema, not the data
        '--no-owner',    # Don't include ownership in the dump
        '--no-acl',      # Don't include access control lists (grants)
        '--file', output_file_path.name,
        '--host', os.getenv("DB_HOST"),
        '--username', os.getenv("DB_USER"),
        os.getenv("DB_NAME")
    ]
    try:
      subprocess.run(
          pg_dump_command,
          check=True,  # Raise an exception if the command fails
          capture_output=True,
          text=True
      )
      log.info("Schema dumped successfully.")
      with open(output_file_path.name, 'r') as f:
          return f.read()
    except subprocess.CalledProcessError as e:
        log.error(f"Error during pg_dump: {e.stderr}")
        return ""
    finally:
        # Unset the PGPASSWORD environment variable for security
        del os.environ['PGPASSWORD']

@sql_mcp.tool
def sql_search(query):
  statements = [s.strip() for s in query.split(';') if s.strip()]
  if len(statements) > 1:
    raise ValueError("Only a single SQL statement is allowed.")
  
  if not statements or not statements[0].lower().startswith('select'):
    raise ValueError("Only SELECT statements are allowed.")
    
  db_config = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }
  with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cursor:
      cursor.execute(query)
      
      # Check if the query returned any columns
      if cursor.description:
          column_names = [desc[0] for desc in cursor.description]
          results = cursor.fetchall()
      else:
          # For queries that don't return rows (e.g., INSERT, UPDATE)
          column_names = []
          results = []
      return results, column_names
    
if __name__ == "__main__":
  # print(get_schema())
  sql_mcp.run(transport="http", host="127.0.0.1", port=8001)
