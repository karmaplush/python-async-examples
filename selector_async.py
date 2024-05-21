import os
import selectors
import sys
import threading
import time
from typing import BinaryIO, Callable

selector = selectors.DefaultSelector()

OUTPUT_FILE = "output.txt"


def write_to_file(file: BinaryIO | int) -> bool:
    """`file` arg can be both of file-like obj or file descriptor integer"""

    fileno = file if isinstance(file, int) else file.fileno()
    data_from_given_descriptor = os.read(fileno, 1024)

    if not data_from_given_descriptor and file == sys.stdin:
        selector.unregister(sys.stdin)
        print("EOF was called from stdin, exit...")
        return False

    if data_from_given_descriptor:
        with open(OUTPUT_FILE, "a") as f:
            bytes_to_string_decoded = data_from_given_descriptor.decode()
            f.write(bytes_to_string_decoded)

    return True


def event_loop():
    while True:

        # It is returns registered events (keys) and bit events mask
        events = selector.select()

        # Iterating over all events and using passed to data kwarg
        # function for writing data in file

        # If EOF (Ctrl+D) was called (only for stdin), func will return False and
        # we will return from event loop
        for key, _ in events:
            service_func: Callable = key.data
            if not service_func(key.fileobj):
                return


def simulate_external_input(write_file_descriptor):
    for i in range(20):
        os.write(write_file_descriptor, f"External message number {i+1}\n".encode())
        time.sleep(0.5)
    os.close(write_file_descriptor)


if __name__ == "__main__":

    # Register stdin for read events
    selector.register(
        fileobj=sys.stdin,
        events=selectors.EVENT_READ,
        data=write_to_file,
    )

    # Creating pipe and register read-end for events
    read_end_pipe_descriptor, write_end_pipe_descriptor = os.pipe()
    selector.register(
        fileobj=read_end_pipe_descriptor,
        events=selectors.EVENT_READ,
        data=write_to_file,
    )

    # Start a thread to simulate external writing to the pipe
    threading.Thread(
        target=simulate_external_input, args=(write_end_pipe_descriptor,)
    ).start()

    # Running event loop
    event_loop()

    # Unregister and closing read-end of pipe after ending event loop
    selector.unregister(read_end_pipe_descriptor)
    os.close(read_end_pipe_descriptor)
