
import sqlite3
import queue

from dotenv import dotenv_values
config = dotenv_values("opt.env")
DB_USERBASE_TABLE_NAME = config['DB_USERBASE_TABLE_NAME']
DB_DEVICES_TABLE_NAME = config['DB_DEVICES_TABLE_NAME']
DB_BASE_NAME = config['DB_FILENAME']

class ConnectionPool:

  def __init__(self, database, max_connections=10):
    self.database = database
    self.max_connections = max_connections
    self.connections = queue.Queue(maxsize=max_connections)
    for i in range(max_connections):
      self.connections.put(sqlite3.connect(database, check_same_thread=False))

  def get_connection(self):
    return self.connections.get()

  def return_connection(self, conn):
    self.connections.put(conn)

  def __enter__(self):
    self.conn = self.get_connection()
    return self.conn

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_val is not None:
      self.conn.rollback()
    else:
      self.conn.commit()
    self.return_connection(self.conn)


pool = ConnectionPool(DB_BASE_NAME)

with pool.get_connection() as conn:
  cursor = conn.cursor()
  cursor.execute(
    f"CREATE TABLE IF NOT EXISTS {DB_USERBASE_TABLE_NAME} (device_id BIGINT NOT NULL UNIQUE PRIMARY KEY, user_id INTEGER, tag STRING)"
  )

  cursor.execute(
    f"CREATE TABLE IF NOT EXISTS {DB_DEVICES_TABLE_NAME} (device_id BIGINT NOT NULL UNIQUE PRIMARY KEY, address STRING)"
  )
  conn.commit()


def append_device(user_id : int, device_id : int, tag=""):
  with pool.get_connection() as conn:
    cursor = conn.cursor()
    
    #check in devices table
    sql_req = f"SELECT EXISTS(SELECT 1 FROM {DB_DEVICES_TABLE_NAME} WHERE device_id = {device_id}) LIMIT 1"
    cursor.execute(sql_req)
    check = cursor.fetchone()

    if check[0] != 0:
      if is_exist(user_id, device_id, tag):
        return False
      else:
        cursor.execute(
          f"INSERT INTO {DB_USERBASE_TABLE_NAME} (device_id, user_id, tag) VALUES(?, ?, ?)",
          (device_id, user_id, tag))
        conn.commit()
        return True
    return False


def is_exist(user_id=0, device_id=0, tag=''):
  with pool.get_connection() as conn:
    cursor = conn.cursor()

    sql_req = f"SELECT EXISTS(SELECT 1 FROM {DB_USERBASE_TABLE_NAME} WHERE user_id = {user_id} AND (device_id = {device_id} OR tag = '{tag}')) LIMIT 1"
    cursor.execute(sql_req)
    check = cursor.fetchone()

    if check[0] != 0:
      return True
    return False


def get_devices(user_id : int):
  with pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {DB_USERBASE_TABLE_NAME} WHERE user_id = ?",
                   (user_id, ))
    devices = cursor.fetchall()
    return devices

def get_device_by_tag(user_id : int, tag : str):
  with pool.get_connection() as conn:
    cursor = conn.cursor()
    sql_req = f"SELECT device_id FROM {DB_USERBASE_TABLE_NAME} WHERE user_id = {user_id} AND tag = '{tag}'"
    cursor.execute(sql_req)
    device_id = cursor.fetchone()
    return device_id[0]

def delete_device_by_ID(device_id : int):
  if device_id != 0:
    with pool.get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute(
        f"DELETE FROM {DB_USERBASE_TABLE_NAME} WHERE device_id = ?",
        (device_id, ))
      conn.commit()
      return True
  else:
    return False


def delete_device_by_TAG(tag : str):
  if tag != '':
    with pool.get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute(f"DELETE FROM {DB_USERBASE_TABLE_NAME} WHERE tag = ?",
                     (tag, ))
      conn.commit()
      return True
  else:
    return False
