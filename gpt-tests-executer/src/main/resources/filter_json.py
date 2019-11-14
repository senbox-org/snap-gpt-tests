"""filter json files"""
import argparse
import os
import sys
import json


__test_files__ = "JSONTestFiles.txt"
__test_sequence__ = "JSONTestFilesSeq.txt"

# tags
__RELEASE_TAG__ = 'release'
__WEEKLY_TAG__ = 'weekly'
__DAILY_TAG__ = 'daily'


def __compatible__(scope, tags):
    """check if the tags are compatible with the current test scope"""
    if scope in tags:
        return True
    if scope == __RELEASE_TAG__:
        return __WEEKLY_TAG__ in tags or __DAILY_TAG__ in tags
    if scope == __WEEKLY_TAG__:
        return __DAILY_TAG__ in tags
    return False


def __create_test_json_list__(test_folder, scope, test_files_path, test_sequence_path):
    """cretas files containing list of tests to execute for a given scope"""
    test_files = [os.path.join(test_folder, f) for f in os.listdir(test_folder)
                  if f.endswith('.json')]
    sequence = ''
    parallel = ''
    scope = scope.lower()
    for test_path in test_files:
        with open(test_path, 'r') as test_file:
            tests = json.load(test_file)
            for test in tests:
                tags = list([x.lower() for x in test['frequency'].split('/')])
                if __compatible__(scope, tags):
                    if test['configVM'] is None:
                        parallel += f'{test_path}\n'
                    else:
                        sequence += f'{test_path}\n'
                    break
    with open(test_files_path, 'w') as file:
        file.write(parallel)
    with open(test_sequence_path, 'w') as file:
        file.write(sequence)
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
        print("Test folder does not exist")
        sys.exit(-1)
    if not os.path.exists(args.output_folder):
        print("Output folder does not exist")
        sys.exit(-1)
    json_test_files = os.path.join(args.output_folder, __test_files__)
    json_test_sequence = os.path.join(args.output_folder, __test_sequence__)

    if __create_test_json_list__(args.test_folder, args.scope, json_test_files, json_test_sequence):
        print(f"Filtered JSON created in {json_test_files}")
        print(f"Seq filtered JSON created in {json_test_sequence}")



if __name__ == '__main__':
    # execute entry point
    __main__()
