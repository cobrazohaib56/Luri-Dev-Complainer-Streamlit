import sqlite3
from sqlite3 import Error
import hashlib

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        username TEXT PRIMARY KEY,
                                        password TEXT NOT NULL
                                    ); """
        sql_create_chats_table = """ CREATE TABLE IF NOT EXISTS chats (
                                        chatid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        username TEXT NOT NULL,
                                        chatname TEXT NOT NULL,
                                        full_text TEXT,
                                        FOREIGN KEY (username) REFERENCES users (username)
                                    ); """
        sql_create_messages_table = """ CREATE TABLE IF NOT EXISTS messages (
                                        messageid INTEGER PRIMARY KEY AUTOINCREMENT,
                                        chatid INTEGER NOT NULL,
                                        role TEXT NOT NULL,
                                        message TEXT NOT NULL,
                                        FOREIGN KEY (chatid) REFERENCES chats (chatid)
                                    ); """
        cursor = conn.cursor()
        cursor.execute(sql_create_users_table)
        cursor.execute(sql_create_chats_table)
        cursor.execute(sql_create_messages_table)
    except Error as e:
        print(e)

def save_message(conn, chatid, role, message):
    sql = ''' INSERT INTO messages(chatid, role, message)
              VALUES(?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, (chatid, role, message))
    conn.commit()

def load_messages(conn, chatid):
    sql = ''' SELECT role, message FROM messages WHERE chatid=? '''
    cur = conn.cursor()
    cur.execute(sql, (chatid,))
    return [{"role": row[0], "message": row[1]} for row in cur.fetchall()]

def create_chat(conn, username, chatname, full_text):
    sql = ''' INSERT INTO chats(username, chatname, full_text)
              VALUES(?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, (username, chatname, full_text))
    conn.commit()
    return cur.lastrowid

def get_chats(conn, username):
    sql = ''' SELECT chatid, chatname, full_text FROM chats WHERE username=? '''
    cur = conn.cursor()
    cur.execute(sql, (username,))
    return cur.fetchall()

def create_user(conn, username, password):
    sql_check = ''' SELECT COUNT(*) FROM users WHERE username = ? '''
    cur = conn.cursor()
    cur.execute(sql_check, (username,))
    if cur.fetchone()[0] > 0:
        return False  # Username already exists
    
    """ Create a new user in the users table """
    sql = ''' INSERT INTO users(username,password)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (username, hash_password(password)))
    conn.commit()
    return cur.lastrowid

def verify_user(conn, username, password):
    """ Verify a user's login credentials """
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    rows = cur.fetchall()
    return len(rows) == 1

def hash_password(password):
    """ Hash a password for storing. """
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(conn, username):
    sql = ''' SELECT * FROM users WHERE username=? '''
    cur = conn.cursor()
    cur.execute(sql, (username,))
    return cur.fetchone()
