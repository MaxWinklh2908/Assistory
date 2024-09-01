from argparse import ArgumentParser
from typing import List

import save_reader


class UncompressedReader(save_reader.SaveReader):

    def __init__(self, data: bytes, idx: int=0):
        super().__init__(data, idx)

    def read_component(self) -> dict:
        level_name = self.read_string()
        path_name = self.read_string()
        return {'level_name': level_name, 'path_name': path_name}

    def read_component_list(self, n: int) -> list:
        return [
            self.read_component()
            for _ in range(n)
        ]

    def read_sublevel(self) -> dict:
        sublevel_name = self.read_string()
        val = self.read_int() # correct
        return {'sublevel_name': sublevel_name, 'value': val}

    def read_sublevels(self) -> list:
        name = self.read_string()
        self.idx +=4 # for maingrid is 12800, landscapegrid is 51200, explorationgrid is 20480, foliagegrid is 12798
        self.idx +=4 # for maingrid is 210220737, landscapegrid is 0, explorationgrid is 2681457155, foliagegrid is 0
        sublevel_cnt = self.read_int()
        sublevels = [
            self.read_sublevel()
            for _ in range(sublevel_cnt)
        ]
        return {'name': name, 'sublevels': sublevels}

    def read_actor_header(self) -> dict:
        val = dict()
        val['type_path'] = self.read_string()
        val['root_object'] = self.read_string()
        val['instance_name'] = self.read_string()
        val['needs_transform'] = self.read_int() # needs transform ?
        val['rot_x'] = self.read_float()
        val['rot_y'] = self.read_float()
        val['rot_z'] = self.read_float()
        val['rot_w'] = self.read_float()
        val['pos_x'] = self.read_float()
        val['pos_y'] = self.read_float()
        val['pos_z'] = self.read_float()
        val['scale_x'] = self.read_float()
        val['scale_y'] = self.read_float()
        val['scale_z'] = self.read_float()
        val['placed'] = self.read_int() # was placed in level ?
        return val

    def read_component_header(self) -> dict:
        val = dict()
        val['type_path'] = self.read_string()
        val['root_object'] = self.read_string()
        val['instance_name'] = self.read_string()
        val['parent_actor_name'] = self.read_string()
        return val

    def read_object_header(self) -> dict:
        val = dict()
        val['start_idx'] = self.idx
        val['object_type'] = self.read_int()
        if val['object_type'] == 1:
            val.update(self.read_actor_header())
        elif val['object_type'] == 0:
            val.update(self.read_component_header())
        else:
            raise ValueError('Invalid object header type:', val['object_type'])
        # object_name = self.read_string()
        return val

    def read_object_headers(self) -> List[dict]:
        n_headers = self.read_int()
        object_headers = []
        for _ in range(n_headers):
            object_headers.append(self.read_object_header())
        return object_headers

    def read_object_reference(self) -> dict:
        val = dict()
        val['level_name'] = self.read_string()
        val['path_name'] = self.read_string()
        return val

    def read_object_references(self) -> list:
        n_collectables = self.read_int()
        collectables = []
        for _ in range(n_collectables):
            collectables.append(self.read_object_reference())
        return collectables

    def read_actor_object(self) -> dict:
        val = dict()
        original_idx = self.idx
        n_bytes = self.read_int() # including trailing bytes
        d = self.read_int()
        e = self.read_int()
        val['components'] = self.read_object_references()
        val['properties'] = self.read_properties()
        # apply trailing bytes
        if original_idx + n_bytes > self.idx:
            self.idx = original_idx + n_bytes
        return val
    
    def read_actor_object2(self) -> dict:
        # TODO: what is wrong with read_actor_object ?
        val = dict()
        original_idx = self.idx
        n_bytes = self.read_int() # including trailing bytes
        val['level_name'] = self.read_string()
        val['path_name'] = self.read_string()
        val['components'] = self.read_object_references()
        val['properties'] = self.read_properties()
        # apply trailing bytes
        if original_idx + n_bytes > self.idx:
            self.idx = original_idx + n_bytes
        return val
    
    def read_component_object(self) -> dict:
        val = dict()
        original_idx = self.idx
        n_bytes = self.read_int()
        val['properties'] = self.read_properties()
        # apply trailing bytes
        if original_idx + n_bytes > self.idx:
            self.idx = original_idx + n_bytes
        return val
    
    def read_object(self, object_type: int) -> dict:
        val = dict()
        val['start_idx'] = self.idx
        a = self.read_int() # 15/6 /3158584 (25282136)
        b = self.read_int() # 42/36
        c = self.read_int() # 0/1
        if object_type == 1:
            backupt_idx = self.idx
            try:
                val_actor_obj = self.read_actor_object()
            except ValueError:
                self.idx = backupt_idx
                val_actor_obj = self.read_actor_object2()
            val.update(val_actor_obj)
        elif object_type == 0:
            val.update(self.read_component_object())
        else:
            raise ValueError('Invalid object type: {object_type}')
        return val

    def read_level(self) -> dict:
        val = dict()
        val['sublevel_name'] = self.read_string()

        # headers and collectables
        n_bytes_h_c = self.read_int() # after padding
        self.idx += 4 # padding?
        original_idx = self.idx
        val['headers'] = self.read_object_headers()
        val['collectables'] = self.read_object_references()
        if original_idx + n_bytes_h_c != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_h_c} != {self.idx}')

        # objects
        n_bytes_objects = self.read_int() # after padding
        self.idx += 4 # padding?
        original_idx = self.idx
        objects = []
        for obj_header in val['headers']:
            objects.append(self.read_object(obj_header['object_type']))
        val['objects'] = objects
        self.idx += 4 # padding?
        if original_idx + n_bytes_objects != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_objects} != {self.idx}')

        val['second_collectables'] = self.read_object_references()

        return val

    def read_levels(self) -> List[dict]:
        n_levels = self.read_int()
        levels = []
        for i in range(n_levels):
            levels.append(self.read_level())
            # print(f'Level {i} at {self.idx}')
        return levels

    def read(self):
        body_size_uncompressed = self.read_int(); print('body_size_uncompressed:', body_size_uncompressed)
        self.idx += 4 # padding?

        print(f'[{self.idx}] Read levels...')
        level_count = self.read_int(); print('sublevel_count:', level_count)
        if level_count != 6:
            raise ValueError('Unexpected number of levels')
        non_level = self.read_sublevels()
        main_grid = self.read_sublevels()
        landscape_grid = self.read_sublevels()
        exploration_grid = self.read_sublevels()
        foliage_grid = self.read_sublevels()
        HLOD_grid = self.read_sublevels()

        print(f'[{self.idx}] Read levels')
        self.read_levels()
        
        print(f'[{self.idx}] Read object headers...')
        n_bytes_headers = self.read_int()
        self.idx += 4 # padding?
        original_idx = self.idx
        objects = self.read_object_headers()
        self.idx += 4 # padding?
        if original_idx + n_bytes_headers != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_headers} != {self.idx}')

        print(f'[{self.idx}] Read objects...')
        n_bytes_objects = self.read_int() # after padding
        self.idx += 4 # padding?
        original_idx = self.idx
        for obj_header in objects:
            object_type = obj_header['object_type']
            obj_header.update(self.read_object(object_type))
        self.idx += 4 # padding?
        if original_idx + n_bytes_objects != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_objects} != {self.idx}')

        self.idx += 4 # padding?
        if len(self.data) != self.idx:
            raise ValueError('Did not reach the end successfully')

        return objects


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('uncompressed_save_file')
    args = parser.parse_args()
    save_file = args.save_file

    with open(save_file, 'rb') as fp:
        data = fp.read()

    reader = UncompressedReader(data)
    # TODO: Read file
