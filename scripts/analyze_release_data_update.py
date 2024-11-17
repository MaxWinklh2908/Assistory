import json

DATA_PATH_OLD = 'data/data copy.json'
DATA_PATH_NEW = 'data/data.json'

with open(DATA_PATH_OLD, 'r') as fp:
    data = json.load(fp)
with open(DATA_PATH_NEW, 'r') as fp:
    data_new = json.load(fp)

for a in data:
    print()
    print(a)
    keys = set(data[a])
    keys_new = set(data_new[a])
    print('Not in old data:', keys_new - keys)
    print('Not in new data:', keys - keys_new)
