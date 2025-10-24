import os
import tarfile
import urllib.request
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re

load_dotenv()

def get_db_connection():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    conn = psycopg2.connect(
        f'dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}'
    )
    return conn

def parse_single_rdf(file, conn):
  content = file.read()
  soup = BeautifulSoup(content, 'lxml-xml')
  for book_elem in soup.find_all('pgterms:ebook'):
    with conn.cursor() as cur:
      # Ebook
      ebook_id = book_elem.get('rdf:about')
      if book_elem.find('dcterms:title'):
        title = book_elem.find('dcterms:title').text
        publisher = book_elem.find('dcterms:publisher').text if book_elem.find('dcterms:publisher') else None
        publication_date = book_elem.find('dcterms:issued').text if book_elem.find('dcterms:issued') else None
        language_node = book_elem.find('dcterms:language')
        language = language_node.find('rdf:value').text if language_node else None
        rights = book_elem.find('dcterms:rights').text if book_elem.find('dcterms:rights') else None
        download_count = int(book_elem.find('pgterms:downloads').text)
        description = book_elem.find('dcterms:description').text if book_elem.find('dcterms:description') else None
        book_type = book_elem.find('dcterms:type').text if book_elem.find('dcterms:type') else None
        marc_fields = {}
        regex = re.compile('.*pgterms:marc.*')
        for marc_elem in book_elem.find_all(regex):
          marc_fields[marc_elem.name] = marc_elem.text
        marc = str(marc_fields)  
        
        cur.execute(
            """
            INSERT INTO ebook (
              id, 
              title, 
              publisher, 
              publication_date, 
              language, 
              license, 
              download_count, 
              description, 
              type, 
              marc
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
              ON CONFLICT (id) DO UPDATE SET 
              title=%s, 
              publisher=%s, 
              publication_date=%s, 
              language=%s, 
              license=%s, 
              download_count=%s, 
              description=%s, 
              type=%s, 
              marc=%s
            """,
            (ebook_id, 
             title, 
             publisher, 
             publication_date, 
             language, 
             rights, 
             download_count, 
             description, 
             book_type, 
             marc,
             title, 
             publisher, 
             publication_date, 
             language, 
             rights, 
             download_count, 
             description, 
             book_type, 
             marc
            )
        )

        # Author
        creator_node = book_elem.find('dcterms:creator')
        if creator_node and creator_node.find('pgterms:agent'):
          author_id = creator_node.find('pgterms:agent').get('rdf:about') if creator_node.find('pgterms:agent') else creator_node.find('pgterms:name').text
          author_name = creator_node.find('pgterms:name').text
          birth_date = ""
          if creator_node.find('pgterms:birthdate'):
            birth_date = creator_node.find('pgterms:birthdate').text
          death_date = ""
          if creator_node.find('pgterms:deathdate'):
            death_date = creator_node.find('pgterms:deathdate').text
          webpage = creator_node.find('pgterms:webpage').text if creator_node.find('pgterms:webpage') else None
          cur.execute(
                  "INSERT INTO author (id, name, birth_date, death_date, webpage) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET name=%s, birth_date=%s, death_date=%s, webpage=%s",
                  (author_id, author_name, birth_date, death_date,webpage,author_name, birth_date, death_date,webpage)
              )
          
          cur.execute("INSERT INTO author_ebook (ebook_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (ebook_id, author_id))
        
        # Subjects
        for subject_node in book_elem.find_all('dcterms:subject'):
          subject_name = subject_node.find('rdf:value').text
          cur.execute("INSERT INTO subject (id) VALUES (%s) ON CONFLICT DO NOTHING;",(subject_name,))
          
          cur.execute("INSERT INTO subject_ebook (ebook_id, subject_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (ebook_id, subject_name))

        # Bookshelves
        for bookshelf_node in book_elem.find_all('pgterms:bookshelf'):
          bookshelf_name = bookshelf_node.find('rdf:value').text
          cur.execute("INSERT INTO bookshelf (id) VALUES (%s) ON CONFLICT DO NOTHING;",(bookshelf_name,))
          cur.execute("INSERT INTO bookshelf_ebook (ebook_id, bookshelf_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (ebook_id, bookshelf_name))

        # # Formats
        for format_node in book_elem.find_all('dcterms:hasFormat'):
          file_node = format_node.find('pgterms:file')
          if file_node:
            mime_type = file_node.find('rdf:value').text
            url = file_node.get('rdf:about')
            cur.execute(
                "INSERT INTO format (id, mime_type) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET mime_type=%s",
                (url, mime_type, mime_type)
            )
            cur.execute("INSERT INTO format_ebook (ebook_id, format_id) VALUES (%s, %s)  ON CONFLICT DO NOTHING", (ebook_id, url))
        conn.commit ()

if __name__ == "__main__":
    url = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
    fname = "rdf-files.tar.bz2"
    if not os.path.isfile(fname):
      print("Downloading RDF data...")
      urllib.request.urlretrieve(url, fname)
      print("Download complete.")
    with get_db_connection() as db_conn:
      with tarfile.open(fname, mode="r:bz2") as tar:
        for member in tar:
            if member.name.endswith(".rdf"):
              with tar.extractfile(member) as file:
                parse_single_rdf(file, db_conn)
    print("Data import complete.")
