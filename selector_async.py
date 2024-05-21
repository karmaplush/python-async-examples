import os
import selectors
import sys
import threading
import time

OUTPUT_FILE = "output.txt"
selector = selectors.DefaultSelector()


def simulate_external_input(write_end_fd: int):

    try:
        for _ in range(10):
            os.write(write_end_fd, "External message from pipe\n".encode())
            time.sleep(1)

    finally:
        os.close(write_end_fd)


def write_to_file(descriptor_like) -> bool:

    # Function for reading data from descriptor and writing it to file

    # The return value is used to track the
    # execution status (need to exit) within the event loop

    fileno = (
        descriptor_like
        if isinstance(descriptor_like, int)
        else descriptor_like.fileno()
    )
    data_from_given_descriptor = os.read(fileno, 1024)

    if not data_from_given_descriptor and descriptor_like == sys.stdin.fileno():
        print("EOF was called from stdin, exit...")
        return False

    with open(OUTPUT_FILE, "a") as f:
        bytes_to_string_decoded = data_from_given_descriptor.decode()
        f.write(bytes_to_string_decoded)

    return True


def event_loop():
    while True:

        # Read events from all registered file-like objects
        events = selector.select()

        # For every selector key object we get function from data
        # and use it for perform required action
        for key, _ in events:
            callback = key.data
            if not callback(key.fileobj):
                return


if __name__ == "__main__":

    read_end_pipe_descriptor, write_end_pipe_descriptor = os.pipe()

    # Register all file-like objects in selector
    selector.register(
        fileobj=sys.stdin.fileno(),
        events=selectors.EVENT_READ,
        data=write_to_file,
    )
    selector.register(
        fileobj=read_end_pipe_descriptor,
        events=selectors.EVENT_READ,
        data=write_to_file,
    )

    external_input_thread = threading.Thread(
        target=simulate_external_input,
        args=(write_end_pipe_descriptor,),
    )
    external_input_thread.start()

    try:
        event_loop()
    finally:
        external_input_thread.join()
        os.close(read_end_pipe_descriptor)
