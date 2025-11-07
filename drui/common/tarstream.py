import os
import tarfile
import threading
import typing as t

from requests import PreparedRequest
from requests import Session


class Data:
    def __init__(self, data, filename, symlink):
        """
        Helper class for TarStream.
        Holds metadata for a single item to be added to the TAR archive.
        """
        self.data = data
        self.filename = filename
        self.symlink = symlink


class TarStream:
    """
    Generates a streaming TAR archive from a list of items.

    This class allows adding files and symlinks to a TAR archive incrementally,
    then streams the archive content in chunks via a generator. Uses threading
    and pipes to avoid blocking during archive creation.

    Example:
        >>> stream = TarStream()
        >>> stream.add(b"Hello", "hello.txt")
        >>> stream.add(b"World", "world.txt")
        >>> for chunk in stream.start():
        ...     print(len(chunk))
    """

    def __init__(self):
        self.queue = []

    def add(self, data: t.Any, filename: str, symlink: bool = False) -> None:
        """
        Add an item to the archive queue.

        :param data: the actual content (bytes, file-like object, PreparedRequest)
        :param filename: the name of the file in the archive
        :param symlink: whether this item should be stored as a symlink
        """
        self.queue.append(Data(data, filename, symlink))

    def start(self):
        """
        Stream the TAR archive as a generator.

        :return: a generator
        """
        # create a pipe for streaming write and read of a TAR file
        read_fd, write_fd = os.pipe()

        def write_tar():
            """
            Worker thread: writes the TAR archive to the pipe.
            """
            with os.fdopen(write_fd, 'wb') as write_file:
                with tarfile.open(fileobj=write_file, mode='w|') as tar:
                    for item in self.queue:
                        try:
                            if item.symlink:
                                tar_info = tarfile.TarInfo(name=item.filename)
                                tar_info.type = tarfile.SYMTYPE
                                tar_info.linkname = item.data
                                tar.addfile(tar_info)
                            else:
                                # create a file-like object from an HTTP response
                                if isinstance(item.data, PreparedRequest):
                                    with Session() as s:
                                        resp = s.send(item.data, stream=True)
                                    file_data = resp.raw
                                    file_size = int(
                                        resp.headers['content-length']
                                    )
                                else:
                                    file_data = item.data
                                    file_size = len(item.data.getvalue())

                                tar_info = tarfile.TarInfo(name=item.filename)
                                tar_info.size = file_size
                                tar.addfile(tar_info, file_data)

                        except Exception as e:
                            print(f'Error processing {item.filename}: {e}')
                            continue

        # start writer thread
        writer_thread = threading.Thread(target=write_tar)
        writer_thread.start()

        # read from pipe and yield chunks (main thread)
        with os.fdopen(read_fd, 'rb') as read_file:
            while True:
                data = read_file.read(8192)
                if not data:
                    break
                yield data

        writer_thread.join()
