"""
Report utils script
"""
import os
import sys
import datetime
import json

import matplotlib.pyplot as plt

import template as t


__base_path__ = "Report"
__datetime_fmt__ = '%d/%m/%Y %H:%M:%S'
__perf_dir__ = 'perfs'
__stats_dir__ = 'stats'
__tests_dir__ = 'tests'
__out_dir__ = 'output'
__template_dir__ = '.'
__image_dir__ = 'images'


def __generate_pie__(name, passed, failed, skipped=0):
    _, axis = plt.subplots()
    axis.pie([failed, passed, skipped], colors=['red', 'green', 'yellow'])
    axis.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.savefig(os.path.join(__base_path__, __image_dir__, name))


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

class Test:
    """
    A single test result
    """
    def __init__(self, test_set, row):
        self.name = row[0]
        self.status = row[3]
        self.start = datetime.datetime.strptime(row[1], __datetime_fmt__)
        self.end = datetime.datetime.strptime(row[2], __datetime_fmt__)
        self.test_set = test_set
        self.json_path = os.path.join('json', test_set, f'{self.name}.json')
        self.graph_id, self.vm_string = self.__load_json__()
        self.stats = self.__load_perfs__()

    def __load_json__(self):
        json_path = resolve_path(self.json_path)
        with open(json_path, 'r') as info:
            struct = json.load(info)
            param = struct['configVM']
            return struct['graphPath'][:-4], param if param else 'Default configuration'
        return None, None

    def __load_perfs__(self):
        perf_stats_file = resolve_path(__perf_dir__, __stats_dir__, self.name+'.json')
        with open(perf_stats_file, 'r') as stats:
            return json.load(stats)
        return None

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

    def performance_report(self):
        """generate perofmance report"""
        with open(os.path.join(__template_dir__, 'perf_report_template.html'), 'r') as file:
            template = t.Template(file.read())
        if template is None:
            print("Unable to load template")
            return
        summary = self.stats
        summ = [
            {
                'label': "Process duration",
                'value': summary['duration']['value'],
                'unit': summary['duration']['unit']
            },
            {
                'label': "CPU total timer",
                'value': summary['cpu_time']['value'],
                'unit': summary['cpu_time']['unit']
            },
            {
                'label': "CPU average usage",
                'value': summary['cpu_usage']['average'],
                'unit': summary['cpu_usage']['unit']
            },
            {
                'label': "CPU max usage",
                'value': summary['cpu_usage']['max'],
                'unit': summary['cpu_usage']['unit']
            },
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
            self.name+"_cpu_usage.png",
            self.name+"_memory_usage.png"
        ]
        html = template.generate(test_id=self.name, summary=summ, plots=plots)
        save_report(html, resolve_path(__tests_dir__, f'Performance_{self.name}.html'))


class TestSet:
    """
    Test Set (json test set) class
    """
    def __init__(self, name):
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

    def is_failed(self):
        """
        is failed flag
        """
        return any([test.is_failed() for test in self.tests])

    def is_passed(self):
        """
        is passed flag
        """
        return all([not test.is_failed() for test in self.tests])

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
            print("Unable to load template")
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
        __generate_pie__(f'{self.name}_pie.png', len(self.passed_tests()), len(self.failed_tests()))
        save_report(html, resolve_path(__tests_dir__, f'Report_{self.name}.html'))
        # generate perofmance report for each test
        for test in self.tests:
            test.performance_report()


def __parse_set__(name, lines):
    test_set = TestSet(name)
    for line in lines:
        row = line.replace('\n', '').split(' - ')
        test_set.tests.append(Test(name, row))
    return test_set




def generate_html_report(base_path, scope, version):
    """
    Generates html reports for the given test execution.

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
    if not test_sets:
        print("no tests set...")
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
        print("Unable to load template")
        return
    failedjson = len(list(filter(lambda x: x.is_failed(), test_sets)))
    failedtest = sum([len(x.failed_tests()) for x in test_sets])
    passedjson = len(list(filter(lambda x: x.is_passed(), test_sets)))
    passedtest = sum([len(x.passed_tests()) for x in test_sets])
    __generate_pie__('results_pie.png', passedjson, failedjson)
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
    print(f'>> report_utils {ARGS}')
    __template_dir__ = ARGS[1]
    generate_html_report(ARGS[2], ARGS[3], ARGS[4])
