#! /usr/bin/python3
import sys
import psutil
import datetime
import time
import argparse
import subprocess
import os


# Directory name constants
__CSV_DIR__ = "csv"
__PLT_DIR__ = "plot"


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


def main():
    """
    main entry point of the profiler
    """
    # parse_arguments
    args = __arguments__()
    # split command in sub parts
    command = __split_command_args__(args.command)
    print("\nProfiling")
    print("=========")
    print(f"command: `{' '.join(command)}`")    
    print(f"output file: `{args.o}`\n") 
        
    MB = 2**20 # const for converting bytes to mega bytes
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
    cpu = [] # cpu time
    cpu_p = [] # cpu usage
    mem = [] # memory usage
    disk_read = [] # disk in usage
    disk_write = [] # disk out usage
    ts = [] # sampling time
    trds = [] # number of threads

    start_time = datetime.datetime.now()
    start_t = time.time()
    print(f'$$$ Starting profiling: {start_time}')
    while psutil.pid_exists(PID) and process.status() not in END_STATUS: # while process is running
        # TODO: found why the read 
        io_counters = psutil.disk_io_counters() # use system wide counters (not the process one) 
        disk_read.append(io_counters[2]/MB) # read_bytes
        disk_write.append(io_counters[3]/MB) # write_bytes
        mem.append(process.memory_info().rss/MB) # memory
        cpu_p.append(process.cpu_percent()) # cpu usage
        cpu.append(process.cpu_times().user) # cpu time
        trds.append(process.num_threads()) # num threads
        ts.append(int(round(1000*(time.time() - start_t)))) # sampling time
        # TODO: Evaluate an adaptive sleep using statistics to regulate the timer
        time.sleep(T) # wait for next sampling

    # Output
    output = args.o
    base_path = None
    csv_path = None
    plt_path = None
    file_name = None
    # if output is defined create needed structure
    if output is not None:
        # init base path
        base_path = os.path.split(output)[0]
        file_name = os.path.split(output)[1]
        csv_path = os.path.join(base_path, __CSV_DIR__) 
        plt_path = os.path.join(base_path, __PLT_DIR__)
        # try to create CSV folder and Plot folder
        if not os.path.exists(csv_path):
            os.mkdir(csv_path)
        if not os.path.exists(plt_path):
            os.mkdir(plt_path)  

    # Write out results (io or file)
    s = f'#start time: {start_time}\n'
    s += f'#cores:{psutil.cpu_count()}\n' # store number of CPU  
    s += '#time(ms), memory(Mb), CPU(s), CPU(%), Threads, Read IO, Write IO\n' # columns label
    for t, m, c, c_p, td, io_in, io_out in zip(ts, mem, cpu, cpu_p, trds, disk_read, disk_write): # iterate entries
        s += f'{t*1000},{m},{c},{c_p},{td},{io_in},{io_out}\n' # create comma separated row
    if output is None: # print 
        print(s, end='')
    else: # save to file
        with open(os.path.join(csv_path, file_name + ".csv"), 'w') as f:
            f.write(s)

    # plot results if needed 
    # NOTE: only import matplotlib library here to avoid including it and limiting the functionality
    # when not needed
    if args.p:

        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(10, 7))
        plt.plot(ts, cpu_p)
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("CPU Usage (%)")
        plt.grid(alpha=0.5)
        plt.title("CPU Usage")
        if output is not None:
            plt.savefig(os.path.join(plt_path, file_name+"_cpu_usage.svg"))
        
        fig = plt.figure(figsize=(10, 7))
        plt.plot(ts, mem)
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("Memory (Mb)")
        plt.grid(alpha=0.5)
        plt.title("Memory Usage")
        if output is not None:
            plt.savefig(os.path.join(plt_path, file_name+"_memory_usage.svg"))
        
        fig = plt.figure(figsize=(10, 7))
        plt.plot(ts, disk_read, label='Read')
        plt.plot(ts, disk_write, label='Write')
        plt.legend()
        plt.xlabel("Elapsed time (ms)")
        plt.ylabel("Activity (Mb)")
        plt.grid(alpha=0.5)
        plt.title("Disk IO Activity")
        if output is not None:
            plt.savefig(os.path.join(plt_path, file_name+"_IO_usage.svg"))
        
        if output is None:
            plt.show()

        # if output is not None:
            # create_html_report()


if __name__ == "__main__":
    main()