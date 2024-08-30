from argparse import ArgumentParser
import zlib

import save_reader


class CompressedReader(save_reader.SaveReader):

    def __init__(self, data: bytes, idx: int=0):
        super().__init__(data, idx)

    def read_header(self):
        save_header_version = self.read_int(); print('save_header_version:', save_header_version)
        save_version = self.read_int(); print('save_version:', save_version)
        build_version = self.read_int(); print('build_version:', build_version)
        map_name = self.read_string(); print('map_name:', map_name)
        map_options = self.read_string(); print('map_options:', map_options)
        session_name = self.read_string(); print('session_name:', session_name)
        played_seconds = self.read_int(); print('played_seconds:', played_seconds)
        save_timestamp = self.read_int(8); print('save_timestamp:', save_timestamp) # ticks
        self.idx += 1 # TODO
        editor_object_version = self.read_int(); print('editor_object_version:', editor_object_version)
        mod_meta_data = self.read_string(); print('mod_meta_data:', mod_meta_data)
        mod_flag = self.read_int(); print('mod_flag:', mod_flag) # 0 if no mods
        save_identifier = self.read_string(); print('save_identifier:', save_identifier)
        self.idx += 28 # TODO

    def read_compressed_chunks(self):
        compressed_body_chunks = []
        while self.idx < len(self.data) - 1:

            ue_package_signature = self.read_hex(4); print('ue_package_signature:', ue_package_signature) # always 9E2A83C1 TODO: but here not?
            if ue_package_signature != 'c1832a9e':
                raise RuntimeError('Unexpected UE package_signature')
            archive_header = self.read_hex(4); print('archive_header:', archive_header) # 0x00000000: v1, 0x22222222: v2
            max_chunk_size = self.read_int(8); print('max_chunk_size:', max_chunk_size)
            compression_algorithm = self.read_bytes(size=1); print('compression_algorithm:', compression_algorithm) # 3: zlib

            compressed_size = self.read_int(8); print('compressed_size:', compressed_size) # number of bytes
            uncompressed_size = self.read_int(8); print('uncompressed_size:', uncompressed_size) # number of bytes
            cp_compressed_size = self.read_int(8); print('cp_compressed_size:', cp_compressed_size) # number of bytes
            cp_uncompressed_size = self.read_int(8); print('cp_uncompressed_size:', cp_uncompressed_size) # number of bytes

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
    
    compressed_safe_file = args.save_file
    uncompressed_save_file = compressed_safe_file[:-4] + '.bin'

    uncompress_save_file(compressed_safe_file, uncompressed_save_file)
