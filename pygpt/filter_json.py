"""
Filter JSON:
filters json files using a given test scope.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
"""
import argparse
import os
import sys
import json

import core.tools as utils
import core.log as log

from core.models import TestScope

__test_files__ = "JSONTestFiles.txt"

# tags
__RELEASE_TAG__ = 'release'
__WEEKLY_TAG__ = 'weekly'
__DAILY_TAG__ = 'daily'
__REGULAR_TAG__ = 'regular'


def __create_test_json_list__(test_folder, scope, test_files_path):
    """cretas files containing list of tests to execute for a given scope"""
    test_files = utils.rlist_files(test_folder, lambda f: f.endswith('.json'))
    test_list = ''
    scope = TestScope.init(scope)
    for test_path in test_files:
        with open(test_path, 'r') as test_file:
            tests = json.load(test_file)
            for test in tests:
                if 'frequency' in test:
                    if TestScope.compatibleN(scope, test['frequency']):
                        test_list += f'{test_path}\n'
    with open(test_files_path, 'w') as file:
        file.write(test_list)
    return True


def __arguments__():
    """
    parse arguments passed by the command line
    """
    # setup arg parser
    parser = argparse.ArgumentParser()

    parser.add_argument('test_folder',
                        help="test folder path")

    parser.add_argument('scope',
                        help="test scope")

    parser.add_argument('output_folder',
                        help="output folder path")

    # parse arguments
    return parser.parse_args()


def __main__():
    """main entry point of the script"""
    args = __arguments__()

    if not os.path.exists(args.test_folder):
        log.error("test folder does not exist")
        sys.exit(1)
    if not os.path.exists(args.output_folder):
        log.error("output folder does not exist")
        sys.exit(1)
    json_test_files = os.path.join(args.output_folder, __test_files__)

    if __create_test_json_list__(args.test_folder, args.scope, json_test_files):
        log.success(f"filtered JSON created in {json_test_files}")


if __name__ == '__main__':
    # execute entry point
    __main__()
