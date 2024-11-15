from argparse import ArgumentParser
import zlib

from assistory.save_parser import save_reader


SUPPORTED_SAVE_HEADER_VERSIONS = [13]
SUPPORTED_SAVE_VERSIONS = [42, 46]


class CompressedReader(save_reader.SaveReader):

    def __init__(self, data: bytes, idx: int=0):
        super().__init__(data, idx)

    def read_header(self):
        save_header_version = self.read_int()
        if not save_header_version in SUPPORTED_SAVE_HEADER_VERSIONS:
            print('WARNING: Save header version not supported: '
                                      + str(save_header_version))
        save_version = self.read_int()
        if not save_version in SUPPORTED_SAVE_VERSIONS:
            print('WARNING: Save version not supported: '
                                      + str(save_version))
        build_version = self.read_int(); print('build_version:', build_version)
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
                print('WARNING: Unexpected UE package_signature:', ue_package_signature)
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
    
    def read(self) -> bytes:
        self.read_header()
        data_uncompressed = bytes()
        for chunk in self.read_compressed_chunks():
            data_uncompressed += zlib.decompress(chunk)
        return data_uncompressed

    @classmethod
    def open_reader(cls, file: str) -> 'CompressedReader':
        with open(file, 'rb') as fp:
            data = fp.read()
        return cls(data)


def uncompress_save_file(compressed_save: str, uncompressed_save: str):
    reader = CompressedReader.open_reader(compressed_save)
    data_uncompressed = reader.read()

    with open(uncompressed_save, 'wb') as fp:
        fp.write(data_uncompressed)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('save_file')
    args = parser.parse_args()

    if not args.save_file[-4:] == '.sav':
        raise RuntimeError('Wrong file format')
    
    compressed_save_file = args.save_file
    uncompressed_save_file = compressed_save_file[:-4] + '.bin'
    uncompress_save_file(compressed_save_file, uncompressed_save_file)
