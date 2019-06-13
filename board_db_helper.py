import os
import sqlite3


class BoardDBHelper:
    def __init__(self, dbname="board_db.sqlite", abs_path=None):
        self.dbname = dbname
        if abs_path is None:
            self.conn = sqlite3.connect(dbname)
        else:
            self.conn = sqlite3.connect(os.path.join(abs_path, dbname))

    def connect(self):
        self._setup_rel()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _setup_rel(self):
        stmt = "CREATE TABLE IF NOT EXISTS userRel (device text, device_name text, id text)"
        self.conn.execute(stmt)
        self.conn.commit()



    def add_user(self, device, device_name, id):
        self.delete_user_by_id(device, id)
        stmt = "INSERT INTO userRel (device,device_name, id) VALUES (?,?,?)"
        args = (device, device_name, id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_user_by_id(self, device, id):
        stmt = "DELETE FROM userRel WHERE device = (?) AND id = (?)"
        args = (device, id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_user_by_id_and_device_name(self, device_name, id):
        stmt = "DELETE FROM userRel WHERE id = (?) AND device_name=(?)"
        args = (id, device_name)
        self.conn.execute(stmt, args)
        self.conn.commit()


    def get_devices(self):
        stmt = "SELECT device FROM userRel"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_chatID_by_device(self, device):
        stmt = "SELECT DISTINCT id FROM userRel where device = (?)"
        args = (device,)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_device_names_by_chatID(self, id):
        stmt = "SELECT DISTINCT device_name FROM userRel where id = (?)"
        args = (id,)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_device_name_by_chatID_and_device(self, id, device):
        stmt = "SELECT DISTINCT device_name FROM userRel where id = (?) AND device= (?)"
        args = (id, device)
        cursor = self.conn.execute(stmt, args).fetchone()
        if cursor is None:
            return None
        return cursor[0]