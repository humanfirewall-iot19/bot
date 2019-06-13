import os
import sqlite3


class FeedbackDBHelper:
    def __init__(self, dbname="tg_db.sqlite", abs_path=None):
        self.dbname = dbname
        if abs_path is None:
            self.conn = sqlite3.connect(dbname)
        else:
            self.conn = sqlite3.connect(os.path.join(abs_path, dbname))

    def connect(self):
        self._setup_feedback()

    def close(self):
        self.conn.commit()
        self.conn.close()


    def _setup_feedback(self):
        stmt = "CREATE TABLE IF NOT EXISTS userFeedback (id text, target text, unwanted bit)"
        self.conn.execute(stmt)
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


    def get_feedback_by_target(self, target):
        stmt1 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 1 group by target"
        stmt2 = "SELECT count(*) FROM userFeedback where target = (?) AND unwanted == 0 group by target"
        args = (target,)
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
