#! /usr/bin/python3
import sys
import psutil
import datetime
import time
import argparse
import subprocess


def split_args(command):
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

# setup arg parser
parser = argparse.ArgumentParser()

parser.add_argument('command', help="command to profile")
parser.add_argument('-f', default=100, help="sampling period in ms")
parser.add_argument('-o', default=None, help="save results to file")
parser.add_argument('-w', choices=[True, False], default=False, help="wait time before starting profiling [default=True]")
parser.add_argument('-c', default=False, help="profile children flag [default=True]", choices=[True, False])
parser.add_argument('-p', default=True, help="plot perforamnces (save if save file setted)", choices=[True, False])

# parse arguments
args = parser.parse_args()
# split command in sub parts
command = split_args(args.command)
print("\nProfiling")
print("=========")
print(f"command: `{' '.join(command)}`")    
print(f"output file: `{args.o}`\n") 
      
MB = 2**20 # const for converting bytes to mega bytes
T = args.f/1000.0 # convert period from ms to s
END_STATUS = set([psutil.STATUS_STOPPED, psutil.STATUS_DEAD, psutil.STATUS_ZOMBIE]) # set of possible end status

# execute the command and retrive the PID
proc = subprocess.Popen(split_args(args.command))
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
disk_in = [] # disk in usage
disk_out = [] # disk out usage
ts = [] # sampling time
trds = [] # number of threads

start_time = datetime.datetime.now()
start_t = time.time()
print(f'$$$ Starting profiling: {start_time}')
while psutil.pid_exists(PID) and process.status() not in END_STATUS: # while process is running
    io_counters = process.io_counters() 
    disk_in.append( io_counters[2]/MB) # read_bytes
    disk_out.append(io_counters[3]/MB) # write_bytes
    mem.append(process.memory_info().rss/MB) # memory
    cpu_p.append(process.cpu_percent()) # cpu usage
    cpu.append(process.cpu_times().user) # cpu time
    trds.append(process.num_threads()) # num threads
    ts.append(int(round(1000*(time.time() - start_t)))) # sampling time
    # TODO: Evaluate an adaptive sleep using statistics to regulate the timer
    time.sleep(T) # wait for next sampling

# Output
output = args.o

# Write out results (io or file)
s = f'#start time: {start_time}\n'
s += f'#cores:{psutil.cpu_count()}\n' # store number of CPU  
s += '#time(ms), memory(Mb), CPU(s), CPU(%), Threads, Read IO, Write IO\n' # columns label
for t, m, c, c_p, td, io_in, io_out in zip(ts, mem, cpu, cpu_p, trds, disk_in, disk_out): # iterate entries
    s += f'{t*1000},{m},{c},{c_p},{td},{io_in},{io_out}\n' # create comma separated row
if output is None: # print 
    print(s, end='')
else: # save to file
    with open(output + ".csv", 'w') as f:
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
        plt.savefig(output+"_cpu_usage.png")
    
    fig = plt.figure(figsize=(10, 7))
    plt.plot(ts, mem)
    plt.xlabel("Elapsed time (ms)")
    plt.ylabel("Memory (Mb)")
    plt.grid(alpha=0.5)
    plt.title("Memory Usage")
    if output is not None:
        plt.savefig(output+"_memory_usage.png")
    
    fig = plt.figure(figsize=(10, 7))
    plt.plot(ts, disk_in, label='In')
    plt.plot(ts, disk_out, label='Out')
    plt.legend()
    plt.xlabel("Elapsed time (ms)")
    plt.ylabel("IO (Mb)")
    plt.grid(alpha=0.5)
    plt.title("IO Activity")
    if output is not None:
        plt.savefig(output+"_IO_usage.png")
    
    if output is None:
        plt.show()
