giga_byte = 1024 * 1024


def generate_input_folders(input_file, min_folder_sizes_gb):
    with open(input_file) as f:
        content = f.readlines()
    content = [x.strip().split() for x in content]
    content = list(map(lambda x: (int(x[0]), x[1]), content))

    for min_folder_size in min_folder_sizes_gb:
        output = list(filter(lambda x: x[0] >= 1024 * 1024 * min_folder_size, content))
        string = ''
        for size, id in output:
            string += str(size) + '\t' + id + '\n'

        with open(input_file + '_geq_' + str(min_folder_size), 'w') as f:
            f.write(string)

generate_input_folders('split_sizes_all', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
