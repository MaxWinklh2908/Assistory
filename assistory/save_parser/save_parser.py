from typing import List

from assistory.save_parser import component_parser


SUPPORTED_SAVE_VERSIONS = [42, 46]


class UncompressedReader(component_parser.SaveReader):

    def __init__(self, data: bytes, idx: int=0, fail_on_error: bool=False):
        """
        Create a reader for uncompressed save file body

        Args:
            data (bytes): content of the uncompressed save file body
            idx (int, optional): Start index. Defaults to 0.
            fail_on_error (bool, optional): Whether to stop on parsing error.
                If false warn and continue parsing. Defaults to False.
        """
        super().__init__(data, idx)
        self.fail_on_error = fail_on_error

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
        try:
            val['level_name'] = self.read_string()
            val['path_name'] = self.read_string()
            val['components'] = self.read_object_references()
            val['properties'] = self.read_properties()
        except Exception as e:
            self.idx = original_idx + n_bytes
            raise e
        # apply trailing bytes
        if original_idx + n_bytes > self.idx:
            self.idx = original_idx + n_bytes
        return val
    
    def read_component_object(self) -> dict:
        val = dict()
        original_idx = self.idx
        n_bytes = self.read_int()
        try:
            val['properties'] = self.read_properties()
        except Exception as e:
            self.idx = original_idx + n_bytes
            raise e

        # apply trailing bytes
        if original_idx + n_bytes > self.idx:
            self.idx = original_idx + n_bytes
        return val
    
    def read_object(self, object_type: int) -> dict:
        val = dict()
        val['start_idx'] = self.idx
        a = self.read_int() # 15/6 /3158584 (25282136)
        val['save_version'] = self.read_int() # 42/36 # TODO: correct?
        if not val['save_version'] in SUPPORTED_SAVE_VERSIONS:
            print('WARNING: Save version not supported: '
                                      + str(val['save_version']))
        c = self.read_int() # 0/1
        if object_type == 1:
            val_actor_obj = self.read_actor_object()
            val.update(val_actor_obj)
        elif object_type == 0:
            val.update(self.read_component_object())
        else:
            raise ValueError('Invalid object type: {object_type}')
        return val
    
    def read_objects(self, verbose: bool=False) -> List[dict]:
        if verbose:
            print(f'[{self.idx}] Read object headers...')
        n_bytes_headers = self.read_int()
        self.idx += 4 # padding?
        original_idx = self.idx
        objects = self.read_object_headers()
        self.idx += 4 # padding?
        if original_idx + n_bytes_headers != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_headers} != {self.idx}')

    
        if verbose:
            print(f'[{self.idx}] Read objects...')
        n_bytes_objects = self.read_int() # after padding
        self.idx += 4 # padding?
        original_idx = self.idx
        complete_objects = []
        for obj_header in objects:
            original_object_idx = self.idx
            object_type = obj_header['object_type']
            try:
                obj_header.update(self.read_object(object_type))
            except Exception as e:
                print(e.args[0])
                print(f'[{original_object_idx}] WARNING Error reading Object {obj_header["instance_name"]}')
                if self.fail_on_error:
                    raise e
                else:
                    continue
            complete_objects.append(obj_header)
        self.idx += 4 # padding?
        if original_idx + n_bytes_objects != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes_objects} != {self.idx}')
        
        return complete_objects

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

    def read(self, verbose: bool=False):
        n_bytes_body = self.read_int() # after padding
        self.idx += 4 # padding?
        original_idx_body = self.idx

        if verbose:
            print(f'[{self.idx}] Read levels...')
        level_count = self.read_int()
        if verbose:
            print('sublevel_count:', level_count)
        if level_count != 6:
            raise ValueError('Unexpected number of levels')
        non_level = self.read_sublevels()
        main_grid = self.read_sublevels()
        landscape_grid = self.read_sublevels()
        exploration_grid = self.read_sublevels()
        foliage_grid = self.read_sublevels()
        HLOD_grid = self.read_sublevels()

        if verbose:
            print(f'[{self.idx}] Read levels')
        self.read_levels()
        
        objects = self.read_objects()

        self.idx = original_idx_body + n_bytes_body # apply final padding

        if len(self.data) != self.idx:
            raise ValueError('Did not reach the end successfully')

        return objects
