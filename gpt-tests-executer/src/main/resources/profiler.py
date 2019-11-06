#! /usr/bin/python3
import sys
import psutil
import datetime
import time
import argparse
import subprocess
import json
import os


# Directory name constants
__CSV_DIR__ = "csv"
__PLT_DIR__ = "plot"
__SUM_DIR__ = "stats"
# Conversion const
__MB__ = 2**20 # const for converting bytes to mega bytes
# HTML report template
__HTML_TEMPLATE__ = """<html><head>
<title>$(test_id) performance report</title>
<style>
body { font-family: Arial, Helvetica, sans-serif; padding: 1em;}    
table.summary { border: 2px solid #FFFFFF; text-align: left; border-collapse: collapse;}
table.summary td, table.summary th { border: 0px solid #FFFFFF; padding: 3px 4px;}    
h1 { font-size: 2em; }
h2 { font-size: 1.3em; }
</style></head>
<body>
<div class="title"><h1>$(test_id) performance summary</h1><hr></div>
<h2>Summary</h2>
<table class="summary"><tbody>
$(summary_table)
</tbody></table>
<div class="plots"><h2>Plots</h2>
<img src="plot/$(test_id)_cpu_usage.png"><img src="plot/$(test_id)_memory_usage.png"><img src="plot/$(test_id)_IO_usage.png">
</div></body></html>"""


# Simple class definition for statistics and paths
class ProcessStats:
    """
    Process profiling statistics class
    """
    def __init__(self):
        """Init ProcessStats."""
        self.time = []
        self.cpu_time = []
        self.cpu_perc = []
        self.memory = []
        self.threads = []
        self.io_write = []
        self.io_read = []
        self.start_time = time.time()

    def update(self, process):
        """
        Updates process statistics.

        Parameters
        ----------
         - process: psutils.process to profile
        """
        io_counters = process.io_counters() # use system wide counters (not the process one) 
        self.io_read.append(io_counters[0]) # read_bytes
        self.io_write.append(io_counters[1]) # write_bytes
        self.memory.append(int(round(process.memory_info().rss/__MB__))) # memory
        self.cpu_perc.append(int(process.cpu_percent())) # cpu usage
        self.cpu_time.append(process.cpu_times().user) # cpu time
        self.threads.append(process.num_threads()) # num threads
        self.time.append(int(round(1000*(time.time() - self.start_time)))) # sampling time

    def summary(self):
        """
        compute statistics summary and print/save it as dict structure
        """
        N = len(self.time)
        summary = {
            'duration': {
                'value' : self.time[-1],
                'unit'  : 'ms',
            },
            'memory': {
                'unit'    : 'Mb',
                'max'     : max(self.memory),
                'average' : sum(self.memory) / N,
            },
            'cpu_time': {
                'value': max(self.cpu_time),
                'unit' : 's',
            },
            'cpu_usage': {
                'unit'    : '%',
                'max'     : max(self.cpu_perc),
                'average' : sum(self.cpu_perc) / N,
            },
            'io': {
                'write' : max(self.io_write),
                'read'  : max(self.io_read),
                'unit'  : '',
            }, 
            'threads': {
                'unit'    : '',
                'max'     : max(self.threads),
                'average' : sum(self.threads) / N,
                'min'     : min(self.threads),
            },
        }
        return summary

    def csv(self):
        """
        generates the csv string for the stats
        """
        # Write out results (io or file)
        s = f'#start time: {self.start_time}\n'
        s += f'#cores:{psutil.cpu_count()}\n' # store number of CPU  
        s += '#time(ms), memory(Mb), CPU(s), CPU(%), Threads, Read IO (#), Write IO (#)\n' # columns label
        for i in range(len(self.time)): # iterate entries
            # create comma separated row
            s += f'{self.time[i]},{self.memory[i]},{self.cpu_time[i]},{self.cpu_perc[i]},{self.threads[i]},{self.io_read[i]},{self.io_write[i]}\n' 
        return s


def __generate_report_table_row__(key, value, unit):
    """generates a row for the summary table of the html report."""
    return f"<tr><td><b>{key}:</b></td><td>{value:0.2f} {unit}</td></tr>"

class ReportOut:
    """Report and output generation class"""  
    def __init__(self, output_arg):
        self.__file_mode__ = output_arg is not None
        if self.__file_mode__:
            # init the path 
            self.path_base = os.path.split(output_arg)[0]
            self.path_csv = os.path.join(self.path_base, __CSV_DIR__) 
            self.path_smm = os.path.join(self.path_base, __SUM_DIR__) 
            self.path_plt = os.path.join(self.path_base, __PLT_DIR__) 
            self.path_fname = os.path.split(output_arg)[1]
            # try to create CSV folder and Plot folder
            if not os.path.exists(self.path_csv):
                os.mkdir(self.path_csv)
            if not os.path.exists(self.path_plt):
                os.mkdir(self.path_plt)  
            if not os.path.exists(self.path_smm):
                os.mkdir(self.path_smm)   

    def csv(self, csv_string):
        """save or display the csv output"""
        if not self.__file_mode__: # print 
            print(csv_string, end='')
        else: # save to file
            with open(os.path.join(self.path_csv, self.path_fname + ".csv"), 'w') as f:
                f.write(csv_string)

    def summary(self, smm_dict):
        """save or display summary structure"""
        s = json.dumps(smm_dict) # generate json string
        if self.__file_mode__:
            with open(os.path.join(self.path_smm, self.path_fname + ".json"), 'w') as f:
                f.write(s)
        else:
            print(s)

    def plot(self, stats):
        """
        Plot process statistics using matplotlib.
        """
        # import required library
        import matplotlib.pyplot as plt

        # plot cpu usage 
        fig = plt.figure(figsize=(10, 7))
        plt.plot(stats.time, stats.cpu_perc)
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("CPU Usage (%)")
        plt.grid(alpha=0.5)
        plt.title("CPU Usage")
        if self.__file_mode__:
            plt.savefig(os.path.join(self.path_plt, self.path_fname+"_cpu_usage.png"))

        # plot memory usage
        fig = plt.figure(figsize=(10, 7))
        plt.plot(stats.time, stats.memory)
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("Memory (Mb)")
        plt.grid(alpha=0.5)
        plt.title("Memory Usage")
        if self.__file_mode__:
            plt.savefig(os.path.join(self.path_plt, self.path_fname+"_memory_usage.png"))

        # plot io activity
        fig = plt.figure(figsize=(10, 7))
        plt.plot(stats.time, stats.io_read, label='Read Count')
        plt.plot(stats.time, stats.io_write, label='Write Count')
        plt.legend()
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("Counter")
        plt.grid(alpha=0.5)
        plt.title("Disk IO Activity")
        if self.__file_mode__:
            plt.savefig(os.path.join(self.path_plt, self.path_fname+"_IO_usage.png"))

        # show results if no output is defined
        if not self.__file_mode__:
            plt.show()

    def html_report(self, summary, include_plot):
        if not self.__file_mode__:
            return
        html = __HTML_TEMPLATE__.replace("$(test_id)", self.path_fname)
        summ_table = __generate_report_table_row__("Process duration", summary['duration']['value'], summary['duration']['unit']) 
        summ_table += __generate_report_table_row__("CPU total time", summary['cpu_time']['value'], summary['cpu_time']['unit']) 
        summ_table += __generate_report_table_row__("CPU average usage", summary['cpu_usage']['average'], summary['cpu_usage']['unit']) 
        summ_table += __generate_report_table_row__("CPU max usage", summary['cpu_usage']['max'], summary['cpu_usage']['unit'])
        summ_table += __generate_report_table_row__("Memory average usage", summary['memory']['average'], summary['memory']['unit'])
        summ_table += __generate_report_table_row__("Memory max usage", summary['memory']['max'], summary['memory']['unit'])
        html = html.replace('$(summary_table)', summ_table)
        with open(os.path.join(self.path_base, 'report_perf_'+self.path_fname+'.html'), 'w') as f:
            f.write(html)


def __split_command_args__(command):
    """
    splits command in list of arguments.
    """
    args = []
    status = True
    token = ""
    for c in command:
        if c == " ":
            if status:
                if len(token) > 0:
                    args.append(token)
                token = ""
            else:
                token += " "
        elif c == '"':
            status = not status
            if status:
                if len(token) > 0:
                    args.append(token)
                token = ""
        else:
            token += c
    if len(token)>0:
        args.append(token)
    return args


def __arguments__():
    """
    parse arguments passed by the command line 
    """
    # setup arg parser
    parser = argparse.ArgumentParser()

    parser.add_argument('command', help="command to profile")
    parser.add_argument('--frequence', default=500, help="sampling period in ms")
    parser.add_argument('-o', default=None, help="save results to file")
    parser.add_argument('-w', choices=[True, False], default=False, help="wait time before starting profiling [default=True]")
    parser.add_argument('-c', default=False, help="profile children flag [default=True]", choices=[True, False])
    parser.add_argument('--plot', default=True, help="plot perforamnces (save if save file setted)", choices=[True, False])
    parser.add_argument('--report', default=True, help="produce html report", choices=[True, False])

    # parse arguments
    return parser.parse_args()


def main():
    """
    main entry point of the profiler
    """
    # parse_arguments
    args = __arguments__()
    # split command in sub parts
    command = __split_command_args__(args.command)
        
    T = args.frequence/1000.0 # convert period from ms to s
    END_STATUS = set([psutil.STATUS_STOPPED, psutil.STATUS_DEAD, psutil.STATUS_ZOMBIE]) # set of possible end status

    # execute the command and retrive the PID
    proc = subprocess.Popen(__split_command_args__(args.command))
    PID = proc.pid

    # wait some time according to arguments
    if args.w:
        time.sleep(2)

    # check if porcessing (still) exists
    if not psutil.pid_exists(PID):
        print("Process not found...")
        sys.exit(-1)

    # get process
    process = psutil.Process(PID)
    if args.c: # if profiling on children process try to get children process
        chld = process.children()
        process = process if len(chld) == 0 else chld[0]

    # initilize results variables
    PID = process.pid
    p_stats = ProcessStats()
    while psutil.pid_exists(PID) and process.status() not in END_STATUS: # while process is running
        p_stats.update(process) # update stats
        # TODO: Evaluate an adaptive sleep using statistics to regulate the timer
        time.sleep(T) # wait for next sampling

    # Output
    output = args.o
    # initialize path structure and make output directories
    report_io = ReportOut(output)
    # generate csv string and display/store it
    report_io.csv(p_stats.csv())
    # compute and save/display statistic summary (max, average...) 
    summary = p_stats.summary()
    # display/store summary
    report_io.summary(summary)

    # plot results if needed 
    # NOTE: only import matplotlib library here to avoid including it and limiting the functionality
    # when not needed
    if args.plot:
        report_io.plot(p_stats)
    # generate html report if required using summary (and plots)
    if args.report:
        report_io.html_report(summary, args.plot)


if __name__ == "__main__":
    main()