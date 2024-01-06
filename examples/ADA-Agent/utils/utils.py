import json

def read_jsonl(file_name):
    """
    Read a file with each line containing a JSON string representing a dictionary,
    and return a list of dictionaries.

    :param file_name: Name of the file to read from.
    :return: List of dictionaries.
    """
    dict_list = []
    with open(file_name, 'r') as file:
        for line in file:
            # Convert the JSON string back to a dictionary.
            dictionary = json.loads(line.rstrip('\n'))
            dict_list.append(dictionary)
    return dict_list

def write_jsonl(dict_list, file_name):
    """
    Write a list of dictionaries to a file, with each dictionary on a new line.

    :param dict_list: List of dictionaries to write to the file.
    :param file_name: Name of the file to write to.
    """
    with open(file_name, 'w') as file:
        for dictionary in dict_list:
            # Convert the dictionary to a JSON string.
            dict_str = json.dumps(dictionary)
            # Write the JSON string to the file followed by a new line character.
            file.write(dict_str + '\n')