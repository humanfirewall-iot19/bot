import sqlite3


class DBHelper:
    def __init__(self, dbname="todo.sqlite", ):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def connect(self):
        self._setup_feedback()
        self._setup_rel()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _setup_rel(self):
        stmt = "CREATE TABLE IF NOT EXISTS userRel (device text, device_name text, id text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def _setup_feedback(self):
        stmt = "CREATE TABLE IF NOT EXISTS userFeedback (id text, target text, unwanted bit)"
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

    def add_feedback(self, id, target, unwanted):
        self.delete_feedback(id, target)
        stmt = "INSERT INTO userFeedback (id, target, unwanted) VALUES (?,?,?)"
        args = (id, target, unwanted)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_feedback(self, id, target):
        stmt = "DELETE FROM userFeedback WHERE id = (?) AND target = (?)"
        args = (id, target)
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

    def get_feedback_by_target(self, target):
        stmt1 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 1 group by target"
        stmt2 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 0 group by target"
        args = target
        cursor1 = self.conn.execute(stmt1, args)
        cursor2 = self.conn.execute(stmt2, args)
        ret1 = cursor1.fetchone()
        ret2 = cursor2.fetchone()
        if ret1 is None and ret2 is None:
            return None
        elif ret1 is None:
            return 0, ret2[0]
        elif ret2 is None:
            return ret1[0], 0
        else:
            return ret1[0], ret2[0]
