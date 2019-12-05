"""
Results models.

Author: Martino Ferrari (CS Group) <martino.ferrari@c-s.fr>
License: GPLv3
"""
import datetime
import json

import core.log as log
import core.fs as fs

from core.models import Test


__datetime_fmt__ = '%d/%m/%Y %H:%M:%S'


class TestReuslt(Test):
    """
    Represents the results of execution of a test
    """
    def __init__(self, struct, results, adaptor=None):
        super().__init__(struct)
        self._status = results[3]
        self._start = datetime.datetime.strptime(row[1], __datetime_fmt__)
        self._end = datetime.datetime.strptime(row[2], __datetime_fmt__)
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
        if self.stats is None:
            return None
        csv_file = fs.profiles.resolve_path(self.name+'.csv')
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
            return self.stats['duration']['value']
        return (self.end - self.start).total_seconds()

    @property
    def memory_max(self):
        """
        maximum use of memory
        """
        if self._stats is None:
            return 0
        return self._stats['memory']['max']

    @property  
    def memory_avg(self):
        """
        average use of memory
        """
        if self._stats is None:
            return 0
        return self._stats['memory']['average']


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
        return '\n'.join([f'<samp>{line}</samp><br>' for line in self.stdout.splitlines()])

    def json_html(self):
        if self._raw is None:
            return ''
        return __dict_to_html__(self.json)


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
            if self.__adaptor__ is not None:    
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
            self.name+"_cpu_usage.png",
            self.name+"_memory_usage.png"
        ]
        if self.__adaptor__ is not None:
            db_key = 'cpu_time_avg'
            times = self.__adaptor__.values(self.name, version, 'start')
            if len(times) == 0:
                return plots
            times = list([datetime.datetime.strptime(x, __sql_fmt__) for x in times])
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

            plt.savefig(fs.plots.resolve(self.name+"_cpu_time_history.png"))
            plt.close()
            
            plots.append(self.name+"_cpu_time_history.png")
            
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

            plt.savefig(fs.plots.resolve(self.name+"_memory_history.png"))
            plots.append(self.name+"_memory_history.png")
            plt.close()

        return plots




class TestResutlSet(log.Printable):
    """
    Set of tests representing the result of a single JSON 
    tests set.
    """