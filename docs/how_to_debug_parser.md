The parser can be debuged using and interactive Python session and the uncompressed save file in an editor.

## Get uncompressed save file

```python
from assistory.save_parser import compressed_parser, save_parser
save_file = '/path/to/the/save/file.sav'
reader = compressed_parser.CompressedReader.open_reader(save_file)
data_uncompressed = reader.read()
with open('/tmp/debug_file.txt', 'wb') as fp:
    fp.write(data_uncompressed)
```

Now open `'/tmp/debug_file.txt'` in an editor that is capable of
- handling large files
- jump of byte positions

# Investigate an error or warning
Run the save file parser
```
reader = save_parser.UncompressedReader(data_uncompressed)
```
Now, the warnings or error will be reported, e.g. like this:
```
[6873884] WARNING Unknown array type: InterfaceProperty ...skip property
```

To debug the parser, jump the the index *6873884* and set the reader index accordingly
```
reader.idx = reader.idx = 6873884
```

Now, debugging can be done manually.
