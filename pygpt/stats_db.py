"""
Stats DB:
Archives the performance profiles of the GPT tests into a centrilized DB

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import argparse
import sys

import report_utils as ru
import core.log as log
import core.dbadaptor as db



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
    # parse arguments
    return parser.parse_args()


def __main__():
    """
    Script main entry point.
    """
    args = __args__()
    adaptor = db.adaptor(args.db_path)

    if adaptor is None:
        log.error('no DB adapotor found')
        sys.exit(1)
    try:
        adaptor.open()
        log.info("Database openned")
        log.debug(args)
        test_sets = ru.get_test_sets(args.base_path)
        tag_id = adaptor.docker_tag_id(args.tag_name)
        adaptor.create_job_entry(args.job, args.branch, args.test_scope, tag_id, test_sets)
    finally:
        adaptor.close()


if __name__ == '__main__':
    __main__()
