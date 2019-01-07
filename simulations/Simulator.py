import copy
import random
import sys
from enum import Enum

from xtreemfs_client import folder
from xtreemfs_client import dataDistribution

import SimulationResult

osd_id_prefix = 'server'
osd_capacity_key = 'capacity'

GB = 1024 * 1024


def create_osd_id(index):
    """
    create an osd id string
    :param index:
    :return:
    """
    return osd_id_prefix + " " + str(index)


def create_osd_list(num_osds):
    """
    create a list of osd id strings
    :param num_osds:
    :param osd_capacities:
    :return:
    """
    test_osds = []
    for i in range(0, num_osds):
        test_osds.append(create_osd_id(i))
    return test_osds


def create_osd_information(num_osds_per_value, values):
    """
    :param num_osds_per_value:
    :param values:
    :return:
    """
    osd_information = {}
    i = 0
    for osd_capacity in values:
        for j in range(0, num_osds_per_value):
            osd_uuid = create_osd_id(i)
            osd_information[osd_uuid] = osd_capacity
            i += 1
    return osd_information


def add_folder_size_to_moved_size_osd_map(osd_uuid, folder_size, moved_osd_size_map):
    """
    add (in the sense of addition) folder_size to the value stored for osd_uuid in moved_osd_size_map and store the
    new value. if no value is stored, proceed as if the stored value was 0.
    :param osd_uuid:
    :param folder_size:
    :param moved_osd_size_map:
    :return:
    """
    if osd_uuid in moved_osd_size_map.keys():
        moved_osd_size_map[osd_uuid] += folder_size
    else:
        moved_osd_size_map[osd_uuid] = folder_size


def transform_simulation_results_to_csv_string(simulation_results):
    csv_string = ''
    for sim_result in simulation_results:
        csv_string += sim_result.get_csv_string()
        csv_string += '\n'

    return csv_string


class RebalancingMechanism(Enum):
    """
    enum class to represent different rebalancing algorithms
    """
    lpt_mean = 1
    move_one = 2
    two_step_optimal = 3
    two_step_random = 4


class FolderHistory(object):
    def __init__(self, folder_id, folder_size, containing_osd, folder_moved,
                 rebalanced_distribution, osd_rebalancing_limit):
        self.folder_id = folder_id
        self.folder_size = folder_size
        self.containing_osd = containing_osd
        self.folder_moved = folder_moved
        self.rebalanced_distribution = rebalanced_distribution
        self.osd_rebalancing_limit = osd_rebalancing_limit

    def __str__(self):
        str_map = {'folder_id': self.folder_id, 'folder_size': self.folder_size, 'containing_osd': self.containing_osd,
                   'folder_moved': self.folder_moved, 'rebalanced_distribution': self.rebalanced_distribution}
        return str(str_map)


class Simulation(object):
    def __init__(self, initial_distribution_type, reblancing_mechanism, lpt_factor,
                 initial_distribution, new_distribution):

        self.unmoved_str = '2_unmoved'
        self.moved_away_str = '1_moved_away'
        self.moved_here_str = '0_moved_here'

        self.initial_distribution_type = initial_distribution_type
        self.rebalancing_mechanism = reblancing_mechanism
        self.lpt_factor = lpt_factor
        self.initial_distribution = initial_distribution
        self.new_distribution = new_distribution

    def get_osd_rebalancing_limit(self):
        return self.initial_distribution.get_rebalance_limit(self.lpt_factor,
                                                             self.initial_distribution.get_total_folder_size())

    def get_folders_history(self):
        folders_initial_distr = []
        folders_new_distr = []
        for osd in self.initial_distribution.OSDs.values():
            for folder_id, folder_size in osd.folders.items():
                folder_moved = self.unmoved_str
                # check whether it is contained in the same OSD in the other distribution
                if not self.new_distribution.get_containing_osd(folder_id).uuid == osd.uuid:
                    folder_moved = self.moved_away_str
                folder_history = FolderHistory(folder_id, folder_size, osd.uuid, folder_moved, folder_moved,
                                               self.get_osd_rebalancing_limit())
                if folder_moved == self.moved_away_str:
                    folders_initial_distr.append(folder_history)
                else:
                    folders_initial_distr.append(folder_history)

        for osd in self.new_distribution.OSDs.values():
            for folder_id, folder_size in osd.folders.items():
                folder_moved = self.unmoved_str
                # check whether it is contained in the same OSD in the other distribution
                if not self.initial_distribution.get_containing_osd(folder_id).uuid == osd.uuid:
                    folder_moved = self.moved_here_str
                folder_history = FolderHistory(folder_id, folder_size, osd.uuid, folder_moved, folder_moved,
                                               self.get_osd_rebalancing_limit())
                if folder_moved == self.moved_here_str:
                    folders_new_distr.append(folder_history)
                else:
                    folders_new_distr.append(folder_history)

        folders_initial_distr.sort(key=lambda x: x.folder_size, reverse=True)
        folders_new_distr.sort(key=lambda x: x.folder_size, reverse=True)
        return (folders_initial_distr, folders_new_distr)


class Simulator(object):
    """
    class to simulate rebalancing algorithms
    """

    def __init__(self, input_file, num_osds, osd_capacities, target_load=0.7):
        self.folders = []
        self.total_folder_size = 0
        self.read_folders(input_file)
        self.folder_map = {}
        self.total_num_osds = num_osds
        self.osd_capacities = osd_capacities

        # scale folder size such that we meet the target_load
        average_osd_capacity = sum(self.osd_capacities) / len(self.osd_capacities)
        total_osd_capacity = average_osd_capacity * self.total_num_osds
        scaling_factor = target_load * (total_osd_capacity / self.total_folder_size)

        for a_folder in self.folders:
            a_folder.size = round(a_folder.size * scaling_factor)

        self.total_folder_size = sum(list(map(lambda x: x.size, self.folders)))
        print("scaling factor to meet target_load of " + str(target_load) + ": " + str(scaling_factor))
        print("new total folder size: " + str(self.total_folder_size))

        for a_folder in self.folders:
            self.folder_map[a_folder.id] = a_folder.size

        # list of pairs (initial_distribution, rebalanced_distributions)
        self.remembered_simulations = []

        self.osd_capacities_map = None
        self.osd_bandwidths_map = None

    def read_folders(self, input_file):
        """
        read folders that will be used for simulation
        :return:
        """
        with open(input_file) as f:
            content = f.readlines()
        content = [x.strip().split() for x in content]

        current_id = 0
        total_size = 0
        for line in content:
            size = int(line[0])
            total_size += size
            self.folders.append(folder.Folder(current_id, size, ''))
            current_id += 1

        self.total_folder_size = total_size

        print("number of folders: " + str(len(self.folders)))
        print("total folder size: " + str(self.total_folder_size))

    def create_empty_distribution(self, set_capacities=False, set_bandwidths=True):
        distribution = dataDistribution.DataDistribution()
        distribution.add_osd_list(create_osd_list(self.total_num_osds))
        if set_capacities:
            assert self.osd_capacities_map is not None
            distribution.set_osd_capacities(self.osd_capacities_map)
        if set_bandwidths:
            assert self.osd_bandwidths_map is not None
            distribution.set_osd_bandwidths(self.osd_bandwidths_map)

        return distribution

    def create_lpt_distribution(self):
        """
        create an LPT balanced distribution: first, create OSDs with given capacities and number;
        then, add all folders in self.folders to them using the LPT algorithm.
        :param num_osds:
        :param osd_capacities:
        :return:
        """
        distribution = self.create_empty_distribution()
        distribution.add_folders(self.folders)
        return distribution

    def create_totally_random_distribution(self):
        """
        create a totally random distribution. osd capacities are ignored.
        :param num_osds:
        :param osd_capacities:
        :return:
        """
        distribution = self.create_empty_distribution()
        distribution.add_folders(self.folders, random_osd_assignment=True)
        return distribution

    def create_random_round_robin_distribution(self):
        """
        create a random round robin style distribution: each osd gets the same number of folders (insofar as it is possible),
        but folder sizes and osd capacities are ignored.
        :param num_osds:
        :param osd_capacities:
        :return:
        """
        distribution = self.create_empty_distribution()
        distribution.add_folders(self.folders, random_osd_assignment=True, ignore_folder_sizes=True)

        # manually update the folder sizes
        for a_folder in self.folders:
            distribution.update_folder(a_folder.id, a_folder.size)

        return distribution

    def create_random_distribution_respecting_osd_capacities(self):
        """
        create a random distribution that respects osd capacities.
        :param num_osds:
        :param osd_capacities:
        :return:
        """
        assert self.osd_capacities_map is not None
        distribution = self.create_empty_distribution(set_capacities=True)
        distribution.add_folders(self.folders, random_osd_assignment=True, ignore_osd_capacities=False)
        return distribution

    def get_simulation_result(self, distribution, initial_makespan, movements, creation_type, rebalancing_mechanism):
        """
        create a simulationResult object; calculate all necessary values.
        no simulation is done here!!!
        :param distribution:
        :param initial_makespan:
        :param movements:
        :param creation_type:
        :param rebalancing_mechanism:
        :return:
        """
        size_moved_per_osd = {}
        for osd_uuid in distribution.OSDs.keys():
            size_moved_per_osd[osd_uuid] = 0

        for movement in movements.keys():
            folder_size = self.folder_map[movement]
            add_folder_size_to_moved_size_osd_map(movements[movement][0], folder_size, size_moved_per_osd)
            add_folder_size_to_moved_size_osd_map(movements[movement][1], folder_size, size_moved_per_osd)

        return SimulationResult.SimulationResult(self.total_folder_size,
                                                 sum(self.osd_capacities_map.values()),
                                                 sum(self.osd_bandwidths_map.values()),
                                                 creation_type,
                                                 rebalancing_mechanism,
                                                 initial_makespan,
                                                 distribution.get_maximum_processing_time()[1],
                                                 sum(list(size_moved_per_osd.values())),
                                                 max(list(size_moved_per_osd.values())))

    def simulate_rebalancing(self, remember_distributions=False,
                             osd_capacities_map=None,
                             osd_bandwidths_map=None):
        """
        simulate multiple rebalancing algorithms based on the different parameters statically determined and given as
        function parameters
        :param remember_distributions:
        :param osd_bandwidths_map:
        :param num_osds:
        :param osd_capacities_map:
        :return:
        """
        self.osd_bandwidths_map = osd_bandwidths_map

        rebalancing_mechanisms = [RebalancingMechanism.lpt_mean,
                                  RebalancingMechanism.move_one,
                                  RebalancingMechanism.two_step_optimal,
                                  RebalancingMechanism.two_step_random]
        # rebalancing_mechanisms = [RebalancingMechanism.two_step]
        #lpt_mean_rebalance_factors = [1.05, 1.04, 1.03, 1.02, 1.01, 1.0, .99, .98, ]
        lpt_mean_rebalance_factors = [1.10, 1.05, 1.00, .95, .90]
        #lpt_mean_rebalance_factors = [1.1, 1.0, 0.8]
        # lpt_mean_rebalance_factors = [1]

        distribution_0 = ('lpt', self.create_lpt_distribution())
        distribution_1 = ('totrand', self.create_totally_random_distribution())
        distribution_2 = ('rand_r_r', self.create_random_round_robin_distribution())
        self.osd_capacities_map = osd_capacities_map
        distribution_3 = (
            'caprand', self.create_random_distribution_respecting_osd_capacities())
        # distributions = [distribution_0, distribution_1, distribution_2, distribution_3]
        distributions = [distribution_3]

        simulation_results = []

        for creation_type, distribution in distributions:
            _, initial_makespan = distribution.get_maximum_processing_time()

            if creation_type == 'lpt':
                continue
            for rebalancing_mechanism in rebalancing_mechanisms:
                if rebalancing_mechanism == RebalancingMechanism.lpt_mean:
                    for rebalancing_factor in lpt_mean_rebalance_factors:
                        working_copy = copy.deepcopy(distribution)
                        movements = working_copy.rebalance_lpt(rebalance_factor=rebalancing_factor)
                        sim_result = self.get_simulation_result(working_copy, initial_makespan, movements,
                                                                creation_type,
                                                                rebalancing_mechanism.name + str(rebalancing_factor))
                        simulation_results.append(sim_result)
                        if remember_distributions:
                            self.remembered_simulations.append(Simulation(creation_type,
                                                                          sim_result.rebalancing_mechanism,
                                                                          rebalancing_factor,
                                                                          distribution, working_copy))

                elif rebalancing_mechanism == RebalancingMechanism.move_one:
                    working_copy = copy.deepcopy(distribution)
                    movements = working_copy.rebalance_one_folder()
                    sim_result = self.get_simulation_result(working_copy, initial_makespan, movements,
                                                            creation_type, rebalancing_mechanism.name)
                    simulation_results.append(sim_result)
                    if remember_distributions:
                        self.remembered_simulations.append(Simulation(creation_type,
                                                                      sim_result.rebalancing_mechanism,
                                                                      1,
                                                                      distribution, working_copy))
                elif rebalancing_mechanism == RebalancingMechanism.two_step_optimal:
                    working_copy = copy.deepcopy(distribution)
                    movements = working_copy.rebalance_two_steps_optimal_matching()
                    sim_result = self.get_simulation_result(working_copy, initial_makespan, movements,
                                                            creation_type, str(rebalancing_mechanism.name))
                    simulation_results.append(sim_result)
                    if remember_distributions:
                        self.remembered_simulations.append(Simulation(creation_type,
                                                                      sim_result.rebalancing_mechanism,
                                                                      1,
                                                                      distribution, working_copy))
                elif rebalancing_mechanism == RebalancingMechanism.two_step_random:
                    working_copy = copy.deepcopy(distribution)
                    movements = working_copy.rebalance_two_steps_random_matching()
                    sim_result = self.get_simulation_result(working_copy, initial_makespan, movements,
                                                            creation_type, str(rebalancing_mechanism.name))
                    simulation_results.append(sim_result)
                    if remember_distributions:
                        self.remembered_simulations.append(Simulation(creation_type,
                                                                      sim_result.rebalancing_mechanism,
                                                                      1,
                                                                      distribution, working_copy))

        return simulation_results

    def get_lower_bound_on_makespan(self):
        """

        :return:
        """
        distribution = self.create_random_distribution_respecting_osd_capacities()
        return SimulationResult.SimulationResult(self.total_folder_size,
                                                 sum(self.osd_capacities_map.values()),
                                                 sum(self.osd_bandwidths_map.values()),
                                                 'caprand',
                                                 'optimal',
                                                 -1,
                                                 distribution.get_lower_bound_on_makespan(),
                                                 -1,
                                                 -1)

    def get_distributions_as_csv(self):
        """
        generate plot data to compare old osd loads to rebalanced osd loads
        there is no distinction between single folders on each osd
        example for one distribution pair with 2 OSDs:
            distr_pair_id, initial_type, rebalancing_mechanism, rebalanced, osd_id, osd_load
            1,caprand,lpt_mean,false,osd_0, 100
            1,caprand,lpt_mean,false,osd_1, 50
            1,caprand,lpt_mean,true,osd_0,75
            1,caprand,lpt_mean,true,osd_1,75
        :return:
        """
        if len(self.remembered_simulations) == 0:
            return ""

        csv_string = "distr_pair_id,initial_type,rebalancing_mechanism,lpt_factor," \
                     "rebalanced,osd_id,folder_id,moved,osd_load\n"
        distr_pair_id = 0

        def append_csv_line(initial_type, rebalancing_mechanism, lpt_factor,
                            rebalanced, osd_uuid, folder_id, moved, value):
            nonlocal csv_string
            csv_string += str(distr_pair_id) \
                          + ',' + str(initial_type) \
                          + ',' + str(rebalancing_mechanism) \
                          + ',' + str(lpt_factor) \
                          + ',' + str(rebalanced) \
                          + ',' + str(osd_uuid) \
                          + ',' + str(folder_id) \
                          + ',' + str(moved) \
                          + ',' + str(value) \
                          + '\n'

        for simulation in self.remembered_simulations:
            folders_histories = simulation.get_folders_history()
            for folder_history in folders_histories[0]:
                append_csv_line(simulation.initial_distribution_type,
                                simulation.rebalancing_mechanism,
                                folder_history.osd_rebalancing_limit,
                                'initial',
                                folder_history.containing_osd,
                                folder_history.folder_id,
                                folder_history.folder_moved,
                                folder_history.folder_size)
            for folder_history in folders_histories[1]:
                append_csv_line(simulation.initial_distribution_type,
                                simulation.rebalancing_mechanism,
                                folder_history.osd_rebalancing_limit,
                                'rebalanced',
                                folder_history.containing_osd,
                                folder_history.folder_id,
                                folder_history.folder_moved,
                                folder_history.folder_size)
            distr_pair_id += 1
        return csv_string


def create_simulation_results(num_osds, osd_capacities, osd_bandwidths, folder_file, target_load, repetitions):
    assert len(osd_capacities) == len(osd_bandwidths)
    
    output_file_name = 'step_5_'
    output_file_name += 'osds_' + str(num_osds)
    output_file_name += '_caps_'

    # we want to scale the capacities such that the quotient (total_folder_size/total_osd_capacity) is 75%
    i = 0
    for capacity in osd_capacities:
        if i > 0:
            output_file_name += '-'
        else:
            i = 1
        output_file_name += str(capacity)

    output_file_name += '_bws_'
    i = 0
    for bandwidth in osd_bandwidths:
        if i > 0:
            output_file_name += '-'
        else:
            i = 1
        output_file_name += str(bandwidth)
    output_file_name += '_' + folder_file + '_'
    output_file_name += str(target_load)
    output_file_name += '_reps_' + str(repetitions)
    output_file_name += '.csv'

    osd_bandwidths = list(map(lambda x: x * GB, osd_bandwidths))
    osd_capacities = list(map(lambda x: x * GB, osd_capacities))

    print("total osd capacity: " + str(sum(osd_capacities) * num_osds))

    simulator = Simulator(folder_file, num_osds * len(osd_capacities), osd_capacities, target_load=target_load)
    simulation_results = []
    for i in range(0, repetitions):
        print("simulation %d..." % (i))
        simulation_results.extend(
            simulator.simulate_rebalancing(osd_capacities_map=create_osd_information(num_osds, osd_capacities),
                                           osd_bandwidths_map=create_osd_information(num_osds, osd_bandwidths),
                                           remember_distributions=(repetitions <= 1)))

    simulation_results.append(simulator.get_lower_bound_on_makespan())

    if repetitions > 1:
        with open(output_file_name, 'w') as file:
            file.write(SimulationResult.get_csv_header())
            file.write('\n')
            file.write(transform_simulation_results_to_csv_string(simulation_results))

    else:
        csv_string = simulator.get_distributions_as_csv()
        with open(output_file_name, 'w') as file:
            file.write(csv_string)


args = sys.argv
print('args: ' + str(args))

if len(args) is not 7:
    print('specify arguments in the format: num_osds, osd_capacities, '
          'osd_bandwidths, folder_file, scaling_factor, repetitions')
    sys.exit(1)

num_osds = int(args[1])
osd_capacities = list(map(lambda x: int(x), args[2].split(',')))
osd_bandwidths = list(map(lambda x: int(x), args[3].split(',')))
folder_file = args[4]
target_load = float(args[5])
repetitions = int(args[6])

random.seed(10)

create_simulation_results(num_osds, osd_capacities, osd_bandwidths, folder_file, target_load, repetitions)
