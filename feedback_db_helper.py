import os
import sqlite3


class FeedbackDBHelper:
    def __init__(self, dbname="feedback_db.sqlite", abs_path=None):
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
        stmt = "CREATE TABLE IF NOT EXISTS userFeedback (id text, target text, unwanted bit, time int)"
        self.conn.execute(stmt)
        self.conn.commit()

    
    def add_feedback(self, chat_id, target, unwanted, time):
        self.delete_feedback(chat_id, target)
        stmt = "INSERT INTO userFeedback (id, target, unwanted, time) VALUES (?,?,?,?)"
        args = (chat_id, target, unwanted, time)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_feedback(self, id, target):
        stmt = "DELETE FROM userFeedback WHERE id = (?) AND target = (?)"
        args = (id, target)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_time_by_target_and_chat_id(self, chat_id, target):
        stmt = "SELECT time FROM userFeedback where target = (?) AND id = (?) order by time DESC limit 1"
        args = (target, chat_id)
        cursor = self.conn.execute(stmt, args)
        ret = cursor.fetchone()
        if ret is None:
            return None
        return ret[0]

    def get_max_time(self):
        stmt = "SELECT time FROM userFeedback order by time DESC limit 1"
        args = ()
        cursor = self.conn.execute(stmt, args)
        ret = cursor.fetchone()
        if ret is None:
            return None
        return ret[0]

    def get_diff(self, timestamp):
        stmt = "SELECT * FROM userFeedback where time>(?)"
        args = (timestamp,)
        return [[x[0],x[1],x[2], x[3]] for x in self.conn.execute(stmt,args)]

    def apply_diff(self, diff):
        for elem in diff:
            self.add_feedback(elem[0],elem[1],elem[2],elem[3])

    def print(self):
        stmt = "SELECT * FROM userFeedback " 
        for x in self.conn.execute(stmt):
            print(x[0],x[1],x[2],x[3]) 

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

