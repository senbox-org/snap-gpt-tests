"""
Chek jsons:
Checks the integrity of the jsons test files and unicity of test IDs.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import argparse
import json
import os
import sys

import core.log as log
import core.tools as utils

def __args__():
    """
    Args parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('test_folder',
                        help="test folder path")
    # parser
    return parser.parse_args()


def __get_ids__(test_file):
    """
    get list of test id
    """
    with open(test_file) as file:
        tests = json.load(file)
        ids = []
        for test in tests:
            if 'id' in test:
                ids.append(test['id'])
        return ids
    return None


def __main__():
    """
    main entry point
    """
    args = __args__()
    if not os.path.exists(args.test_folder):
        log.error("test folder does not exist")
        sys.exit(1)
    # list containing all json files in all sub directories
    test_files = utils.rlist_files(args.test_folder, lambda f: f.endswith('.json'))
    tests = {}
    status = True
    for test_file in test_files:
        for test_id in __get_ids__(test_file):
            if test_id in tests:
                log.error(f'duplicate test id:\n\t{test_id} is defined in `{tests[test_id]}` and in `{test_file}`')
                status = False
            else:
                tests[test_id] = test_file
    if status:
        log.success('no duplicated test ids found')
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    __main__()