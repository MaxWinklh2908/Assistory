import json
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('old_data_file')
parser.add_argument('new_data_file')
args = parser.parse_args()

DATA_PATH_OLD = args.old_data_file
DATA_PATH_NEW = args.new_data_file

with open(DATA_PATH_OLD, 'r') as fp:
    data = json.load(fp)
with open(DATA_PATH_NEW, 'r') as fp:
    data_new = json.load(fp)

for a in data:
    print()
    print(a)
    keys = set(data[a])
    keys_new = set(data_new[a])
    print('Not in old data:', sorted(keys_new - keys))
    print('Not in new data:', sorted(keys - keys_new))
