"""SNAP GPT Test"""
import argparse
import configparser
import datetime
import sys
import os
import json
import subprocess

import filter_json


__DATE_FMT__ = '%d/%m/%Y %H:%M:%S'


def __load_properties__(path):
    """
    load properties file
    """
    config = configparser.ConfigParser()
    with open(path, 'r') as file:
        config.read_string('[SNAP]\n'+file.read())
    return config['SNAP']


def __arguments__():
    """
    parse arguments passed by the command line
    """
    # setup arg parser
    parser = argparse.ArgumentParser()

    parser.add_argument('test_output',
                        help="GPT Output Test Executor")

    parser.add_argument('properties',
                        help="properties file")

    parser.add_argument('scope',
                        help="test scope")

    parser.add_argument('json_path',
                        help="test json file path")

    parser.add_argument('report_dir',
                        help="report directory path")

    parser.add_argument('--Profiling',
                        default='on',
                        choices=['on', 'off'],
                        help="enable the profiler")

    # parse arguments
    return parser.parse_args()


def __check_properties__(properties):
    test_folder = properties['testFolder']
    graph_folder = properties['graphFolder']
    input_folder = properties['inputFolder']
    expected_output_folder = properties['expectedOutputFolder']
    temp_folder = properties['tempFolder']

    if None in [test_folder, graph_folder,
                input_folder, expected_output_folder,
                temp_folder]:
        print('Some folder is null')
        sys.exit(1)


def __check_args__(args):
    if not os.path.exists(args.json_path):
        print(f'JSON file does not exists: {args.json_path}')
        sys.exit(1)

    if not os.path.exists(args.report_dir):
        print(f'Rerpot folder doees not exists: {args.report_dir}')
        sys.exit(1)


def __vm_parameters__(test):
    configVM = None if not 'configVM' in test else test['configVM']
    if not configVM:
        return []
    params = []
    return params

def __run_test__(test, args, properties):
    profiling = args.profiling == 'on'
    gpt_parameters = []
    gpt_bin = os.path.join(properties['snapBin'], 'gpt') if properties['snapBin'] else 'gpt'
    gpt_parameters.append(gpt_bin)
    gpt_parameters.append(os.path.join(args.graph_folder, test['graphPath']))
    gpt_parameters += __vm_parameters__(test)
    
    return False

def __run_tests__(args, properties):
    output = ''
    passed = True
    with open(args.json_path, 'r') as file:
        tests = json.load(file)
        for test in tests:
            if not 'frequency' in test:
                continue
            start = datetime.datetime.now().strftime(__DATE_FMT__)
            output += f'{test["name"]} - {start}'
            if not filter_json.compatible(args.scope, test['frequency']):
                output += f' - {start} - SKIPPED\n'
            else:
                result = __run_test__(test, args, properties)
                passed = passed and result
                end = datetime.datetime.now().strftime(__DATE_FMT__)
                result_str = 'PASSED' if result else 'FAILED'
                output += f' - {end} - {result_str}\n'
    json_name = os.path.split(args.json_path)[-1]
    report_path = os.path.join(args.report_dir, f'Report_{json_name}.txt')
    with open(report_path, 'w') as file:
        file.write(output)
    return passed



def __main__():
    """main entry point"""
    args = __arguments__()
    __check_args__(args)
    properties = __load_properties__(args.properties)
    __check_properties__(properties)
    if not __run_tests__(args, properties):
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    __main__() # execute script
