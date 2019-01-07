class SimulationResult(object):
    def __init__(self, total_folder_size, total_osd_capacity, total_osd_bandwidth,
                 initial_distribution_type, rebalancing_mechanism,
                 initial_makespan, rebalanced_makespan,
                 size_of_moved_folders, max_size_moved_per_osd):
        self.total_folder_size = total_folder_size
        self.total_osd_capacity = total_osd_capacity
        self.total_osd_bandwidth = total_osd_bandwidth
        self.initial_distribution_type = initial_distribution_type
        self.rebalancing_mechanism = rebalancing_mechanism
        self.initial_makespan = initial_makespan
        self.rebalanced_makespan = rebalanced_makespan
        self.size_of_moved_folders = size_of_moved_folders
        self.max_size_moved = max_size_moved_per_osd

    def get_csv_string(self):
        return str(self.total_folder_size) + ',' + \
               str(self.total_osd_capacity) + ',' + \
               str(self.total_osd_bandwidth) + ',' + \
               str(self.initial_distribution_type) + ',' + \
               str(self.rebalancing_mechanism) + ',' + \
               str(self.initial_makespan) + ',' + \
               str(self.rebalanced_makespan) + ',' + \
               str(round(100. * self.rebalanced_makespan / float(self.initial_makespan), 2)) + ',' + \
               str(self.size_of_moved_folders) + ',' + \
               str(round(100. * self.size_of_moved_folders / float(self.total_folder_size), 2)) + ',' + \
               str(self.max_size_moved)

    def __str__(self):
        string = "size: " + str(self.total_folder_size) + \
                 " cap: " + str(self.total_osd_capacity) + \
                 " init: " + str(self.initial_distribution_type) + \
                 " rebalanc: " + str(self.rebalancing_mechanism) + \
                 " ms befor: " + str(self.initial_makespan) + \
                 " ms after: " + str(self.rebalanced_makespan) + \
                 " of ms befor (%): " + str(round(100. * self.rebalanced_makespan /
                                                  float(self.initial_makespan), 2)) + \
                 " moved: " + str(self.size_of_moved_folders) + \
                 " of total size (%): " + str(round(100. * self.size_of_moved_folders /
                                                    float(self.total_folder_size), 2))

        return string


def get_csv_header():
    return "total_folder_size" + \
           ",total_osd_capacity" + \
           ",total_osd_bandwidth" + \
           ",initial_distribution_type" + \
           ",rebalancing_mechanism" + \
           ",initial_makespan" + \
           ",rebalanced_makespan" + \
           ",improvement_ratio_percent" + \
           ",total_size_moved" + \
           ",moved_size_percent" + \
           ",max_size_moved"
