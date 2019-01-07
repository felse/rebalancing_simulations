#!/bin/bash
# number of servers per configuration
num_osds=32
# capacities of servers
osd_capacities='355,466'
# bandwidths of servers. make sure that the number of capacities matches the number of bandwithds (the lists should have the same length)
osd_bandwidth='600,150'
# total average usage of the available simulated capacities
target_load=0.7
# number of simulations to be executed
repetitions=1000

for folder_file in `ls split_sizes_all_geq*`;
    do
    python -u Simulator.py $num_osds $osd_capacities $osd_bandwidth $folder_file $target_load $repetitions &
done
