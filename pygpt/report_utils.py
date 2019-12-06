"""
Report generation script:
Generates automatically the HTML report for the executed GPT tests.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import os
import sys
import datetime
import json

import core.fs as fs
from core.results import TestResutlSet, TestResult 
import core.temply as t
import core.tools as utils
import core.dbadaptor as sdb
import core.log as log

import matplotlib as mpl
mpl.use('Agg') # use no graphical server needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# DATE TIME FORMAT STRINGS
__datetime_fmt__ = '%d/%m/%Y %H:%M:%S'

def __auto_pct__(pct, total):
    val = int(round(pct/100 * total))
    if val < 1:
        return ''
    return f'{val}'

def __generate_pie__(name, passed, failed, skipped=0):
    my_dpi = 120
    fig = plt.figure(figsize=(600/my_dpi, 300/my_dpi), dpi=my_dpi)
    axis = fig.subplots()
    if skipped:
        values = [failed, passed, skipped]
        labels = ['failed', 'passed', 'skipped']
    else:
        values = [failed, passed]
        labels = ['failed', 'passed']
    total = sum(values)
    wedges, _, _ = axis.pie(values,
                            colors=['red', 'green', 'orange'],
                            autopct=lambda pct: __auto_pct__(pct, total),
                            textprops=dict(color="w", weight="semibold"))
    axis.legend(wedges, labels,
                title="Legend",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))
    axis.axis('square')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.savefig(fs.images.resolve(name), transparent=True)


def save_report(html, path):
    """save document"""
    with open(path, 'w') as file:
        file.write(html)


def performance_report(test, version):
    """generate test perofmance report"""
    if test.is_skipped() or not test._stats:
        log.error("No stats found")
        return
    args = {
        'test_id' : test.name,
        'summary' : test.perf_summary(version),
        'plots'   : test.plots_path(version)
    }
    if not test.has_adapator():
        with open(fs.templates.resolve('perf_report_template.html'), 'r') as file:
            template = t.Template( file.read())
    else:
        with open(fs.templates.resolve('perf_report_with_history_template.html'), 'r') as file:
            template = t.Template(file.read())
            args['version'] = version
    if template is None:
        log.error("Unable to load template")
        return

    html = template.generate(**args)
    with open(fs.tests.resolve(f'Performance_{test.name}.html'), 'w') as file:
        file.write(html)

def testset_report(test_set, scope, version):
    """
    Generates html reports for the given test execution.

    Paramters:
    ----------
     - base_path: path containing all results of the execution
    """
    fs.mkdir(fs.tests.path)
    template = None
    with open(fs.templates.resolve('gptTest_report_template.html'), 'r') as file:
        template = t.Template(file.read())
    if template is None:
        log.error("Unable to load template")
        return
    percent = round(100 * len(test_set.passed_tests())/len(test_set.tests), 2)
    html = template.generate(name=test_set.name,
                             start_date=test_set.start_date,
                             duration=f'{test_set.duration} s',
                             scope=scope,
                             operating_system=sys.platform,
                             version=version,
                             total=len(test_set.tests),
                             failed_tests=len(test_set.failed_tests()),
                             passed_tests=len(test_set.passed_tests()),
                             percent=percent,
                             real_duration=f'{test_set.real_duration} s',
                             tests=test_set.tests
                            )
    __generate_pie__(f'{test_set.name}_pie.png',
                     len(test_set.passed_tests()),
                     len(test_set.failed_tests()),
                     len(test_set.skipped_tests())
                    )
    with open(fs.tests.resolve(f'Report_{test_set.name}.html'), 'w') as file:
        file.write(html)
    # generate perofmance report for each test
    for test in test_set.tests:
        performance_report(test, version)


def __parse_set__(name, lines, dbadaptor=None):
    tests = []
    for line in lines:
        row = line.replace('\n', '').split(' - ')
        test_name = row[0]
        json_path = os.path.join('json', f'{test_name}.json')
        with open(fs.report.resolve(json_path), 'r') as f:
            tests.append(TestResult(json.load(f), row, dbadaptor))
    test_set = TestResutlSet(name, tests)
    return test_set

def get_test_sets(report_path, dbadaptor=None):
    """
    Get list of test sets executed.

    Paramters:
    ----------
     - base_path: path containing all results of the execution
    """
    fs.report.update(report_path)
    output_dir = fs.outputs.path
    filter_file = lambda x: x.startswith('Report_') and x.endswith('.txt')
    report_files = [f for f in os.listdir(output_dir) if filter_file(f)]
    test_sets = []
    for report_file in report_files:
        set_name = report_file[7:-4]
        with open(fs.outputs.resolve(report_file), 'r') as rep:
            test_sets.append(__parse_set__(set_name, rep.readlines(), dbadaptor))
    return test_sets


def generate_html_report(base_path, scope, version, dbadaptor=None):
    """
    Generates html reports for the given test execution.

    Paramters:
    ----------
     - base_path: path containing all results of the execution
    """
    test_sets = get_test_sets(base_path, dbadaptor)
    if len(test_sets) == 0:
        log.error("no tests set found...")
        sys.exit(0)
    start_date = min([test_set.start_date for test_set in test_sets])
    end_date = max([test_set.end_date for test_set in test_sets])
    total_seconds = sum([test_set.duration for test_set in test_sets])
    n_tests = sum([len(test_set.tests) for test_set in test_sets])
    duration_in_min = (end_date - start_date).total_seconds() / 60.0
    platform = sys.platform
    template = None
    with open(fs.templates.resolve('gptIndex_report_template.html'), 'r') as file:
        template = t.Template(file.read())
    if template is None:
        log.error("Unable to load template")
        return

    failedjson = len(list(filter(lambda x: x.is_failed(), test_sets)))
    failedtest = sum([len(x.failed_tests()) for x in test_sets])
    passedjson = len(list(filter(lambda x: x.is_passed(), test_sets)))
    passedtest = sum([len(x.passed_tests()) for x in test_sets])
    skippedjson = len(list(filter(lambda x: x.is_skipped(), test_sets)))
    __generate_pie__('results_pie.png', passedjson, failedjson, skippedjson)
    html = template.generate(start_date=start_date.strftime(__datetime_fmt__),
                             duration_in_min=round(duration_in_min, 2),
                             scope=scope,
                             operating_system=platform,
                             version=version,
                             totaljson=len(test_sets),
                             totaltest=n_tests,
                             failedjson=failedjson,
                             failedtest=failedtest,
                             passedjson=passedjson,
                             passedtest=passedtest,
                             percentjson=round(passedjson/len(test_sets) * 100, 2),
                             percenttest=round(passedtest/n_tests * 100, 2),
                             duration=f'{total_seconds} s',
                             test_sets=test_sets
                            )
    save_report(html, fs.report.resolve('index.html'))
    for test_set in test_sets:
        testset_report(test_set, scope, version)


def main():
    """
    Main report utils 
    """
    args = sys.argv[1:]
    if len(args) not in (4, 5):
        print("wrong number of arguments!\nreport_utils TEMPLATE_DIR BASE_PATH SCOPE VERSION (DB_PATH=None)")
        sys.exit(1)

    # use given template dir
    fs.templates.update(args[0])
    adaptor = None
    try:
        adaptor = None
        if len(args) == 5:
            db_path = args[4]
            adaptor = sdb.adaptor(db_path)
            adaptor.open()
        generate_html_report(args[1], args[2], args[3], adaptor)
        log.success('report generated successfully')
    finally:
        if adaptor is not None:
            adaptor.close()

if __name__ == '__main__':
    # execute the main function
    main()
    