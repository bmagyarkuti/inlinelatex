"""
This module reads the configuration JSON. Make sure to point the config_file variable to
your location for config.json.
"""

config_file ='config.json'
import json


def read_json_from_file(json_file: str):
    with open(json_file) as json_object:
        json_dictionary = json.load(json_object)

    return (json_dictionary['token'], json_dictionary['username'], json_dictionary['host'],
            json_dictionary['remote_path'], json_dictionary['http_address'])

(token, username, host,
 remote_path, http_address) = read_json_from_file(config_file)
