from libarchive import memory_reader, memory_writer

from . import check_archive, treestat


def test_convert():

    # Collect information on what should be in the archive
    tree = treestat('libarchive')

    # Create an archive of our libarchive/ directory
    buf = bytes(bytearray(1000000))
    with memory_writer(buf, 'gnutar', 'xz') as archive1:
        archive1.add_files('libarchive/')

    # Convert the archive to another format
    buf2 = bytes(bytearray(1000000))
    with memory_reader(buf) as archive1:
        with memory_writer(buf2, 'zip') as archive2:
            archive2.add_entries(archive1)

    # Check the data
    with memory_reader(buf2) as archive2:
        check_archive(archive2, tree)
