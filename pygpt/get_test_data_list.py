"""
Get test data:
Produce a file listing relative test data for a given json test path.

Author: Frederick BALDO (CS Group) <frederick.baldo@csgroup.eu>
"""
import argparse
import os
import sys
import json
import re
import fs

import core.log as log

# Output file
__data_files__ = "singleTestData.txt"

def get_parent(path):
    """returns parent directory for files"""
    if re.search("(.xml|.XML|.JP2|.zip|.ZIP|.tgz|.NTF|.dim|.DIMA|.h5|.txt|.tif|.TIF|_OC|.N1|.nc|.dbf|.prj|.qix|.shp|.shx|.qpj|.png|.PNG|.jpg|.JPG|.E1|.E2|.001|.safe)$", path):
        return fs.path.dirname(path)
    else:
        return path

def __create_test_json_list__(test_path, data_files_path, testdata_folder):
    """creates files containing list of tests data for a given test"""
    test_data = []
    for path in [test_path]:
        with open(path, 'r') as test_file:
            tests = json.load(test_file)
            for test in tests:
                if 'inputs' in test:
                    for input in list(test['inputs']):
                        folder = get_parent(test['inputs'][input])
                        # TODO Check if folder alreay exist locally
                        if folder not in test_data:
                            if os.access(os.path.join(testdata_folder, folder), 0):
                                print(folder + ' already exists - skip download')
                            else:
                                test_data.append(folder)
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
    
    parser.add_argument('test_data_path',
                        help="test data folder path")

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

    if not os.path.exists(args.test_data_path):
        log.error("test data folder does not exist")
        sys.exit(1)
    data_file = os.path.join(args.output_folder, __data_files__)

    if __create_test_json_list__(args.test_path, data_file, args.test_data_path):
        log.success(f"filtered test data list created in {data_file}")


if __name__ == '__main__':
    # execute entry point
    __main__()
