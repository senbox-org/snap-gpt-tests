"""SNAP GPT Test"""
import argparse
import configparser
import datetime
import sys
import os
import json
import subprocess
import shutil

import filter_json
import profiler
import graph_drawer


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

    parser.add_argument('java_path', help='java path')
    parser.add_argument('java_args', help='java args')

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


    parser.add_argument('--profiling',
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


def __vm_parameters__(test, snap_dir):
    configVM = None if not 'configVM' in test else test['configVM']
    if not configVM:
        return []
    params = []
    # set memory setting to configuration file
    if 'xmx' in configVM:
        vm_option = os.path.join(snap_dir, 'gpt.vmoptions')
        vm_original = os.path.join(snap_dir, 'gpt.vmoptionsORIGINAL')
        shutil.copy2(vm_option, vm_original)
        modified_str = "";
        with open(vm_original) as file:
            for line in file.readlines():
                if line.startswith('-Xmx'):
                    modified_str += f'-Xmx{configVM["xmx"]}\n'
                else:
                    modified_str += line
        with open(vm_option, 'w') as file:
            file.write(modified_str)
    # add extra args
    params.append('-c')
    params.append(configVM['cacheSize'])
    params.append('-q')
    params.append(configVM['parallelism'])

    return params

def __vm_parameters_reset__(test, snap_dir):
    configVM = None if not 'configVM' in test else test['configVM']
    if not configVM:
        return 
    if 'xmx' in configVM:
        vm_option = os.path.join(snap_dir, 'gpt.vmoptions')
        vm_original = os.path.join(snap_dir, 'gpt.vmoptionsORIGINAL')
        shutil.copy2(vm_original, vm_option)
        os.remove(vm_original)
    return

def __perpare_param__(value, properties):
    value = value.replace('$graphFolder', properties['graphFolder'])
    value = value.replace('$inputFolder', properties['inputFolder'])
    value = value.replace('$expectedOutputFolder', properties['expectedOutputFolder'])
    value = value.replace('$tempFolder', properties['tempFolder'])
    return value

def __io_parameters__(test, properties):
    params = []
    # prepare inputs
    for in_key in test['inputs']:
        in_value = __perpare_param__(test['inputs'][in_key], properties)
        in_value = os.path.join(properties['inputFolder'], in_value)
        params.append(f'-P{in_key}={in_value}')

    # prepare paramters
    for param_key in test['parameters']:
        param = __perpare_param__(test['parameters'][param_key], properties)
        params.append(f'-P{param_key}={param}')

    # prepare outputs
    for output in test['outputs']:
        out_key = output['parameter']
        out_value = __perpare_param__(output['outputName'], properties)
        out_value = os.path.join(properties['tempFolder'], out_value)
        params.append(f'-P{out_key}={out_value}')

    return params

def __find_output__(output, folder):
    files = list([f for f in os.listdir(folder) if f.startswith(f'{output["outputName"]}.')])
    if len(files) == 1:
        return os.path.join(folder, files[0])
    out_dir = os.path.join(folder, output['outputName'])
    if os.path.exists(out_dir):
        return out_dir
    return None

def __run_test__(test, args, properties):
    profiling = args.profiling == 'on'
    gpt_parameters = []
    snap_dir = properties['snapBin']
    snap_dir = snap_dir if snap_dir else ''
    gpt_bin = os.path.join(snap_dir, 'gpt')
    gpt_parameters.append(gpt_bin)
    gpt_parameters.append(os.path.join(properties['graphFolder'], test['graphPath']))
    gpt_parameters += __vm_parameters__(test, snap_dir)
    gpt_parameters += __io_parameters__(test, properties)
    
    if profiling:
        output_dir = os.path.join(properties['tempFolder'], test['id'])
        res, stdout = profiler.profile(gpt_parameters,
                                       200,
                                       output_dir,
                                       wait=False,
                                       child=False,
                                       plot=True)
    else:
        res, stdout = profiler.run(gpt_parameters)
    
    __vm_parameters_reset__(test, snap_dir)
    stdout_file = os.path.join(paramters['tempFolder'], f'{test["id"]}_gptOutput.txt')
    
    with open(stdout_file, 'w') as file:
        file.write(stdout)

    if res is not None and res > 0:
        print(f">> Test {test['id']} failded")
        return False

    for output in test['outputs']:
        if 'expected' in output and output['expected'] is not None:
            # check output
            output_path = __find_output__(output, paramters['tempFolder'])
            if output_path is None:
                print(f'>> Test {test["id"]} failed: output {output["outputName"]} not found!')
                return False
            expected_output_path = os.path.join(properties['expectedOutputFolder'], output['expected'])
            cmd = [args.java_path]
            cmd +=  args.java_args.split(' ')
            cmd +=  [args.test_output, output_path, expected_output_path, output['outputName']]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                print(f">> Test {test['id']} failed:\n{result.stdout.decode('utf-8')}")
                with open(stdout_file, 'a+') as file:
                    file.write(result.stdout.decode('utf-8'))
                return False
    return True


def __mkdirs__(path):
    paths = os.path.split(os.path.dirname(path))
    crr = ''
    for path in paths:
        crr = os.path.join(crr, path)
        if not os.path.exists(crr):
            os.mkdir(crr)

def __draw_graph__(test, properties, args):
    graph_path = os.path.join(properties['graphFolder'], test['graphPath'])
    image_path = os.path.join(args.report_dir, 'images', test['graphPath'])
    image_path = os.path.splitext(image_path)[0] + '.png'
    __mkdirs__(image_path)
    graph_drawer.draw(graph_path, image_path)
    
def __save_json__(test, properties, args):
    path = os.path.join(args.report_dir, 'json', f"{test['id']}.json")
    __mkdirs__(path)
    with open(path, 'w') as file:
        file.write(json.dumps(test))


def __run_tests__(args, properties):
    output = ''
    passed = True
    with open(args.json_path, 'r') as file:
        tests = json.load(file) 
        for test in tests:
            if not 'frequency' in test:
                continue
            __save_json__(test, properties, args)
            __draw_graph__(test, properties, args)
            start = datetime.datetime.now().strftime(__DATE_FMT__)
            output += f'{test["id"]} - {start}'
            print(args.scope, test['frequency'])
            if not filter_json.compatible(args.scope, test['frequency']):
                output += f' - {start} - SKIPPED\n'
                print('skipped')
            else:
                result = __run_test__(test, args, properties)
                passed = passed and result
                end = datetime.datetime.now().strftime(__DATE_FMT__)
                result_str = 'PASSED' if result else 'FAILED'
                output += f' - {end} - {result_str}\n'
                print(test['id'], start, end, result_str)
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

    perfs = os.path.join(args.report_dir, 'perfs')
    if not os.path.exists(perfs):
        os.mkdir(perfs)

    if not __run_tests__(args, properties):
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    __main__() # execute script
