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
__data_files__ = "singleTestData.txt"

# tags
__RELEASE_TAG__ = 'release'
__WEEKLY_TAG__ = 'weekly'
__DAILY_TAG__ = 'daily'
__REGULAR_TAG__ = 'regular'

def get_parent(path):
    """returns parent directory for files"""
    if os.path.isfile(path):
        return fs.path.dirname(path)
    else:
        return path

def __create_test_json_list__(test_path, data_files_path):
    """creates files containing list of tests data for a given test"""
    test_data = []
    for path in [test_path]:
        with open(path, 'r') as test_file:
            tests = json.load(test_file)
            for test in tests:
                if 'inputs' in test:
                    for input in list(test['inputs']):
                        if test['inputs'][input] not in test_data:
                            test_data.append(get_parent(test['inputs'][input]))
    with open(data_files_path, 'w') as file:
        file.write('\n'.join(test_data))
    return True


def __arguments__():
    """
    parse arguments passed by the command line
    """
    # setup arg parser
    parser = argparse.ArgumentParser()

    parser.add_argument('test_path',
                        help="test file path")

    parser.add_argument('output_folder',
                        help="output folder path")

    # parse arguments
    return parser.parse_args()


def __main__():
    """main entry point of the script"""
    args = __arguments__()

    if not os.path.exists(args.test_path):
        log.error("test path does not exist")
        sys.exit(1)

    if not os.path.exists(args.output_folder):
        log.error("output folder does not exist")
        sys.exit(1)
    data_file = os.path.join(args.output_folder, __data_files__)

    if __create_test_json_list__(args.test_path, data_file):
        log.success(f"filtered test data list created in {data_file}")


if __name__ == '__main__':
    # execute entry point
    __main__()
