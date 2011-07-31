def read_string(file, size, encoding=None):
    data = file.read(size)

    try:
        data = data[:data.index(b'\x00')]
    except ValueError:
        pass

    if encoding:
        return data.decode(encoding)
    else:
        return data
