DROP DATABASE IF EXISTS gutenberg;
CREATE USER gutenberg WITH ENCRYPTED PASSWORD 'gutenberg';
CREATE DATABASE gutenberg LOCALE 'en_US.UTF-8' OWNER gutenberg;
GRANT ALL PRIVILEGES ON DATABASE gutenberg TO gutenberg;

GRANT ALL ON SCHEMA public TO gutenberg;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO 

--
CREATE TABLE author (
    id varchar (255) PRIMARY KEY,
    name varchar (1024) NOT NULL,
    birth_date varchar (255),
    death_date varchar (255),
    webpage varchar (1024)
);

CREATE TABLE subject (
    id varchar (255) PRIMARY KEY
);

CREATE TABLE bookshelf (
    id varchar (255) PRIMARY KEY
);

CREATE TABLE format (
    id varchar (255) PRIMARY KEY,
    mime_type varchar (64) NOT NULL
);


CREATE TABLE ebook (
    id varchar (255) PRIMARY KEY,
    title varchar (1024) NOT NULL,
    publisher varchar(1024),
    license varchar (1024),
    publication_date DATE,
    language varchar (255),
    download_count INTEGER,
    marc TEXT,
    description TEXT,
    type varchar (255)

);

CREATE TABLE author_ebook (
  author_id varchar (255),
  ebook_id varchar (255),
  PRIMARY KEY (author_id, ebook_id),
  FOREIGN KEY (ebook_id) REFERENCES ebook (id),
  FOREIGN KEY (author_id) REFERENCES author (id)
);

CREATE TABLE bookshelf_ebook (
  bookshelf_id varchar (255) ,
  ebook_id varchar (255) ,
  PRIMARY KEY (bookshelf_id, ebook_id),
  FOREIGN KEY (ebook_id) REFERENCES ebook (id),
  FOREIGN KEY (bookshelf_id) REFERENCES bookshelf (id)
);

CREATE TABLE subject_ebook (
  subject_id varchar (255) ,
  ebook_id varchar (255) ,
  PRIMARY KEY (subject_id, ebook_id),
  FOREIGN KEY (ebook_id) REFERENCES ebook (id),
  FOREIGN KEY (subject_id) REFERENCES subject (id)
);

CREATE TABLE format_ebook (
  format_id varchar (255) ,
  ebook_id varchar (255) ,
  PRIMARY KEY (format_id, ebook_id),
  FOREIGN KEY (ebook_id) REFERENCES ebook (id),
  FOREIGN KEY (format_id) REFERENCES format (id)
);
