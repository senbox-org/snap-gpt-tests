"""
Results models.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import datetime
import sys
import json

import matplotlib as mpl
mpl.use('Agg') # use no graphical server needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import core.log as log
import core.fs as fs
import core.temply as t

from core.models import Test


# DATE TIME FORMAT STRINGS
__datetime_fmt__ = '%d/%m/%Y %H:%M:%S'
__sql_fmt__ = "%Y-%m-%d %H:%M:%S"


def __val_to_html__(value):
    html = ''
    if isinstance(value, list):
        html += '<ol>'
        for el in value:
            html += f'<li>'+__val_to_html__(el)+'</li>'
        return html + '</ol>'
    elif isinstance(value, dict):
        return __dict_to_html__(value)
    return str(value)

def __dict_to_html__(data):
    html = '<ul>\n'
    for key in data:
        html += f'<li><b>{key}</b>: {__val_to_html__(data[key])}</li>'
    return html + '</ul>'

class TestResult(Test):
    """
    Represents the results of execution of a test
    """
    def __init__(self, struct, results, adaptor=None):
        super().__init__(struct)
        self._status = results[3]
        self._start = datetime.datetime.strptime(results[1], __datetime_fmt__)
        self._end = datetime.datetime.strptime(results[2], __datetime_fmt__)
        self.__adaptor__ = adaptor
        if self._status != 'SKIPPED':
            self._stats = self.__load_perfs__()
            self._stdout = self.__load_stdout__()
        else:
            self._stats = None
            self._stdout = None

    def __load_perfs__(self):
        perf_stats_file = fs.statistics.resolve(self.name+'.json')
        with open(perf_stats_file, 'r') as stats:
            return json.load(stats)
        return None

    def __load_stdout__(self):
        stdout_path = fs.outputs.resolve(f'{self.name}_gptOutput.txt')
        with open(stdout_path, 'r') as file:
            return file.read()
        return None

    def raw_profile(self):
        """
        return raw perf csv file
        """
        if self._stats is None:
            return None
        csv_file = fs.profiles.resolve(self.name+'.csv')
        with open(csv_file, 'rb') as raw_data:
            return raw_data.read()

    @property
    def status(self):
        return self._status

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def duration(self):
        """
        duration in second of the test
        """
        if self._stats is not None:
            return self._stats['duration']['value']
        return (self.end - self.start).total_seconds()

    @property
    def memory_max(self):
        """
        maximum use of memory
        """
        if self._stats is None:
            return -1
        return self._stats['memory']['max']

    @property
    def memory_avg(self):
        """
        average use of memory
        """
        if self._stats is None:
            return -1
        return self._stats['memory']['average']

    @property
    def io_write(self):
        if self._stats is None:
            return -1
        return self._stats['io']['write']

    @property
    def io_read(self):
        if self._stats is None:
            return -1
        return self._stats['io']['read']

    @property
    def cpu_time(self):
        if self._stats is None:
            return -1
        return self._stats['cpu_time']['value']

    @property
    def cpu_usage_avg(self):
        if self._stats is None:
            return -1
        return self._stats['cpu_usage']['average']

    @property
    def cpu_usage_max(self):
        if self._stats is None:
            return -1
        return self._stats['cpu_usage']['max']


    @property
    def threads_avg(self):
        if self._stats is None:
            return -1
        return self._stats['threads']['average']

    @property
    def threads_max(self):
        if self._stats is None:
            return -1
        return self._stats['threads']['max']

    @property
    def stdout(self):
        """Test ouput."""
        return self._stdout

    def is_crashed(self):
        """
        is crashed flag
        """
        return self.status == 'CRASHED' or (self.is_failed() and 'Exception' in self._stdout)

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

    def stdout_html(self):
        """
        Format stdout for html.
        """
        if self._stdout is None:
            return ''
        return '\n'.join([f'<samp>{line}</samp><br>' for line in self._stdout.splitlines()])

    def json_html(self):
        if self._raw is None:
            return ''
        return __dict_to_html__(self._raw)


    def __get_value__(self, label, key, version, param='value'):
        obj = None
        if 'duration' in self._stats:
            obj = {
                'label': label,
                'value': self._stats[key][param],
                'unit': self._stats[key]['unit'],
                'reference': '-',
                'average': '-'
            }
            if self.__adaptor__ is not None and self.name is not None:
                db_key = key
                if param == 'average':
                    db_key += '_avg'
                elif param == 'max':
                    db_key += '_max'
                vals = self.__adaptor__.values(self.name, version, db_key)
                if len(vals) > 0:
                    obj['average'] = round(sum(vals) / len(vals), 1)

                ref = self.__adaptor__.reference_value(self.name, db_key)
                if ref is not None:
                    obj['reference'] = ref

        return obj

    def perf_summary(self, version):
        """
        Create summary struct of performances.
        """
        summ = []
        vals = [("Process duration", "duration", version),
                ("CPU total time", "cpu_time", version),
                ("CPU average usage", "cpu_usage", version, "average"),
                ("CPU max usage", "cpu_usage", version, "max"),
                ("Memory average usage", "memory", version, "average"),
                ("Memory max usage", "memory", version, "max")
               ]
        for val in vals:
            result = self.__get_value__(*val)
            if result is not None:
                summ.append(result)
        return summ

    def plots_path(self, version):
        """
        return list of plots associated to the test.
        """
        plots = [
            self.name+"_cpu_usage.svg",
            self.name+"_memory_usage.svg"
        ]
        if self.__adaptor__ is not None:
            db_key = 'cpu_time_avg'
            times = self.__adaptor__.values(self.name, version, 'start')
            if len(times) == 0:
                return plots
            # times = list([datetime.datetime.strptime(x, __sql_fmt__) for x in times])
            if len(times) <= 1:
                """no history in db"""
                return plots
            cpu_time = self.__adaptor__.values(self.name, version, 'cpu_time')
            memory = self.__adaptor__.values(self.name, version, 'memory_avg')
            _, axis = plt.subplots(figsize=(10, 7))
            plt.plot(times, cpu_time, 'o-')
            plt.grid(alpha=0.5)
            plt.xlabel('Date')
            plt.ylabel('CPU Average Time (s)')
            plt.title('CPU Average Time Historic')
            #set ticks every day
            axis.xaxis.set_major_locator(mdates.DayLocator())
            #set major ticks format
            axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

            plt.savefig(fs.plots.resolve(self.name+"_cpu_time_history.svg"))
            plt.close()

            plots.append(self.name+"_cpu_time_history.svg")

            _, axis = plt.subplots(figsize=(10, 7))
            plt.plot(times, memory, 'o-')
            plt.grid(alpha=0.5)
            plt.xlabel('Date')
            plt.ylabel('Memory Average (Mb)')
            plt.title('Memory Average Historic')
            #set ticks every day
            axis.xaxis.set_major_locator(mdates.DayLocator())
            #set major ticks format
            axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

            plt.savefig(fs.plots.resolve(self.name+"_memory_history.svg"))
            plots.append(self.name+"_memory_history.svg")
            plt.close()

        return plots

    def has_adapator(self):
        """
        Checks if the db adaptor is setted.
        """
        return self.__adaptor__ is not None

    def has_statistics(self):
        """
        Checks if statistics have been generated.
        """
        return self._stats is not None


class TestResutlSet(log.Printable):
    """
    Set of tests representing the result of a single JSON
    tests set.
    """
    def __init__(self, name, tests):
        log.Printable.__init__(self)
        self.name = name
        self._tests = tests

    @property
    def tests(self):
        return self._tests


    @property
    def duration(self):
        """
        Total duration in seconds
        """
        duration = 0
        for test in self.tests:
            duration += test.duration
        return duration

    @property
    def memory_max(self):
        """
        maximum useage of memory
        """
        if self.tests:
            return max([test.memory_max for test in self.tests])
        return -1

    @property
    def memory_avg(self):
        """
        average usage of memory
        """
        if self.tests:
            return round(sum([test.memory_avg for test in self.tests]) / len(self.tests))
        return -1

    @property
    def start_date(self):
        """
        start datetime
        """
        if self.tests:
            return min([test.start for test in self.tests])
        return datetime.date(datetime.MAXYEAR, 1, 1)

    @property
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
        return list(filter(lambda test: test.is_failed() or test.is_crashed(), self.tests))

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
        return any([test.is_failed() or test.is_crashed() for test in self.tests])

    def is_passed(self):
        """
        is passed flag
        """
        return all([test.is_passed() for test in self.tests])

    @property
    def status(self):
        """
        status of the test set
        """
        if self.is_failed():
            return 'FAILED'
        if self.is_passed():
            return 'PASSED'
        return 'SKIPPED'

    @property
    def real_duration(self):
        """real elapsed time"""
        return int((self.end_date - self.start_date).total_seconds())
