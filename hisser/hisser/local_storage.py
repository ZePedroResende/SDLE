import argparse
import json
import pickle


# Convert data to JSON
def __dataToJson(messages, following, vector_clock):
    data = {}
    data['messages'] = messages
    data['following'] = following
    data['vector_clock'] = vector_clock
    return json.dumps(data)


# Convert JSON to data
def __JsonToData(string):
    data = json.loads(string)
    return (data['messages'], data['following'], data['vector_clock'])


# Import data from file
def __importData(filename):
    try:
        with open(filename + '.p', "rb") as data_file:
            data = pickle.load( data_file )
            data_file.close()
            return data
    except Exception:
        pass


# Export data to file
def __exportData(data, filename):
    with open(filename + '.p', 'wb') as outfile:
        pickle.dump( data, outfile )
    outfile.close()


# load all data from file
def read_data(db_file):
    data = __importData(db_file)
    if data:
        return __JsonToData(data)

    return ([], [], {})


# save all data to the file
def save_data(messages, following, vector_clock,  db_file):
    data = __dataToJson(messages, following, vector_clock)
    __exportData(data, db_file)
