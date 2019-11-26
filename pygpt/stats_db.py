"""
Tools to store the statics in a centralized db
"""
import argparse
import os
import time
import sys
import sqlite3

import report_utils as ru
import gpt_utils as ut


class _DBAdaptor:
    """
    Generic DB Adaptor
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.__db__ = None
        self.__cursor__ = None

    def open(self):
        """
        Open Database
        """
        return False

    def close(self):
        """
        Close Database
        """
        return False

    def get_tag_id(self, tag_name):
        """
        Get tag id from tag name.
        """
        pass

    def create_job_entry(self, job, branch, tag_id, test_sets):
        """
        Create job entry in the db.

        Parameters:
        -----------
         - job: job number
         - branch: branch name
         - tag_id: docker tag id
         - test_sets: test sets executed in the job
        """
        pass



class _SQLiteAdaptor(_DBAdaptor):
    def __init__(self, db_path, locker=True, max_wait=600):
        _DBAdaptor.__init__(self, db_path)
        self.locker = locker
        if self.locker:
            self.__locker_path__ = self.db_path+'.lock' # lock file path
            self.__max_t__ = max_wait # max wait time in sec
        
    def open(self):
        if self.__db__ is not None:
            return True
        if self.locker:
            counter = 0
            # check if db is locked and wait for freeing
            while os.path.exists(self.__locker_path__) and counter < self.__max_t__:
                counter += 1
                ut.log('wating for unlocking SQLite DB')
                time.sleep(1) # wait 1 second every time
            # check if duration 
            if counter >= self.__max_t__:
                ut.error(f'the sqlite DB is still locked after {self.__max_t__} seconds.')
                sys.exit(1)
                return False
            # lock db
            os.mknod(self.__locker_path__)
        ut.log(f"connecting to db: {self.db_path}")
        # connect to db
        self.__db__ = sqlite3.connect(self.db_path)
        self.__cursor__ = self.__db__.cursor()
        self.__db_init__()
        return True

    def close(self):
        if self.__db__ is None:
            return True

        ut.log(f"disconnecting to db: {self.db_path}")
        self.__db__.commit()
        self.__db__.close()
        self.__db__ = None
        self.__cursor__ = None

        if self.locker:
            # remove locker
            os.remove(self.__locker_path__)
        return True
    
    def __db_init__(self):
        query = 'SELECT * FROM dockerTags;'
        try:
            self.__cursor__.execute(query)
        except sqlite3.OperationalError:
            query = '''CREATE TABLE dockerTags(
                ID INTEGER PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE);
            '''
            self.__cursor__.execute(query)
        
        query = 'SELECT * FROM jobs;'
        try:
            self.__cursor__.execute(query)
        except sqlite3.OperationalError:
            query = '''CREATE TABLE jobs(
                ID INTEGER PRIMARY KEY,
                branch VARCHAR(64) NOT NULL,
                jobnum INTEGER NOT NULL,
                dockerTag INTEGER NOT NULL,
                timestamp_start DATETIME NOT NULL,
                timestamp_end DATETIME NOT NULL,
                result INTEGER NOT NULL
            );
            '''

    def get_tag_id(self, tag_name):
        if self.__db__ is None:
            ut.panic('DB not connected')
        query = f"select ID from dockerTags where name='{tag_name}';"
        
        self.__cursor__.execute(query)
        res = self.__cursor__.fetchone()
        
        if res is None:
            query = f"insert into dockerTags (name) values ('{tag_name}');"
            self.__cursor__.execute(query)
            return self.get_tag_id(tag_name)

        return res[0]

    def create_job_entry(self, job, branch, tag_id, test_sets):
        start_date = min([test_set.start_date() for test_set in test_sets])
        end_date = max([test_set.end_date() for test_set in test_sets])
        print(start_date, end_date)

        
def __args__():
    """
    parse arguments passed by the command line
    """
    # setup arg parser
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path', help='DB path')
    parser.add_argument('tag_name', help='Docker Tag Name')
    parser.add_argument('test_scope', help='Test scope')
    parser.add_argument('base_path', help='Report base path')
    parser.add_argument('job', help='Job number')
    parser.add_argument('branch', help='Test Branch')

    parser.add_argument('--adaptor', default='sqlite',
                        choices=['sqlite'], 
                        help='DB adaptor (sqlite, mysql)')    
    # parse arguments
    return parser.parse_args()


def __main__():
    """
    Script main entry point.
    """
    args = __args__()
    adaptor = None
    if args.adaptor == 'sqlite':
        adaptor = _SQLiteAdaptor(args.db_path)

    if adaptor is None:
        ut.error('no DB adapotor found')
        sys.exit(1)

    adaptor.open()
    try:
        test_sets = ru.get_test_sets(args.base_path)
        tag_id = adaptor.get_tag_id(args.tag_name)
        adaptor.create_job_entry(args.job, args.branch, tag_id, test_sets)
    finally:
        adaptor.close()


if __name__ == '__main__':
    __main__()