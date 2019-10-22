#! /bin/bash

# output file
csvoutput=$1
# time variable
t=0.0
echo "#time (s), memory (Mb), CPU (s)" > $csvoutput
while :
do
	# cpu usage in ns
	cpu=`cat /sys/fs/cgroup/cpuacct/cpuacct.usage`
	# memory usage in bytes
	mem=`cat /sys/fs/cgroup/memory/memory.usage_in_bytes`
	# convert unit to human readable
	# memory in mb
	mem=`echo "scale=2; $mem / 1048576" | bc -l`
	# cpu time in seconds
	cpu=`echo "scale=2; $cpu / 10^9" | bc -l`
	# add lines to the csv file
	echo "$t,$mem,$cpu" >> $csvoutput
	# sleep 0.1s
	sleep 0.1
	# increment time variable
	t=`echo "scale=2; $t + 0.1" | bc -l`
done