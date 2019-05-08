import sqlite3


class DBHelper:
    def __init__(self, dbname="todo.sqlite",):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def connect(self):
        self._setup_feedback()
        self._setup_rel()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _setup_rel(self):
        stmt = "CREATE TABLE IF NOT EXISTS userRel (device text, id text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def _setup_feedback(self):
        stmt = "CREATE TABLE IF NOT EXISTS userFeedback (id text, target text, unwanted bit)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_user(self, device, id):
        delete_user(device,id)
        stmt = "INSERT INTO userRel (device, id) VALUES (?,?)"
        args = (device, id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_user(self, device, id):
        stmt = "DELETE FROM userRel WHERE device = (?) AND id = (?)"
        args = (device, id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_feedback(self, id, target, unwanted):
        self.delete_user(id, target)
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
        args = device
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_feedback_by_target(self, target):
        stmt1 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 1 group by target"
        stmt2 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 0 group by target"
        args = target
        cursor1 = self.conn.execute(stmt1, args)
        cursor2 = self.conn.execute(stmt2, args)
        if cursor1.fetchone() is None or cursor2.fetchone() is None:
            return None
        return self.conn.execute(stmt1, args).fetchone()[0], self.conn.execute(stmt2, args).fetchone()[0]
