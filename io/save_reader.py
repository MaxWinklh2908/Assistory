import struct


class SaveReader:

    def __init__(self, data: bytes, idx: int=0):
        self.data = data
        self.idx = idx

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

    def read_int(self, size=4) -> int:
        val = int.from_bytes(self.data[self.idx: self.idx + size], 'little')
        self.idx += size
        return val

    def read_byte(self) -> int:
        val = self.data[self.idx]
        self.idx += 1
        return val

    def read_hex(self, size) -> str:
        text = self.data[self.idx: self.idx + size].hex()
        self.idx += size
        return text

    def read_float(self) -> float:
        val = struct.unpack('f', self.data[self.idx: self.idx + 4])[0]
        self.idx += 4
        return val

    
    def read_property(self) -> dict:
        val = dict()
        val['name'] = self.read_string()
        if val['name'] == '':
            raise ValueError('Invalid name: ' + val['name'])
        if val['name'] == 'None':
            return val
        val['property_type'] = self.read_string()
        if val['property_type'] == 'FloatProperty':
            val.update(self._read_float_property())
        elif val['property_type'] == 'IntProperty':
            val.update(self._read_int_property())
        elif val['property_type'] == 'ObjectProperty':
            val.update(self._read_object_property())
        elif val['property_type'] == 'BoolProperty':
            val.update(self._read_bool_property())
        elif val['property_type'] == 'StructProperty':
            val.update(self._read_struct_property())
        elif val['property_type'] == 'ArrayProperty':
            val.update(self._read_array_property())
        elif val['property_type'] == 'UInt32Property':
            val.update(self._read_uint32_property())
        elif val['property_type'] == 'MapProperty':
            val.update(self._read_map_property())
        elif val['property_type'] == 'ByteProperty':
            val.update(self._read_byte_property())
        elif val['property_type'] == 'StrProperty':
            val.update(self._read_str_property())
        elif val['property_type'] == 'NameProperty':
            val.update(self._read_str_property())
        elif val['property_type'] == 'EnumProperty':
            val.update(self._read_enum_property())
        elif val['property_type'] == 'Int64Property':
            val.update(self._read_int64_property())
        elif val['property_type'] == 'Int8Property':
            val.update(self._read_int8_property())
        elif val['property_type'] == 'TextProperty':
            val.update(self._read_text_property())
        else:
            raise ValueError('Unknown property type: ' + val['property_type'])
        return val

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
        val = bool(self.read_byte())
        self.idx += 1 # padding
        return {'value': val}

    def _read_struct_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        struct_type = self.read_string()
        self.idx += 17 # padding
        self.idx += n_bytes # TODO
        return dict()
    
    def _read_array_property(self) -> dict:
        n_bytes = self.read_int() # after padding
        index = self.read_int()
        val = dict()
        val['array_type'] = self.read_string()
        self.idx += 1 # padding
        original_idx = self.idx
        # length = self.read_int()
        self.idx += n_bytes # TODO
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
        val['value'] = self.data[self.idx: self.idx + n_bytes]
        self.idx += n_bytes
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
        val['history_type'] = self.read_byte() # semantic unclear
        val['culture_invariant'] = self.read_int() # semantic unclear
        val['value'] = self.read_string()
        if original_idx + n_bytes != self.idx:
            raise ValueError(f'{original_idx} + {n_bytes} != {self.idx}')
        return val

    def read_property_list(self) -> list:
        properties = []
        while True:
            next_prop = self.read_property()
            if next_prop['name'] == 'None':
                break
            properties.append(next_prop)
        return properties
    
    def print_context(self, c=200):
        print('------------')
        print(self.data[self.idx-c:self.idx])
        print('<----', self.idx)
        print(self.data[self.idx:self.idx+c])
        print('------------')
