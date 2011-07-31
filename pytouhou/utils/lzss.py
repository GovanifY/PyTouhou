def decompress(bitstream, size, dictionary_size=0x2000,
               offset_size=13, length_size=4, minimum_match_length=3):
    out_data = []
    dictionary = [0] * dictionary_size
    dictionary_head = 1
    while len(out_data) < size:
        flag = bitstream.read_bit()
        if flag:
            # The `flag` bit is set, indicating the upcoming chunk of data is a literal
            # Add it to the uncompressed file, and store it in the dictionary
            byte = bitstream.read(8)
            dictionary[dictionary_head] = byte
            dictionary_head = (dictionary_head + 1) % dictionary_size
            out_data.append(byte)
        else:
            # The `flag` bit is not set, the upcoming chunk is a (offset, length) tuple
            offset = bitstream.read(offset_size)
            length = bitstream.read(length_size) + minimum_match_length
            if (offset, length) == (0, 0):
                break
            for i in range(offset, offset + length):
                out_data.append(dictionary[i % dictionary_size])
                dictionary[dictionary_head] = dictionary[i % dictionary_size]
                dictionary_head = (dictionary_head + 1) % dictionary_size
    return b''.join(chr(byte) for byte in out_data)
