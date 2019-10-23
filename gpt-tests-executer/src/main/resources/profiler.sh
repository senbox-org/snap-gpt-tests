#! /bin/bash

# output file
csvoutput=$1
# time variable
start_t=`date +%s%N`
echo "#start time(ms): $start_t" > $csvoutput
echo "#time (s), memory (Mb), CPU (s)" >> $csvoutput
while :
do	
	# compute relative time
	t=`date +%s%N`
	t=`echo "($t - $start_t) / 1000000 " | bc`
	# cpu usage in ns
	cpu=`cat /sys/fs/cgroup/cpuacct/cpuacct.usage`
	# memory usage in bytes
	mem=`cat /sys/fs/cgroup/memory/memory.stat | grep "^rss " | cut -c 5-`
	# convert unit to human readable
	# memory in mb
	mem=`echo "scale=2; $mem / 1048576" | bc -l`
	# cpu time in seconds
	cpu=`echo "scale=2; $cpu / 10^9" | bc -l`
	# add lines to the csv file
	echo "$t,$mem,$cpu" >> $csvoutput
	# sleep 0.1s
	sleep 0.1
done