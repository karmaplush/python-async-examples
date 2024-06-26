import os
import sys
import threading
import time
from select import select

OUTPUT_FILE = "output.txt"
descriptors_for_read_from = []


def simulate_external_input(write_end_fd: int):

    try:
        for _ in range(10):
            os.write(write_end_fd, "External message from pipe\n".encode())
            time.sleep(1)

    finally:
        os.close(write_end_fd)


def event_loop():
    while True:

        # Get descriptors, what ready to reading
        waiting_for_read, _, _ = select(descriptors_for_read_from, [], [])

        # For every "ready-to-read" descriptor...
        for readable in waiting_for_read:

            data_from_given_descriptor = os.read(readable, 1024)

            if not data_from_given_descriptor and readable == sys.stdin.fileno():
                print("EOF was called from stdin, exiting...")
                return

            with open(OUTPUT_FILE, "a") as f:
                bytes_to_string_decoded = data_from_given_descriptor.decode()
                f.write(bytes_to_string_decoded)


if __name__ == "__main__":

    read_end_pipe_descriptor, write_end_pipe_descriptor = os.pipe()

    descriptors_for_read_from.append(sys.stdin.fileno())
    descriptors_for_read_from.append(read_end_pipe_descriptor)

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
