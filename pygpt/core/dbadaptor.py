"""
DBAdaptor provides an easy access to the perfomances database.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import os
import time
import sys
import sqlite3
import pymysql

from functools import wraps

import core.log as log


class DBAdaptor:
    """
    Generic DB Adaptor
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.__db__ = None
        self.__cursor__ = None

    def open(self):
        """
        Opens Database
        """
        return False

    def close(self):
        """
        Closes Database
        """
        return False

    def docker_tag_id(self, tag_name):
        """
        Gets tag id from tag name.
        """
        query = f"SELECT ID FROM dockerTags WHERE name='{tag_name}';"
        res = self.execute(query)
        if not res:
            log.info(f'inserting dockerTag `{tag_name}` into DB')
            query = f"INSERT INTO dockerTags (name) VALUES ('{tag_name}');"
            self.execute(query)
            return self.docker_tag_id(tag_name)

        return res[0][0]

    def test_id(self, test_name):
        """
        Gets db test id from test name
        """
        res = self.execute(f"SELECT ID FROM tests WHERE name='{test_name}'")
        if res:
            return res[0][0]
        return None


    def create_job_entry(self, job, branch, test_scope, tag_id, test_sets):
        """
        Creates job entry in the db.

        Parameters:
        -----------
         - job: job number
         - branch: branch name
         - test_scope: test scope tag
         - tag_id: docker tag id
         - test_sets: test sets executed in the job
        """
        query = f'SELECT ID FROM jobs WHERE branch="{branch}" AND jobnum={job};'
        res = self.execute(query)

        if not res:

            query = f'SELECT (MAX(ID)+1) AS id FROM jobs;'
            new_id = self.execute(query)[0]['id']
            start_date = min([test_set.start_date for test_set in test_sets])
            end_date = max([test_set.end_date for test_set in test_sets])
            result = all([not ts.is_failed() for ts in test_sets])
            log.info(f'inserting job `{job}` into DB')
            add_query = f'''INSERT INTO jobs (
                ID,
                branch,
                jobnum,
                dockerTag,
                testScope,
                timestamp_start,
                timestamp_end,
                result
            ) VALUES (
                {new_id}, {branch}, {job}, {tag_id}, {test_scope}, {start_date}, {end_date}, {1 if result else 3}
            );'''
            self.execute(add_query)
            res = self.execute(query)
            if not res:
                log.panic('impossible to add job')
        job_id = res[0]['ID']
        for test_set in test_sets:
            for test in test_set.tests:
                test_id = self.test_entry(test, test_set.name)
                self.create_result_entry(job_id, test_id, test)

    def test_entry(self, test, parent_set):
        """
        Gets ID of a test entry. If does not exists create a new test entry.

        Parameters:
        -----------
         - test: test object
         - parent_set: parent json test set name

        Returns:
        --------
        test entry ID
        """
        name = test.name
        query = f'SELECT ID FROM tests WHERE name="{name}"'
        res = self.execute(query)
        if not res:
            log.info(f'inserting test `{name}`')
            query = f'''INSERT INTO tests (
                name,
                testset,
                description,
                author,
                frequency,
                graphPath,
                graphXML
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            );'''
            print(test.graph_xml)
            print(query)
            self.execute(query, (name, parent_set, test.description,
                                 test.author, test.frequency, 
                                 test.graph_path, test.graph_xml))
            return self.test_entry(test, parent_set)
        return res[0]['ID']

    def create_result_entry(self, job_id, test_id, test):
        """
        Inserting a performance result entry for a givent test and given run.

        Parameters:
        -----------
         - job_id: db job id
         - test_id: db test id
         - test: test object
        """
        if not test.has_statistics():
            log.warning(f'test `{test.name}` has no statistics')
            return
        query = 'SELECT * FROM results WHERE job=%s AND test=%s'
        res = self.execute(query, (job_id, test_id))
        if not res:
            log.info(f'inserting results for test `{test.name}`')
            result = 1
            if test.is_crashed():
                result = 4
            elif test.is_failed():
                result = 3
            elif test.is_skipped():
                result = 2
            query = f'''INSERT INTO results (
                test, job, result,
                start, duration, cpu_time,
                cpu_usage_avg, cpu_usage_max, memory_avg,
                memory_max, io_write, io_read,
                threads_avg, threads_max,
                raw_data, output
            ) VALUES (
                {test_id}, {job_id}, {result},
                '{test.start}', {test.duration}, {test.cpu_time},
                {test.cpu_usage_avg}, {test.cpu_usage_max}, {test.memory_avg},
                {test.memory_max}, {test.io_read}, {test.io_write}, 
                {int(test.threads_avg)}, {test.threads_max},
                %s, %s);'''
            self.execute(query, (test.raw_profile(), test.stdout))

    def execute(self, query, *args):
        """
        Executes a query

        Parameters:
        -----------
         - query: SQL query
         - args: additional arguments

        Returns:
        --------
        all results found
        """
        return []

    def values(self, test, docker_tag, value_tag, last_n=None):
        """
        Retrive average value for a specific performance information
        """
        docker_id = self.docker_tag_id(docker_tag)
        test_id = self.test_id(test)

        query = f'''SELECT {value_tag} FROM results
            WHERE test={test_id} and job in
                (SELECT ID FROM jobs
                WHERE dockerTag={docker_id})
            ORDER BY start DESC'''
        if last_n is not None:
            query += f' LIMIT {last_n}'
        res = self.execute(query)
        return list([x[value_tag] for x in res])

    def reference_value(self, test, value_tag):
        """
        Retrive reference value.
        """
        test_id = self.test_id(test)

        query = f'''SELECT {value_tag} FROM reference_values
            WHERE test={test_id}'''
        res = self.execute(query)
        if res:
            return res[0][value_tag]
        return None



def ensure_connection(func):
    """
    ensure connection decroator
    """
    @wraps(func)
    def inner(*args, **kwargs):
        if args[0].__db__ is None:
            log.panic('DB not connected')
        return func(*args, **kwargs)
    return inner


class MySQLAdaptor(DBAdaptor):
    """MySQL adaptor."""
    def __init__(self, db_path):
        DBAdaptor.__init__(self, db_path)
        self.user, self.password = db_path.split('@')[0].split(':')
        self.dbname = db_path.split('@')[1].split('/')[1]
        self.host, self.port = db_path.split('@')[1].split('/')[0].split(':')

    def open(self):
        if self.__db__ is not None:
            return True
        log.info(f"connecting to db: {self.host}:{self.port}/{self.dbname}")
        self.__db__ = pymysql.connect(
            host=self.host,
            port=int(self.port),
            user=self.user,
            password=self.password,
            db=self.dbname,
            cursorclass=pymysql.cursors.DictCursor
        )
        return True

    def close(self):
        if self.__db__ is None:
            return True
        log.info(f"disconnecting to db: {self.host}:{self.port}/{self.dbname}")
        self.__db__.commit()
        self.__db__.close()
        self.__db__ = None
        self.__cursor__ = None
        return True

    @ensure_connection
    def execute(self, query, *args):
        with self.__db__.cursor() as cursor:
            cursor.execute(query, *args)
            res_list = cursor.fetchall()
        return res_list

    def docker_tag_id(self, tag_name):
        """
        Gets tag id from tag name.
        """
        query = f"SELECT ID FROM dockerTags WHERE name='{tag_name}';"
        res = self.execute(query)
        if not res:
            log.info(f'inserting dockerTag `{tag_name}` into DB')
            query = f"INSERT INTO dockerTags (name) VALUES ('{tag_name}');"
            self.execute(query)
            return self.docker_tag_id(tag_name)
        return res[0]['ID']

    def test_id(self, test_name):
        """
        Gets db test id from test name
        """
        res = self.execute(f"SELECT ID FROM tests WHERE name='{test_name}'")
        if res:
            return res[0]['ID']
        return None


class SQLiteAdaptor(DBAdaptor):
    """SQLite3 Adaptor."""
    def __init__(self, db_path, locker=True, max_wait=600):
        DBAdaptor.__init__(self, db_path)
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
                log.info('wating for unlocking SQLite DB')
                time.sleep(1) # wait 1 second every time
            # check if duration
            if counter >= self.__max_t__:
                log.error(f'the sqlite DB is still locked after {self.__max_t__} seconds.')
                sys.exit(1)
                return False
            # lock db
            with open(self.__locker_path__, 'w') as file:
                file.write('locked')
        log.info(f"connecting to db: {self.db_path}")
        # connect to db
        self.__db__ = sqlite3.connect(self.db_path)
        self.__cursor__ = self.__db__.cursor()
        self.__db_init__()
        return True

    def close(self):
        if self.__db__ is None:
            return True

        log.info(f"disconnecting to db: {self.db_path}")
        self.__db__.commit()
        self.__db__.close()
        self.__db__ = None
        self.__cursor__ = None

        if self.locker:
            # remove locker
            os.remove(self.__locker_path__)
        return True


    def __table_exists__(self, table):
        query = f'SELECT * FROM {table};'
        try:
            self.__cursor__.execute(query)
            return True
        except sqlite3.OperationalError:
            return False

    @ensure_connection
    def __db_init__(self):
        if not self.__table_exists__('dockerTags'):
            log.info('creating table `dockerTags`')
            query = '''CREATE TABLE dockerTags(
                ID INTEGER PRIMARY KEY,
                name VARCHAR(64) NOT NULL UNIQUE);
            '''
            self.__cursor__.execute(query)

        if not self.__table_exists__('resultTags'):
            log.info('creating table `resultTags`')
            query = '''CREATE TABLE resultTags (
                ID INTEGER PRIMARY KEY,
                tag VARCHAR(64) NOT NULL UNIQUE,
                fatal BOOLEAN NOT NULL
            );'''
            self.__cursor__.execute(query)
            query = 'INSERT INTO resultTags (ID, tag, fatal) VALUES (1, "SUCCESS", 0);'
            self.__cursor__.execute(query)
            query = 'INSERT INTO resultTags (ID, tag, fatal) VALUES (2, "SKIPPED", 0);'
            self.__cursor__.execute(query)
            query = 'INSERT INTO resultTags (ID, tag, fatal) VALUES (3, "FAILED", 1);'
            self.__cursor__.execute(query)
            query = 'INSERT INTO resultTags (ID, tag, fatal) VALUES (4, "CRASHED", 1);'
            self.__cursor__.execute(query)

        if not self.__table_exists__('jobs'):
            log.info('creating table `jobs`')
            query = '''CREATE TABLE jobs(
                ID INTEGER PRIMARY KEY,
                branch VARCHAR(64) NOT NULL,
                jobnum INTEGER NOT NULL,
                dockerTag INTEGER NOT NULL,
                testScope VARCHAR (128) NOT NULL,
                timestamp_start DATETIME NOT NULL,
                timestamp_end DATETIME NOT NULL,
                result INTEGER NOT NULL,
                FOREIGN KEY (dockerTag) REFERENCES dockerTags(ID),
                FOREIGN KEY (result) REFERENCES resultTags(ID),
                CONSTRAINT UQ_job UNIQUE (
                    branch, jobnum
                )
            );
            '''
            self.__cursor__.execute(query)

        if not self.__table_exists__('tests'):
            log.info('creating table `tests`')
            query = '''CREATE TABLE tests (
                ID INTEGER PRIMARY KEY,
                name VARCHAR(256) NOT NULL UNIQUE,
                testset VARCHAR(256) NOT NULL,
                description VARCHAR(256) NOT NULL,
                author VARCHAR(256) NOT NULL,
                frequency VARCHAR(256) NOT NULL,
                graphPath VARCHAR(256) NOT NULL,
                graphXML BLOB,
            );
            '''
            self.__cursor__.execute(query)

        if not self.__table_exists__('results'):
            log.info('creating table `results`')
            query = '''CREATE TABLE results (
                ID INTEGER PRIMARY KEY,
                test INTEGER NOT NULL,
                job INTEGER NOT NULL,
                result INTEGER NOT NULL, -- SUCCESS/SKIPPED/ERROR
                start DATETIME NOT NULL,
                duration INTEGER NOT NULL, -- in seconds
                cpu_time INTEGER NOT NULL, -- in seconds
                cpu_usage_avg INTEGER NOT NULL, -- percentage
                cpu_usage_max INTEGER NOT NULL, -- percentage
                memory_avg INTEGER NOT NULL, -- in Mb
                memory_max INTEGER NOT NULL, -- in Mb
                io_write INTEGER NOT NULL, -- counter
                io_read INTEGER NOT NULL, -- counter
                threads_avg INTEGER NOT NULL, -- counter
                threads_max INTEGER NOT NULL, -- counter
                raw_data BLOB NOT NULL,
                output BLOB,
                FOREIGN KEY (test) REFERENCES tests(ID),
                FOREIGN KEY (job) REFERENCES jobs(ID),
                FOREIGN KEY (result) REFERENCES resultTags(ID),
                CONSTRAINT UQ_test UNIQUE (
                    test, job
                )
            );'''
            self.__cursor__.execute(query)

        if not self.__table_exists__('referenceTags'):
            log.info('creating table `referenceTags`')
            query = '''CREATE TABLE referenceTags (
                ID INTEGER PRIMARY KEY,
                tag VARCHAR(64) NOT NULL UNIQUE
            );'''
            self.__cursor__.execute(query)
            query = '''INSERT INTO referenceTags (ID, tag) VALUES (1, "default");'''
            self.__cursor__.execute(query)

        if not self.__table_exists__('reference_values'):
            query = '''CREATE TABLE reference_values (
                ID INTEGER PRIMARY KEY,
                test INTEGER NOT NULL,
                referenceTag INTEGER NOT NULL DEFAULT 1,
                updated DATETIME NOT NULL,
                duration INTEGER NOT NULL, -- in seconds
                cpu_time INTEGER NOT NULL, -- in seconds
                cpu_usage_avg INTEGER NOT NULL, -- percentage
                cpu_usage_max INTEGER NOT NULL, -- percentage
                memory_avg INTEGER NOT NULL, -- in Mb
                memory_max INTEGER NOT NULL, -- in Mb
                io_write INTEGER NOT NULL, -- counter
                io_read INTEGER NOT NULL, -- counter
                threads_avg INTEGER NOT NULL, -- counter
                threads_max INTEGER NOT NULL, -- counter
                raw_data BLOB NOT NULL,
                FOREIGN KEY (test) REFERENCES tests(ID),
                FOREIGN KEY (referenceTag) REFERENCES referenceTags(ID),
                CONSTRAINT UQ_reference UNIQUE (
                    test, referenceTag
                )
            );'''
            self.__cursor__.execute(query)


    @ensure_connection
    def execute(self, query, *args):
        try:
            self.__cursor__.execute(query, *args)
        except sqlite3.OperationalError as exc:
            log.error(f'SQL query `{query}` malformed')
            raise exc
        res_list = []
        res = self.__cursor__.fetchone()
        while res is not None:
            res_list.append(res)
            res = self.__cursor__.fetchone()
        return res_list


def adaptor(db_path):
    """
    Retrives adaptor for the given db.

    Parametrs:
    ----------
     - db_path: path to the database

    Returns:
    --------
    return db adaptor
    """
    if '://' in db_path:
        mode = db_path.split('://')[0]
        path = db_path.split('://')[1]
    else:
        # ensuring back compatibility with old syntax
        mode = 'sqlite'
        path = db_path

    #if mode == 'sqlite':
    #    return SQLiteAdaptor(path)
    if mode == 'mysql':
        return MySQLAdaptor(path)
    if mode == 'conf':
        with open(path, 'r') as file:
            db_path = file.readline().replace('\n', '')
            return adaptor(db_path)
    print(f'Database mode {mode} not supported')
    sys.exit(0)
