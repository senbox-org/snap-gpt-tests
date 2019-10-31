#! /usr/bin/python3
import sys
import psutil
import datetime
import time
import argparse
import subprocess
import json
import os
from collections import namedtuple


# Directory name constants
__CSV_DIR__ = "csv"
__PLT_DIR__ = "plot"
__SUM_DIR__ = "stats"
# Conversion const
__MB__ = 2**20 # const for converting bytes to mega bytes


# Simple class definition for statistics and paths
ProcessStats = namedtuple('ProcessStats', ['time', 'cpu_time', 'cpu_perc', 'memory', 'threads', 'io_write', 'io_read', 'start_time'])
ReportPath = namedtuple("ReportPath", ['csv', 'plt', 'base', 'summary', 'file_name'])


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
    parser.add_argument('-f', default=100, help="sampling period in ms")
    parser.add_argument('-o', default=None, help="save results to file")
    parser.add_argument('-w', choices=[True, False], default=False, help="wait time before starting profiling [default=True]")
    parser.add_argument('-c', default=False, help="profile children flag [default=True]", choices=[True, False])
    parser.add_argument('-p', default=True, help="plot perforamnces (save if save file setted)", choices=[True, False])

    # parse arguments
    return parser.parse_args()


def __generate_csv__(stats):
    """
    generates the csv string for the stats
    """
    # Write out results (io or file)
    s = f'#start time: {stats.start_time}\n'
    s += f'#cores:{psutil.cpu_count()}\n' # store number of CPU  
    s += '#time(ms), memory(Mb), CPU(s), CPU(%), Threads, Read IO, Write IO\n' # columns label
    for i in range(len(stats.time)): # iterate entries
        s += f'{stats.time[i]},{stats.memory[i]},{stats.cpu_time[i]},{stats.cpu_perc[i]},{stats.threads},{stats.io_read},{stats.io_write}\n' # create comma separated row
    return s


def __stats_summary__(stats, path):
    """
    compute statistics summary and print/save it as json structure
    """
    N = len(stats.time)
    summary = {
        'duration': {
            'value' : stats.time[-1],
            'unit'  : 'ms',
        },
        'memory': {
            'unit'    : 'Mb',
            'max'     : max(stats.memory),
            'average' : sum(stats.memory) / N,
        },
        'cpu_time': {
            'value': max(stats.cpu_time),
            'unit' : 's',
        },
        'cpu_usage': {
            'unit'    : '%',
            'max'     : max(stats.cpu_perc),
            'average' : sum(stats.cpu_perc) / N,
        },
        'io': {
            'write' : max(stats.io_write),
            'read'  : max(stats.io_read),
            'unit'  : 'Mb',
        }, 
        'threads': {
            'unit'    : '',
            'max'     : max(stats.threads),
            'average' : sum(stats.threads) / N,
            'min'     : min(stats.threads),
        },
    }
    res = json.dumps(summary, indent=4)
    if path is None:
        print(res)
    else:
        fp = os.path.join(path.summary, path.file_name + '_sum.json')
        with open(fp, 'w') as f:
            f.write(res)
    return summary


def __updates_stats__(process, stat):
    """
    Update process statistics with current process status.
    """
    # TODO: found why the read 
    io_counters = psutil.disk_io_counters() # use system wide counters (not the process one) 
    stat.io_read.append(io_counters[2]/__MB__) # read_bytes
    stat.io_write.append(io_counters[3]/__MB__) # write_bytes
    stat.memory.append(process.memory_info().rss/__MB__) # memory
    stat.cpu_perc.append(process.cpu_percent()) # cpu usage
    stat.cpu_time.append(process.cpu_times().user) # cpu time
    stat.threads.append(process.num_threads()) # num threads
    stat.time.append(int(round(1000*(time.time() - stat.start_time)))) # sampling time
    return stat


def __init_path__(output_path):
    """
    Initializes ReportPath structure and create the needed
    folders.
    """
    if output_path is None:
        return None
    path = ReportPath()
    # init base path
    path.base = os.path.split(output_path)[0]
    path.file_name = os.path.split(output_path)[1]
    path.csv = os.path.join(path.base, __CSV_DIR__) 
    path.plt = os.path.join(path.base, __PLT_DIR__)
    path.summary = os.path.join(path.base, __SUM_DIR__)
    # try to create CSV folder and Plot folder
    if not os.path.exists(path.csv):
        os.mkdir(path.csv)
    if not os.path.exists(path.plt):
        os.mkdir(path.plt)  
    if not os.path.exists(path.summary):
        os.mkdir(path.summary)      
    return path


def __plot__(stats, path=None):
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
    if path is not None:
        plt.savefig(os.path.join(path.plt, path.file_name+"_cpu_usage.svg"), format="svg")
    
    # plot memory usage
    fig = plt.figure(figsize=(10, 7))
    plt.plot(stats.time, stats.memory)
    plt.xlabel("Elapsed time (ms)")
    plt.ylabel("Memory (Mb)")
    plt.grid(alpha=0.5)
    plt.title("Memory Usage")
    if path is not None:
        plt.savefig(os.path.join(path.plt, path.file_name+"_memory_usage.svg"), format="svg")
    
    # plot io activity
    fig = plt.figure(figsize=(10, 7))
    plt.plot(stats.time, stats.io_read, label='Read')
    plt.plot(stats.time, stats.io_write, label='Write')
    plt.legend()
    plt.xlabel("Elapsed time (ms)")
    plt.ylabel("Activity (Mb)")
    plt.grid(alpha=0.5)
    plt.title("Disk IO Activity")
    if path is not None:
        plt.savefig(os.path.join(path.plt, path.file_name+"_IO_usage.svg"), format="svg")

    # show results if no output is defined
    if path is None:
        plt.show()


def main():
    """
    main entry point of the profiler
    """
    # parse_arguments
    args = __arguments__()
    # split command in sub parts
    command = __split_command_args__(args.command)
        
    T = args.f/1000.0 # convert period from ms to s
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
    p_stats = ProcessStats(time=[],cpu_time=[], cpu_perc=[], memory=[], threads=[], io_write=[], io_read=[])

    p_stat.start_time = datetime.datetime.now()
    start_t = time.time()
    while psutil.pid_exists(PID) and process.status() not in END_STATUS: # while process is running
        p_stat = __updates_stats__(process, p_stats)
        # TODO: Evaluate an adaptive sleep using statistics to regulate the timer
        time.sleep(T) # wait for next sampling

    # Output
    output = args.o
    # initialize path structure and make output directories
    report_path = __init_path__(output)

    # Write out results (io or file)
    csv_string = __generate_csv__(p_stats) # generate csv string
    if output is None: # print 
        print(csv_string, end='')
    else: # save to file
        with open(os.path.join(report_path.csv, report_path.file_name + ".csv"), 'w') as f:
            f.write(csv_string)

    # compute and save/display statistic summary (max, average...)
    __stats_summary__(p_stats, report_path)

    # plot results if needed 
    # NOTE: only import matplotlib library here to avoid including it and limiting the functionality
    # when not needed
    if args.p:
        __plot__(p_stats, report_path)
        # if output is not None:
            # create_html_report()


if __name__ == "__main__":
    main()