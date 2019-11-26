"""
Tests the integrity of the jsons test files
"""
import argparse
import json
import os
import sys

import gpt_utils as ut

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
        ut.error("test folder does not exist")
        sys.exit(1)
    # cretas files containing list of all json files
    test_files = ut.rlist_files(args.test_folder, lambda f: f.endswith('.json'))
    tests = {}
    status = True
    for test_file in test_files:
        for test_id in __get_ids__(test_file):
            if test_id in tests:
                ut.error(f'duplicate test id:\n\t{test_id} is defined in `{tests[test_id]}` and in `{test_file}`')
                status = False
            else:
                tests[test_id] = test_file
    if status:
        ut.success('no duplicated test ids found')
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    __main__()