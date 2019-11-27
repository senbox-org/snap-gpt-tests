"""
Report utils script
"""
import os
import sys
import datetime
import json

import template as t
import gpt_utils as utils

import matplotlib as mpl
mpl.use('Agg') # use no graphical backend
import matplotlib.pyplot as plt



__base_path__ = "Report"
__datetime_fmt__ = '%d/%m/%Y %H:%M:%S'
__perf_dir__ = 'performances'
__stats_dir__ = 'stats'
__csv_dir__ = 'csv'
__tests_dir__ = 'tests'
__out_dir__ = 'output'
__template_dir__ = '.'
__image_dir__ = 'images'



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
    plt.savefig(os.path.join(__base_path__, __image_dir__, name), transparent=True)


def resolve_path(*path):
    """create absolute path from relative one"""
    return os.path.join(__base_path__, *path)

def mkdir(*paths):
    """create dir if needed"""
    path = resolve_path(*paths)
    if not os.path.exists(path):
        os.mkdir(path)

def save_report(html, path):
    """save document"""
    with open(path, 'w') as file:
        file.write(html)

class Test(utils.Printable):
    """
    A single test result
    """
    def __init__(self, test_set, row):
        utils.Printable.__init__(self)
        self.name = row[0]
        self.status = row[3]
        self.start = datetime.datetime.strptime(row[1], __datetime_fmt__)
        self.end = datetime.datetime.strptime(row[2], __datetime_fmt__)
        self.test_set = test_set
        self.json_path = os.path.join('json', f'{self.name}.json')
        self.graph_id, self.vm_string, self.json = self.__load_json__()
        if self.status != 'SKIPPED':
            self.stats = self.__load_perfs__()
        else:
            self.stats = None

    def __load_json__(self):
        json_path = resolve_path(self.json_path)
        with open(json_path, 'r') as info:
            struct = json.load(info)
            param = 'Default configuration'
            if 'configVM' in struct and struct['configVM']:
                param = struct['configVM']
            return struct['graphPath'][:-4], param if param else 'Default configuration', struct
        return None, None, None

    def __load_perfs__(self):
        perf_stats_file = resolve_path(__perf_dir__, __stats_dir__, self.name+'.json')
        with open(perf_stats_file, 'r') as stats:
            return json.load(stats)
        return None

    def csv(self):
        """
        return raw perf csv file
        """
        if self.stats is None:
            return None
        csv_file = resolve_path(__perf_dir__, __csv_dir__ , self.name+'.csv')
        with open(csv_file, 'rb') as raw_data:
            return raw_data.read()

    def duration(self):
        """
        duration in second of the test
        """
        if self.stats:
            return self.stats['duration']['value']
        return (self.end - self.start).total_seconds()

    def duration_str(self):
        """duration string"""
        return f'{self.duration()} s'

    def memory_max(self):
        """
        maximum use of memory
        """
        if not self.stats:
            return 0
        return self.stats['memory']['max']

    def memory_max_str(self):
        """memory max string"""
        return f'{self.memory_max()} Mb'

    def memory_avg(self):
        """
        average use of memory
        """
        if not self.stats:
            return 0
        return self.stats['memory']['average']

    def is_failed(self):
        """
        is failed flag
        """
        return self.status == 'FAILED'

    def is_passed(self):
        """
        is passed flag
        """
        return self.status == 'PASSED'

    def is_skipped(self):
        """
        is skipped flag
        """
        return self.status == 'SKIPPED'


def performance_report(test):
        """generate test perofmance report"""
        if test.is_skipped() or not test.stats:
            utils.error("No stats found")
            return
        with open(os.path.join(__template_dir__, 'perf_report_template.html'), 'r') as file:
            template = t.Template(file.read())
        if template is None:
            utils.error("Unable to load template")
            return
        summ = []
        summary = test.stats
        if 'duration' in summary:
            summ.append(
                {
                    'label': "Process duration",
                    'value': summary['duration']['value'],
                    'unit': summary['duration']['unit']
                })
        if 'cpu_time' in summary:
            summ.append(
                {
                    'label': "CPU total timer",
                    'value': summary['cpu_time']['value'],
                    'unit': summary['cpu_time']['unit']
                })
        if 'cpu_usage' in summary:
            summ += [
                {
                    'label': "CPU average usage",
                    'value': summary['cpu_usage']['average'],
                    'unit': summary['cpu_usage']['unit']
                },
                {
                    'label': "CPU max usage",
                    'value': summary['cpu_usage']['max'],
                    'unit': summary['cpu_usage']['unit']
                }
            ]
        if 'memory' in summary:
            summ += [
                {
                    'label': "Memory average usage",
                    'value': summary['memory']['average'],
                    'unit': summary['memory']['unit']
                },
                {
                    'label': "Memory max usage",
                    'value': summary['memory']['max'],
                    'unit': summary['memory']['unit']
                }
            ]

        plots = [
            test.name+"_cpu_usage.png",
            test.name+"_memory_usage.png"
        ]
        html = template.generate(test_id=test.name, summary=summ, plots=plots)
        save_report(html, resolve_path(__tests_dir__, f'Performance_{test.name}.html'))


class TestSet(utils.Printable):
    """
    Test Set (json test set) class
    """
    def __init__(self, name):
        utils.Printable.__init__(self)
        self.name = name
        self.tests = []

    def duration(self):
        """
        Total duration in seconds
        """
        duration = 0
        for test in self.tests:
            duration += test.duration()
        return duration

    def memory_max(self):
        """
        maximum useage of memory
        """
        if self.tests:
            return max([test.memory_max() for test in self.tests])
        return 0

    def memory_avg(self):
        """
        average usage of memory
        """
        if self.tests:
            return round(sum([test.memory_avg() for test in self.tests]) / len(self.tests))
        return 0

    def start_date(self):
        """
        start datetime
        """
        if self.tests:
            return min([test.start for test in self.tests])
        return datetime.date(datetime.MAXYEAR, 1, 1)

    def end_date(self):
        """
        end datetime
        """
        if self.tests:
            return max([test.end for test in self.tests])
        return datetime.date(datetime.MINYEAR, 1, 1)

    def failed_tests(self):
        """
        list of failed tests
        """
        return list(filter(lambda test: test.is_failed(), self.tests))

    def passed_tests(self):
        """
        list of passed tests
        """
        return list(filter(lambda test: test.is_passed(), self.tests))

    def skipped_tests(self):
        """
        list of skipped tests
        """
        return list(filter(lambda test: test.is_skipped(), self.tests))

    def is_skipped(self):
        """
        is skipped flag
        """
        return not self.is_failed() and not self.is_passed()

    def is_failed(self):
        """
        is failed flag
        """
        return any([test.is_failed() for test in self.tests])

    def is_passed(self):
        """
        is passed flag
        """
        return all([test.is_passed() for test in self.tests])

    def status(self):
        """
        status of the test set
        """
        if self.is_failed():
            return 'FAILED'
        if self.is_passed():
            return 'PASSED'
        return 'SKIPPED'

    def duration_str(self):
        """
        duration string
        """
        return f'{self.duration()} s'

    def memory_max_str(self):
        """
        memory max string
        """
        return f'{self.memory_max()} Mb'

    def real_duration(self):
        """real elapsed time"""
        return int((self.end_date() - self.start_date()).total_seconds())

    def generate_html_report(self, scope, version):
        """
        Generates html reports for the given test execution.

        Paramters:
        ----------
         - base_path: path containing all results of the execution
        """
        mkdir(__tests_dir__)
        template = None
        with open(os.path.join(__template_dir__, 'gptTest_report_template.html'), 'r') as file:
            template = t.Template(file.read())
        if template is None:
            utils.error("Unable to load template")
            return
        percent = round(100 * len(self.passed_tests())/len(self.tests), 2)
        html = template.generate(name=self.name,
                                 start_date=self.start_date(),
                                 duration=f'{self.duration()} s',
                                 scope=scope,
                                 operating_system=sys.platform,
                                 version=version,
                                 total=len(self.tests),
                                 failed_tests=len(self.failed_tests()),
                                 passed_tests=len(self.passed_tests()),
                                 percent=percent,
                                 real_duration=f'{self.real_duration()} s',
                                 tests=self.tests
                                )
        __generate_pie__(f'{self.name}_pie.png',
                         len(self.passed_tests()),
                         len(self.failed_tests()),
                         len(self.skipped_tests())
                        )
        save_report(html, resolve_path(__tests_dir__, f'Report_{self.name}.html'))
        # generate perofmance report for each test
        for test in self.tests:
            performance_report(test)


def __parse_set__(name, lines):
    test_set = TestSet(name)
    for line in lines:
        row = line.replace('\n', '').split(' - ')
        test_set.tests.append(Test(name, row))
    return test_set

def get_test_sets(base_path):
    """
    Get list of test sets executed.

    Paramters:
    ----------
     - base_path: path containing all results of the execution
    """
    global __base_path__
    __base_path__ = base_path
    report_path = os.path.join(base_path, __out_dir__)
    filter_file = lambda x: x.startswith('Report_') and x.endswith('.txt')
    report_files = [f for f in os.listdir(report_path) if filter_file(f)]
    test_sets = []
    for report_file in report_files:
        set_name = report_file[7:-4]
        with open(os.path.join(report_path, report_file), 'r') as rep:
            test_sets.append(__parse_set__(set_name, rep.readlines()))
    return test_sets


def generate_html_report(base_path, scope, version):
    """
    Generates html reports for the given test execution.

    Paramters:
    ----------
     - base_path: path containing all results of the execution
    """
    test_sets = get_test_sets(base_path)
    if len(test_sets) == 0:
        utils.error("no tests set found...")
        sys.exit(0)
    start_date = min([test_set.start_date() for test_set in test_sets])
    end_date = max([test_set.end_date() for test_set in test_sets])
    total_seconds = sum([test_set.duration() for test_set in test_sets])
    n_tests = sum([len(test_set.tests) for test_set in test_sets])
    duration_in_min = (end_date - start_date).total_seconds() / 60.0
    platform = sys.platform
    template = None
    with open(os.path.join(__template_dir__, 'gptIndex_report_template.html'), 'r') as file:
        template = t.Template(file.read())
    if template is None:
        utils.error("Unable to load template")
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
    save_report(html, resolve_path('index.html'))
    for test_set in test_sets:
        test_set.generate_html_report(scope, version)

if __name__ == '__main__':
    ARGS = sys.argv
    if len(ARGS) != 5:
        print("wrong number of arguments!\nreport_utils TEMPLATE_DIR BASE_PATH SCOPE VERSION")
        sys.exit(-1)
    __template_dir__ = ARGS[1]
    generate_html_report(ARGS[2], ARGS[3], ARGS[4])
    utils.success('report generated successfully')