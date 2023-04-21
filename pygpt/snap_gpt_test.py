"""
SNAP GPT Test:
Executes the GPT tests for the ESA-SNAP CI project.

Author: Martino Ferrari (CS Group) <martino-ferrari@c-s.fr>
License: GPLv3
"""
import argparse
import configparser
import datetime
import sys
import os
import json
import subprocess
import shutil

from enum import Enum

from core.models import TestScope, Test

import core.profiler as profiler
import core.graph as graph
import core.tools as utils
import core.log as log


__DATE_FMT__ = '%d/%m/%Y %H:%M:%S'
__SEED_ENV_VARIABLE__ = 'snap.random.seed'


class Result(Enum):
    SKIPPED = -1
    PASSED = 0
    FAILED = 1
    CRASHED = 2

    def __str__(self):
        if self == Result.SKIPPED:
            return 'SKIPPED'
        if self == Result.PASSED:
            return 'PASSED'
        if self == Result.FAILED:
            return 'FAILED'
        return 'CRASHED'


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


def __str2bool__(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


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
                        help="save output of failed tests (if scope not [REGULAR, DAILY...])")


    parser.add_argument('--profiling',
                        default='on',
                        choices=['on', 'off'],
                        help="enable the profiler")

    parser.add_argument('--debug', 
                        default=False,
                        type=__str2bool__,
                        help="enable debugging")

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
        log.error('some folder is null')
        sys.exit(1)
    utils.mkdirs(temp_folder)


def __check_args__(args):
    """
    Check arguments of the GPT Test executor.
    Exit(1) if it fails
    """
    if not os.path.exists(args.json_path):
        log.error(f'JSON file `{args.json_path}` does not exists')
        sys.exit(1)

    if not os.path.exists(args.report_dir):
        log.error(f'rerpot folder `{args.report_dir}` does not exists')
        sys.exit(1)


def __vm_parameters_set__(test, snap_dir):
    """
    Prepare list of arguments for the Java VM
    """
    config_vm = test.jvm_config
    if not config_vm:
        return

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


def __vm_parameters_reset__(test, snap_dir):
    """
    Reset Java VM paramters
    """
    config_vm = test.jvm_config
    if not config_vm:
        return
    if 'xmx' in config_vm:
        vm_option = os.path.join(snap_dir, 'gpt.vmoptions')
        vm_original = os.path.join(snap_dir, 'gpt.vmoptionsORIGINAL')
        shutil.copy2(vm_original, vm_option)
        os.remove(vm_original)
    return

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
    output_conformity, stdout
    """
    stdout = ''
    log.info(f'check outputs')
    for output in test.outputs:
        if 'expected' in output and output['expected'] is not None and output['expected'] != "":
            # check output
            log.info(f'comparing {output["outputName"]} with {output["expected"]}')
            output_path = __find_output__(output, properties['tempFolder'])
            if output_path is None:
                log.error(f'test `{test.name}` failed, output {output["outputName"]} not found')
                return False
            expected_output_path = os.path.join(properties['expectedOutputFolder'],
                                                output['expected'])
            cmd = [args.java_path]
            cmd += utils.split_args(args.java_args)
            cmd += [args.test_output, output_path, expected_output_path, output['outputName']]
            log.info(cmd)
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.info(f'comparing done, result: {result.returncode}')
            stdout = result.stdout.decode('utf-8','ignore')
            stdout_file = os.path.join(args.report_dir, f'{test.name}_gptOutput.txt')
            with open(stdout_file, 'a') as file:
                file.write(stdout)
            
            if result.returncode != 0:
                log.error(f"test `{test.name}` failed:\n{stdout}")
                return False, stdout
        else:
            log.warning(f'comparing unavaible: ',output)

    return True, stdout


def debug_log(args, *msgs):
    """Log debug event in a file."""
    if args.debug:
        log.debug(msgs)
        path = os.path.join(args.report_dir, 'gpt_debug.log')
        timestamp = datetime.datetime.now().strftime(__DATE_FMT__)
        log_mesg = ' '.join([f'{arg}' for arg in msgs])
        with open(path, 'a+') as file:
            file.write(f'{timestamp} {log_mesg}\n')


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
    log.info(f'execute: `{" ".join(gpt_parameters)}`') # DEBUG print
    # graph to test
    gpt_parameters.append(os.path.join(properties['graphFolder'], test.graph_path))
    gpt_parameters += test.gpt_parameters(properties)
    # prepare JVM settings if needed
    __vm_parameters_set__(test, snap_dir)
    # log.info(f'execute: `{" ".join(gpt_parameters)}`') # DEBUG print
    # prepare enviroment
    enviroment = os.environ
    if test.seed is not None:
        enviroment[__SEED_ENV_VARIABLE__] = str(test.seed)
    debug_log(args, 'test start', test.name)
    if profiling:
        # output directory for the profiling
        output_dir = os.path.join(args.report_dir, test.name)
        res, stdout = profiler.profile(gpt_parameters,
                                       0.1,
                                       output_dir,
                                       wait=False,
                                       child=False,
                                       plot=True,
                                       env=enviroment,timeout=4000)
        # execute the gpt test with the profiler at sampling time 200ms
    else:
        # execute gpt test without profiler
        res, stdout = profiler.run(gpt_parameters, env=enviroment)
    debug_log(args, 'test done', test.name, res)

    log.info('execution finished')
    # Reset Java VM parameters if needed
    __vm_parameters_reset__(test, snap_dir)

    # gpt Ouput file to store the ouput of the previous test execution
    stdout_file = os.path.join(args.report_dir, f'{test.name}_gptOutput.txt')
    with open(stdout_file, 'w') as file:
        file.write(stdout)

    if res is None:
        res = 0

    # if a result output is configuated
    if test.result is not None:
        if test.result['status'] and res > 0:
            # the process should not have failed
            return Result.CRASHED
        elif not test.result['status'] and test.result['source'] == 'process':
            # the process should fail graciously
            if res == 0:
                # process succeded and should have failed
                log.error(f'test `{test.name}` was supposed to fail')
                return Result.FAILED
            elif not test.result['message'].lower() in stdout.lower():
                # process failed but with a different message than expected
                log.error(f'test `{test.name}` was suppoed to fail with message `{test.result["message"]}`')
                return Result.FAILED
            else:
                log.success(f'test `{test.name}` failed succesfully')
                return Result.PASSED
    # if the execution result is not 0 return False
    elif res > 0:
        return Result.CRASHED

    debug_log(args, 'check output', test.name)
    # check outputs
    conformity, check_stdout = __check_outputs__(test, args, properties)
    debug_log(args, 'check done', test.name, conformity)

    if test.result is not None:
        if test.result['status']:
            return conformity
        elif conformity:
            log.error(f'conformity test for `{test.name}` was supposed to fail')
            return Result.FAILED
        elif not test.result['message'].lower() in check_stdout.lower():
            log.error(f'conformity test for `{test.name}` was suppoed to fail with message `{test.result["message"]}`')
            return Result.FAILED
        else:
            log.success(f'conformity test `{test.name}` failed succesfully')
            return Result.PASSED
    else:
        return Result.PASSED if conformity else Result.FAILED


def __draw_graph__(test, properties, args):
    """
    Draw the diagram of the graph using the custom graph_drawer.
    """
    graph_path = os.path.join(properties['graphFolder'], test.graph_path)
    image_path = os.path.join(args.report_dir, 'images', test.graph_path)
    image_path = os.path.splitext(image_path)[0] + '.jpg'
    image_path = utils.mkdirs(os.path.dirname(image_path))
    if image_path:
        graph.draw(graph_path, image_path)


def __save_json__(test, args):
    """
    Save test json individually into the report folder.
    """
    path = os.path.join(args.report_dir, 'json', f"{test.name}.json")
    utils.mkdirs(os.path.dirname(path))
    with open(path, 'w') as file:
        file.write(json.dumps(test._raw))


def __copy_output__(test, args, properties):
    """
    function to copy the outputs of the test (if neede) into
    the report directory.
    """
    if lazy_bool(args.save_output):
        log.info('coping output products to `report/output` folder')
        files = os.listdir(properties['tempFolder'])
        for output in test.outputs:
            name = output['outputName']
            for fname in [f for f in files if f.startswith(name)]:
                fpath = os.path.join(properties['tempFolder'], fname)
                dpath = os.path.join(args.report_dir, fname)
                if os.path.isdir(fpath):
                    shutil.copytree(fpath, dpath)
                else:
                    shutil.copy2(fpath, dpath)


def __run_tests__(args, properties):
    """
    Execute list of test of a json file
    """
    debug_log(args, 'testing start')

    output = '' # output string saved in Report_* file
    passed = True # passed flag
    with open(args.json_path, 'r') as file:
        # open the json file and parse it
        tests = json.load(file)
        test_list = []
        for test in tests:
            if 'frequency' in test:
                test_list.append(Test(test, args.json_path))
        log.info(f'List of tests: {", ".join([x.name for x in test_list])}')
        count = 0
        for test in test_list:
            # for each tests
            count += 1
            print() # empty line here
            log.info(f"Test [{count}/{len(test_list)}]")
            log.info(f"saving json file for test `{test.name}`")
            __save_json__(test, args) # save raw json copy
            log.info(f"drawing graph for test `{test.name}`")
            __draw_graph__(test, properties, args) # make the graph image
            log.info(f"preparing test `{test.name}`")
            start = datetime.datetime.now().strftime(__DATE_FMT__) # stats
            output += f'{test.name} - {start}'
            if not test.compatible(TestScope.init(args.scope)):
                output += f' - {start} - SKIPPED\n'
                log.warning(f'test `{test.name}` skipped')
            else:
                log.info(f"Test `{test.name}`")
                log.info(f'-- Author: {test.author}')
                log.info(f'-- Description: {test.description}')
                result = __run_test__(test, args, properties)
                end = datetime.datetime.now().strftime(__DATE_FMT__)
                log.info(f"finish test `{test.name}`")
                passed = passed and (result == Result.PASSED)
                result_str = str(result)
                output += f' - {end} - {result_str}\n'
                if result == Result.PASSED:
                    log.success(f"test `{test.name}` succeded")    
                else:
                    log.error(f"test `{test.name} failed")
                if not isinstance(TestScope.init(args.scope), TestScope):
                    # copy output files
                    __copy_output__(test, args, properties)
    json_name = os.path.split(args.json_path)[-1]
    report_path = os.path.join(args.report_dir, f'Report_{json_name[:-5]}.txt')
    with open(report_path, 'w') as file:
        file.write(output)
    print('final status: ', passed)
    debug_log(args, 'testing end')
    return passed

def exit(properties, code=0):
    utils.rmfiles(properties['tempFolder'])
    sys.exit(code)

def __main__():
    """main test entry point"""
    log.info('SNAP GPT Test Utils')
    args = __arguments__()
    __check_args__(args) # check if arguments are corrected
    properties = __load_properties__(args.properties) # load properties file
    __check_properties__(properties) # check if properties are correct

    exit_code = 0 if __run_tests__(args, properties) else 1 # run tests with given parameters
    exit(properties, exit_code) # if tests fails exit with status code

if __name__ == '__main__':
    __main__() # execute script
