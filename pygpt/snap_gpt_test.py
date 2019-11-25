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
import gpt_utils as utils


__DATE_FMT__ = '%d/%m/%Y %H:%M:%S'
__REGULAR_TAGS__ = ['REGULAR', 'DAILY', 'WEEKLY', 'RELEASE']


def lazy_bool(string):
    """
    convert a string to a boolean
    """
    return string.lower() == 'true'


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

    parser.add_argument('save_output',
                        default='false',
                        choices=['true', 'false'],
                        help="save output of failed tests (if scope not [REGULAR, DAILY...])")


    parser.add_argument('--profiling',
                        default='on',
                        choices=['on', 'off'],
                        help="enable the profiler")
    # parse arguments
    return parser.parse_args()


def __check_properties__(properties):
    """
    Check properties of the GPT Test executor.
    Exit(1) if it fails
    """
    test_folder = properties['testFolder']
    graph_folder = properties['graphFolder']
    input_folder = properties['inputFolder']
    expected_output_folder = properties['expectedOutputFolder']
    temp_folder = properties['tempFolder']

    if None in [test_folder, graph_folder,
                input_folder, expected_output_folder,
                temp_folder]:
        utils.error('some folder is null')
        sys.exit(1)


def __check_args__(args):
    """
    Check arguments of the GPT Test executor.
    Exit(1) if it fails
    """
    if not os.path.exists(args.json_path):
        utils.error(f'JSON file `{args.json_path}` does not exists')
        sys.exit(1)

    if not os.path.exists(args.report_dir):
        utils.error(f'rerpot folder `{args.report_dir}` does not exists')
        sys.exit(1)


def __vm_parameters__(test, snap_dir):
    """
    Prepare list of arguments for the Java VM
    """
    config_vm = None if not 'configVM' in test else test['configVM']
    if not config_vm:
        return ['-q', '4']
    params = []
    # set memory setting to configuration file
    if 'xmx' in config_vm:
        vm_option = os.path.join(snap_dir, 'gpt.vmoptions')
        vm_original = os.path.join(snap_dir, 'gpt.vmoptionsORIGINAL')
        shutil.copy2(vm_option, vm_original)
        modified_str = ""
        with open(vm_original) as file:
            for line in file.readlines():
                if line.startswith('-Xmx'):
                    modified_str += f'-Xmx{config_vm["xmx"]}\n'
                else:
                    modified_str += line
        with open(vm_option, 'w') as file:
            file.write(modified_str)
    # add extra args
    params.append('-c')
    params.append(config_vm['cacheSize'])
    params.append('-q')
    params.append(config_vm['parallelism'])

    return params


def __vm_parameters_reset__(test, snap_dir):
    """
    Reset Java VM paramters
    """
    config_vm = None if not 'configVM' in test else test['configVM']
    if not config_vm:
        return
    if 'xmx' in config_vm:
        vm_option = os.path.join(snap_dir, 'gpt.vmoptions')
        vm_original = os.path.join(snap_dir, 'gpt.vmoptionsORIGINAL')
        shutil.copy2(vm_original, vm_option)
        os.remove(vm_original)
    return


def __perpare_param__(value, properties):
    """
    Prepare parameter with custom values
    """
    if isinstance(value, str):
        value = value.replace('$graphFolder', properties['graphFolder'])
        value = value.replace('$inputFolder', properties['inputFolder'])
        value = value.replace('$expectedOutputFolder', properties['expectedOutputFolder'])
        value = value.replace('$tempFolder', properties['tempFolder'])
    return value


def __io_parameters__(test, properties):
    """
    Flag for the test parameters (inputs, outputs and paramters)

    Paramters:
    ----------
     - json: test json object
     - properties: test properties

    Returns:
    --------
    return list of arguments containing the custom paramters
    """
    params = [] # list of arguments
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
    """
    find the output produced in the selected folder.

    Parameters:
    -----------
     - output: output json object
     - folder: base folder where to search for ouput

    Returns:
    --------
    A file named `{output}.*` if only one file with this pattern
    has been found.
    A directory named `{output}/` if it exists.
    `None` otherwise.
    """
    # list of files starting with the name of the output
    files = list([f for f in os.listdir(folder)
                  if os.path.isfile(os.path.join(folder, f))
                  and f.startswith(f'{output["outputName"]}.')])
    if len(files) == 1:
        return os.path.join(folder, files[0]) # file named `output.*`
    out_path = os.path.join(folder, output['outputName'])
    if os.path.exists(out_path):
        return out_path # folder path
    return None # if nothing has been found


def __check_outputs__(test, args, properties):
    """
    Check the conformity of the resulting outputs with the expected outputs.

    Properties:
    -----------
     - test: test json object
     - args: arguments of the test executor
     - properties: properties of the test executor

    Returns:
    --------
    `True` if the output are conformed.
    `False` if the output are not conformed or not found.
    """
    for output in test['outputs']:
        if 'expected' in output and output['expected'] is not None and output['expected'] != "":
            # check output
            utils.log(f'comparing {output["outputName"]} with {output["expected"]}')
            output_path = __find_output__(output, properties['tempFolder'])
            if output_path is None:
                utils.error(f'test `{test["id"]}` failed, output {output["outputName"]} not found')
                return False
            expected_output_path = os.path.join(properties['expectedOutputFolder'],
                                                output['expected'])
            cmd = [args.java_path]
            cmd += args.java_args.split(' ')
            cmd += [args.test_output, output_path, expected_output_path, output['outputName']]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            utils.log(f'comparing done, result: {result.returncode}')
            stdout_file = os.path.join(args.report_dir, f'{test["id"]}_gptOutput.txt')

            if result.returncode != 0:
                utils.error(f"test `{test['id']}` failed:\n{result.stdout.decode('utf-8')}")
                with open(stdout_file, 'a') as file:
                    file.write(result.stdout.decode('utf-8'))
                return False
    return True


def __run_test__(test, args, properties):
    """
    Execute a test

    Parameters:
    -----------
     - test: json test object
     - args: test executer arguments
     - properties: test executer properties

    Returns:
    --------
    `True` if the test was succesful and the outputs are conformed to
    the expected output, `False` otherwise.
    """
    profiling = args.profiling == 'on' # profiling flag
    snap_dir = properties['snapBin'] if properties['snapBin'] is not None else ''
    gpt_bin = os.path.join(snap_dir, 'gpt') # gpt binary
    gpt_parameters = [gpt_bin] # gpt command and arguments
    # graph to test
    gpt_parameters.append(os.path.join(properties['graphFolder'], test['graphPath']))
    gpt_parameters += __vm_parameters__(test, snap_dir) # java vm parameters (if any)
    gpt_parameters += __io_parameters__(test, properties) # custom test parameters
    utils.log(f'execute: `{" ".join(gpt_parameters)}`') # DEBUG print
    if profiling:
        # output directory for the profiling
        output_dir = os.path.join(args.report_dir, test['id'])
        res, stdout = profiler.profile(gpt_parameters,
                                       0.2,
                                       output_dir,
                                       wait=False,
                                       child=False,
                                       plot=True)
        # execute the gpt test with the profiler at sampling time 200ms
    else:
        # execute gpt test without profiler
        res, stdout = profiler.run(gpt_parameters)
    utils.log('execution finished')
    # Reset Java VM parameters if needed
    __vm_parameters_reset__(test, snap_dir)

    # gpt Ouput file to store the ouput of the previous test execution
    stdout_file = os.path.join(args.report_dir, f'{test["id"]}_gptOutput.txt')
    with open(stdout_file, 'w') as file:
        file.write(stdout)

    # if the execution result is not 0 return False
    if res is not None and res > 0:
        return False
    # return the confirmity of the outputs
    return __check_outputs__(test, args, properties)


def __draw_graph__(test, properties, args):
    """
    Draw the diagram of the graph using the custom graph_drawer.
    """
    graph_path = os.path.join(properties['graphFolder'], test['graphPath'])
    image_path = os.path.join(args.report_dir, 'images', test['graphPath'])
    image_path = os.path.splitext(image_path)[0] + '.png'
    utils.mkdirs(os.path.dirname(image_path))
    graph_drawer.draw(graph_path, image_path)


def __save_json__(test, args):
    """
    Save test json individually into the report folder.
    """
    path = os.path.join(args.report_dir, 'json', f"{test['id']}.json")
    utils.mkdirs(os.path.dirname(path))
    with open(path, 'w') as file:
        file.write(json.dumps(test))


def __copy_output__(test, args, properties):
    """
    function to copy the outputs of the test (if neede) into
    the report directory.
    """
    if lazy_bool(args.save_output):
        utils.log('coping output products to `report/output` folder')
        files = os.listdir(properties['tempFolder'])
        for output in test['outputs']:
            name = output['outputName']
            for fname in [f for f in files if f.startswith(name)]:
                fpath = os.path.join(properties['tempFolder'], fname)
                dpath = os.path.join(args.report_dir, fname)
                if os.path.isdir(fpath):
                    shutil.copytree(fpath, dpath)
                else:
                    shutil.copy2(fpath, dpath)


def __print_stats__():
    """ print docker info """
    with open('/proc/meminfo', 'r') as meminfo:
        print(''.join(meminfo.readlines()[:3]), end='')


def pprint(test, starts=''):
    """pretty print test"""
    if isinstance(test, dict):
        for key in test:
            value = test[key]
            if isinstance(value, str):
                print(f'{starts}.{key}: {value}')
            else:
                print(f'{starts}.{key}:')
                pprint(value, ' '+starts)
    elif isinstance(test, list):
        for value in test:
            if isinstance(value, str):
                print(f'{starts}- {value}')
            else:
                print(f'{starts}+ object:')
                pprint(value, '  '+starts)


def __run_tests__(args, properties):
    """
    Execute list of test of a json file
    """
    output = '' # output string saved in Report_* file
    passed = True # passed flag
    with open(args.json_path, 'r') as file:
        # open the json file and parse it
        tests = json.load(file)
        tst_lst = []
        for test in tests:
            if 'frequency' in test:
                tst_lst.append(test['id'])
        utils.log(f'List of tests: {", ".join(tst_lst)}')
        count = 0
        for test in tests:
            # for each tests
            if not 'frequency' in test:
                continue # if no frequency is not a test
            count += 1
            utils.log(f"Test [{count}/{len(tst_lst)}]")                
            __print_stats__() # print server stats
            print("JSON ------")
            pprint(test, ' ')
            print("END  ------")
            utils.log(f"saving json file for test `{test['id']}`")
            __save_json__(test, args) # save json
            utils.log(f"drawing graph for test `{test['id']}`")
            __draw_graph__(test, properties, args) # make the graph image
            utils.log(f"preparing test `{test['id']}`")
            start = datetime.datetime.now().strftime(__DATE_FMT__) # stats
            output += f'{test["id"]} - {start}'
            print('START------')
            if not filter_json.compatible(args.scope, test['frequency']):
                output += f' - {start} - SKIPPED\n'
                utils.warning(f'test `{test["id"]}` skipped')
            else:
                utils.log(f"Test `{test['id']}`")
                utils.log(f'-- Author: {test["author"]}')
                utils.log(f'-- Description: {test["description"]}')
                result = __run_test__(test, args, properties)
                end = datetime.datetime.now().strftime(__DATE_FMT__)
                utils.log(f"finish test `{test['id']}`")
                passed = passed and result
                result_str = 'PASSED' if result else 'FAILED'
                output += f' - {end} - {result_str}\n'
                if not result:
                    utils.error(f"test `{test['id']} failed")
                else:
                    utils.log(f"test `{test['id']}` succeded")
                if not result and not args.scope.upper() in __REGULAR_TAGS__:
                    # copy output files
                    __copy_output__(test, args, properties)
    json_name = os.path.split(args.json_path)[-1]
    report_path = os.path.join(args.report_dir, f'Report_{json_name[:-5]}.txt')
    with open(report_path, 'w') as file:
        file.write(output)
    return passed


def __main__():
    """main test entry point"""
    utils.log('SNAP GPT Test Utils')
    args = __arguments__()
    __check_args__(args) # check if arguments are corrected
    properties = __load_properties__(args.properties) # load properties file
    __check_properties__(properties) # check if properties are correct

    if not __run_tests__(args, properties): # run tests with given parameters
        sys.exit(1) # if tests fails exit with status 1
    sys.exit(0) # otherwise normal exit

if __name__ == '__main__':
    __main__() # execute script
