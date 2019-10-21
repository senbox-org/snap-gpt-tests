#! /usr/bin/python3
import sys
import psutil
import time
import argparse
import subprocess

# setup arg parser
parser = argparse.ArgumentParser()

parser.add_argument('command')
parser.add_argument('-f', default=100, help="sampling period in ms")
parser.add_argument('-o', default=None, help="save results to file")
parser.add_argument('-w', choices=[True, False], default=True, help="wait time before starting profiling [default=True]")
parser.add_argument('-c', default=True, help="profile children flag [default=True]", choices=[True, False])

# parse arguments
args = parser.parse_args()
print("\nProfiling")
print("=========")
print(f"command: `{args.command}`")
print(f"output file: `{args.o}`\n") 
      
MB = 2**20 # const for converting bytes to mega bytes
T = args.f/1000.0 # convert period from ms to s
END_STATUS = set([psutil.STATUS_STOPPED, psutil.STATUS_DEAD, psutil.STATUS_ZOMBIE]) # set of possible end status

# execute the command and retrive the PID
proc = subprocess.Popen(args.command.split(' '))
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

t = 0 # profiling timer
print('$$$ Starting profiling...')
while psutil.pid_exists(PID) and process.status() not in END_STATUS: # while process is running
    io_counters = process.io_counters() 
    disk_in.append( io_counters[2]/MB) # read_bytes
    disk_out.append(io_counters[3]/MB) # write_bytes
    mem.append(process.memory_info().rss/MB) # memory
    cpu_p.append(process.cpu_percent()) # cpu usage
    cpu.append(process.cpu_times().user) # cpu time
    trds.append(process.num_threads()) # num threads
    ts.append(t) # sampling time
    time.sleep(T) # wait for next sampling
    t += T # increment timer

# Write out results (io or file)
s = f'#cores:{psutil.cpu_count()}\n' # save cpu number  
s += '#time(ms), memory(Mb), CPU(s), CPU(%), Threads, Read IO, Write IO\n' # columns label
for t, m, c, c_p, td, disk_in, disk_out in zip(ts, mem, cpu, cpu_p, trds, disk_in, disk_out): # iterate entries
    s += f'{t*1000},{m},{c},{c_p},{td},{disk_in},{disk_out}\n' # create comma separated row
if args.o is None: # print 
    print(s, end='')
else: # save to file
    with open(args.o, 'w') as f:
        f.write(s)
