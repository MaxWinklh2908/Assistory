def get_bare_name(name: str) -> str:
    # remove _C
    name = name[:-2]
    # remove prefix
    name = '_'.join(name.split('_')[1:])
    return name


def transform_to_dict(items: list):
    return {
        d['item']: d['amount']
        for d in items
    }
