from argparse import ArgumentParser
import zlib

import save_reader


class CompressedReader(save_reader.SaveReader):

    def __init__(self, data: bytes, idx: int=0):
        super().__init__(data, idx)

    def read_header(self):
        save_header_version = self.read_int()
        save_version = self.read_int()
        build_version = self.read_int()
        map_name = self.read_string()
        map_options = self.read_string()
        session_name = self.read_string()
        played_seconds = self.read_int()
        save_timestamp = self.read_int(8) # ticks
        self.idx += 1 # TODO
        editor_object_version = self.read_int()
        mod_meta_data = self.read_string()
        mod_flag = self.read_int() # 0 if no mods
        save_identifier = self.read_string()
        self.idx += 28 # TODO

    def read_compressed_chunks(self):
        compressed_body_chunks = []
        while self.idx < len(self.data) - 1:

            ue_package_signature = self.read_hex(4); # always 9E2A83C1 TODO: but here not?
            if ue_package_signature != 'c1832a9e':
                raise RuntimeError('Unexpected UE package_signature')
            archive_header = self.read_hex(4) # 0x00000000: v1, 0x22222222: v2
            max_chunk_size = self.read_int(8)
            compression_algorithm = self.read_bytes(size=1) # 3: zlib

            compressed_size = self.read_int(8) # number of bytes
            uncompressed_size = self.read_int(8) # number of bytes
            cp_compressed_size = self.read_int(8) # number of bytes
            cp_uncompressed_size = self.read_int(8) # number of bytes

            compressed_body_chunks.append(self.data[self.idx: self.idx + compressed_size])
            self.idx += compressed_size
        return compressed_body_chunks


def uncompress_save_file(compressed_save: str, uncompressed_save: str):
    with open(compressed_save, 'rb') as fp:
        data = fp.read()

    reader = CompressedReader(data)
    reader.read_header()
    compressed_body_chunks = reader.read_compressed_chunks()

    with open(uncompressed_save, 'wb') as fp:
        for chunk in compressed_body_chunks:
            uncompressed_chunk = zlib.decompress(chunk)
            fp.write(uncompressed_chunk)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('save_file')
    args = parser.parse_args()

    if not args.save_file[-4:] == '.sav':
        raise RuntimeError('Wrong file format')
    
    compressed_save_file = args.save_file
    uncompressed_save_file = compressed_save_file[:-4] + '.bin'
    uncompress_save_file(compressed_save_file, uncompressed_save_file)
