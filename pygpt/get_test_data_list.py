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


def __create_test_json_list__(test_path, data_files_path):
    """creates files containing list of tests data for a given test"""
    test_files = [test_path]
    test_list = []
    test_data = []
    for test_path in test_files:
        with open(test_path, 'r') as test_file:
            tests = json.load(test_file)
            for test in tests:
                if test_path not in test_list:
                    test_list.append(test_path)
                if 'inputs' in test:
                    if 'input' in test['inputs']:
                        if test['inputs']['input'] not in test_data:
                            test_data.append(test['inputs']['input'])
                            if test['inputs']['input'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input'])[0] + '.data')
                    if 'input1' in test['inputs']:
                        if test['inputs']['input1'] not in test_data:
                            test_data.append(test['inputs']['input1'])
                            if test['inputs']['input1'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input1'])[0] + '.data')
                    if 'input2' in test['inputs']:
                        if test['inputs']['input2'] not in test_data:
                            test_data.append(test['inputs']['input2'])
                            if test['inputs']['input2'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input2'])[0] + '.data')
                    if 'input3' in test['inputs']:
                        if test['inputs']['input3'] not in test_data:
                            test_data.append(test['inputs']['input3'])
                            if test['inputs']['input3'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input3'])[0] + '.data')
                    if 'input4' in test['inputs']:
                        if test['inputs']['input4'] not in test_data:
                            test_data.append(test['inputs']['input4'])
                            if test['inputs']['input4'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input4'])[0] + '.data')
                    if 'input5' in test['inputs']:
                        if test['inputs']['input5'] not in test_data:
                            test_data.append(test['inputs']['input5'])
                            if test['inputs']['input5'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input5'])[0] + '.data')
                    if 'input6' in test['inputs']:
                        if test['inputs']['input6'] not in test_data:
                            test_data.append(test['inputs']['input6'])
                            if test['inputs']['input6'].endswith('.dim'):
                                test_data.append(os.path.splitext(test['inputs']['input6'])[0] + '.data')
                # test_list += f'{test_path}\n'
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
