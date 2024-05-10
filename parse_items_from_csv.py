import csv
import game


def parse_items(file_path: str):
    with open(file_path, 'r') as fp:
        data = fp.readlines()

    # Skip total row and header row
    data = data[2:]

    item_name2class_name = {
        item['name']: item['className']
        for item in game.data['items'].values()
    }

    resources_available = {
        item_name:0 for item_name in game.ITEMS
    }

    for row in csv.reader(data, delimiter=';'):
        item_name = row[0]
        if not item_name in item_name2class_name:
            print('Warning: Skip unknown item:', item_name)
            continue
        balance = float(row[3].replace(',', '.'))
        if balance <= 0:
            continue
        resources_available[item_name2class_name[item_name]] = balance

    return resources_available
        

if __name__ == '__main__':
    print(parse_items('../Autonation4.0.csv'))
