import struct
from typing import Tuple, Union

class SaveReader:

    def __init__(self, data: bytes, idx: int=0):
        self.data = data
        self.idx = idx
        self._property_parsers = {
            'FloatProperty': self._read_float_property,
            'IntProperty': self._read_int_property,
            'ObjectProperty': self._read_object_property,
            'BoolProperty': self._read_bool_property,
            'StructProperty': self._read_struct_property,
            'ArrayProperty': self._read_array_property,
            'UInt32Property': self._read_uint32_property,
            'MapProperty': self._read_map_property,
            'ByteProperty': self._read_byte_property,
            'StrProperty': self._read_str_property,
            'NameProperty': self._read_str_property,
            'EnumProperty': self._read_enum_property,
            'Int64Property': self._read_int64_property,
            'Int8Property': self._read_int8_property,
            'TextProperty': self._read_text_property,
        }
        
        self._array_property_parsers = {
            'ObjectProperty': self._read_array_object_property,
            'IntProperty': self._read_array_int_property,
            'StructProperty': self._read_array_struct_property,
            'ByteProperty': self._read_array_byte_property,
            'StrProperty': self._read_array_string_property,
        }

    def read_string(self) -> str:
        length = self.read_int() # Including terminating character
        if length == 0:
            return ""
        idx_string_term  = self.data.find(b'\00', self.idx)
        if self.idx + length != idx_string_term + 1:
            raise ValueError(f'{self.idx} + {length} != {idx_string_term} + 1')
        text = self.data[self.idx: idx_string_term].decode()
        self.idx = idx_string_term + 1
        return text

    def read_int(self, size: int=4) -> int:
        val = int.from_bytes(self.data[self.idx: self.idx + size], 'little')
        self.idx += size
        return val

    def read_bytes(self, size: int) -> bytes:
        val = self.data[self.idx: self.idx + size]
        self.idx += size
        return val

    def read_hex(self, size: int) -> str:
        text = self.data[self.idx: self.idx + size].hex()
        self.idx += size
        return text

    def read_float(self) -> float:
        val = struct.unpack('f', self.data[self.idx: self.idx + 4])[0]
        self.idx += 4
        return val

    def read_property(self) -> Tuple[str, Union[None, dict]]:
        original_idx = self.idx
        name = self.read_string()
        if name == '':
            raise ValueError('Invalid name: ' + name)
        if name == 'None':
            return name, None
        val = dict()
        val['start_idx'] = original_idx
        val['property_type'] = self.read_string()
        if not val['property_type'] in self._property_parsers:
            raise ValueError('Unknown property type: ' + val['property_type'])
        
        try:
            val.update(self._property_parsers[val['property_type']]())
        except Exception as e:
            print('Reading', val['property_type'], 'failed at original_idx:', original_idx)
            raise e
        
        val['end_idx'] = self.idx
        return name, val

    def _read_float_property(self) -> dict:
        n_bytes = self.read_int()
        if n_bytes != 4:
            raise ValueError
        index = self.read_int()
        self.idx += 1 # padding
        val = self.read_float()
        return {'value': val}

    def _read_object_property(self) -> dict:
        n_bytes = self.read_int()
        index = self.read_int()
        self.idx += 1 # padding
        original_idx = self.idx
        level_name = self.read_string()
        path_name = self.read_string()
        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return {'level_name': level_name, 'path_name': path_name}
    
    def _read_bool_property(self) -> dict:
        padding = self.read_int()
        index = self.read_int()
        val = bool(self.read_bytes(size=1))
        self.idx += 1 # padding
        return {'value': val}

    def _read_struct_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        struct_type = self.read_string()
        self.idx += 17 # padding
        payload = self.read_bytes(n_bytes) # InventoryItem: int, string, int, int
        return {'struct_type': struct_type, 'payload': payload}
    
    def _read_array_object_property(self) -> dict:
        val = dict()
        length = self.read_int()
        val['elements'] = []
        for _ in range(length):
            elem = dict()
            elem['level_name'] = self.read_string()
            elem['path_name'] = self.read_string()
            val['elements'].append(elem)
        return val
    
    def _read_array_int_property(self) -> dict:
        val = dict()
        length = self.read_int()
        val['elements'] = []
        for _ in range(length):
            val['elements'].append(self.read_int())
        return val
    
    def _read_array_byte_property(self) -> dict:
        val = dict()
        length = self.read_int()
        val['elements'] = self.read_bytes(length)
        return val
    
    def _read_array_string_property(self) -> dict:
        val = dict()
        length = self.read_int()
        val['elements'] = []
        for _ in range(length):
            val['elements'].append(self.read_string())
        return val
    
    def _read_array_struct_property(self) -> dict:
        val = dict()
        length = self.read_int()
        name = self.read_string() # duplicate
        array_property_type = self.read_string()
        # if not array_property_type == 'StructProperty':
        #     raise ValueError('Expected StructProperty. Got ' + array_property_type)
        n_bytes = self.read_int() # after the byte padding (after UUID)
        padding = self.read_int()
        val['element_type'] = self.read_string() # SpawnData, LinearColor, InventoryStacks, ScannableResourcePair
        uuid = [self.read_int(), self.read_int(), self.read_int(), self.read_int()]
        self.idx += 1 # padding
        
        # typed data
        original_idx = self.idx
        val['elements'] = []
        for _ in range(length):
            if val['element_type'] == 'LinearColor':
                elem = {
                    'r': self.read_float(),
                    'g': self.read_float(),
                    'b': self.read_float(),
                    'a': self.read_float()
                }
            elif val['element_type'] == 'ScannableResourcePair':
                elem = dict()
                elem_name, elem_prop = self.read_property()
                elem['prop'] = elem_prop
                elem['name'] = elem_name
            else:
                elem = dict()
                elem_name, elem_prop = self.read_property()
                elem['prop'] = elem_prop
                elem['properties'] = self.read_properties()
                elem['name'] = elem_name
            val['elements'].append(elem)

        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return val
    
    def _read_array_property(self) -> dict:
        val = dict()
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        val['array_type'] = self.read_string()
        if not val['array_type'] in self._array_property_parsers:
            raise ValueError(f' [{self.idx}] Unknown array type: {val["array_type"]}')
        self.idx += 1 # padding
        original_idx = self.idx
        # second part?

        val.update(self._array_property_parsers[val['array_type']]())

        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        
        return val
    
    def _read_int_property(self) -> dict:
        n_bytes = self.read_int()
        if n_bytes != 4:
            raise ValueError
        index = self.read_int()
        self.idx += 1 # padding
        val = self.read_int() # TODO: which format?
        return {'value': val}
    
    def _read_uint32_property(self) -> dict:
        n_bytes = self.read_int()
        if n_bytes != 4:
            raise ValueError
        self.idx += 4 # TODO
        self.idx += 1 # padding
        val = self.read_int()
        return {'value': val}
    
    def _read_map_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        key_type = self.read_string()
        value_type = self.read_string()
        self.idx += 1 # padding
        self.idx += n_bytes # TODO
        return dict()
    
    def _read_byte_property(self) -> dict:
        val = dict()
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        val['value_type'] = self.read_string()
        self.idx += 1 # padding
        val['value'] = self.read_bytes(size=n_bytes)
        return val

    def _read_str_property(self) -> dict:
        val = dict()
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        self.idx += 1 # padding
        original_idx = self.idx
        val['value'] = self.read_string()
        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return val

    def _read_enum_property(self) -> dict:
        val = dict()
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        val['value_type'] = self.read_string()
        self.idx += 1 # padding
        original_idx = self.idx
        val['value'] = self.read_string()
        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return val
    
    def _read_int64_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        if n_bytes != 8:
            raise ValueError
        index = self.read_int()
        self.idx += 1 # padding
        val = self.read_int(size=n_bytes) # TODO: signed?
        return {'value': 0}
    
    def _read_int8_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        if n_bytes != 1:
            raise ValueError
        index = self.read_int()
        self.idx += 1 # padding
        val = self.read_int(size=1) # TODO: signed?
        return {'value': 0}
    
    def _read_text_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        self.idx += 1 # padding
        original_idx = self.idx
        val = dict()
        val['flags'] = self.read_int() # semantic unclear
        val['history_type'] = self.read_bytes(size=1) # semantic unclear
        val['culture_invariant'] = self.read_int() # semantic unclear
        val['value'] = self.read_string()
        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return val

    def read_properties(self) -> dict:
        properties = dict()
        while True:
            name, prop = self.read_property()
            if prop is None:
                break
            properties[name] = prop
        return properties
    
    def print_context(self, c=200):
        print('------------')
        print(self.data[self.idx-c:self.idx])
        print('<----', self.idx)
        print(self.data[self.idx:self.idx+c])
        print('------------')
