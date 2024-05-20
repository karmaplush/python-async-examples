import os
import sys
import threading
import time
from select import select

descriptors_for_read_from = []


def event_loop():
    # In endless cycle...
    while True:

        # Get descriptors, what ready to reading
        waiting_for_read, _, _ = select(descriptors_for_read_from, [], [])

        # For every "ready-to-read" descriptor...
        for readable in waiting_for_read:

            # Get bytes data from given "readable" (our stdin in this case)
            data_from_given_descriptor = os.read(readable, 1024)

            # If EOF (Ctrl+D) was called (only for stdin), we will return from loop
            # (os.close() also call EOF, so in this case we wants
            # to avoid exiting loop, if "simulator" will end)
            if not data_from_given_descriptor and readable == sys.stdin.fileno():
                print("End of input, exiting...")
                return

            # Decode and write bytes from given descriptor into .txt file
            with open("select_async.txt", "a") as f:
                bytes_to_string_decoded = data_from_given_descriptor.decode()
                f.write(bytes_to_string_decoded)


def simulate_external_input(write_file_descriptor):

    # For ten times...
    for i in range(20):

        # We will write data to descriptor (pipe write end in this case)
        os.write(write_file_descriptor, f"External message number {i+1}\n".encode())

        # Sleep for 0.5 second
        time.sleep(0.5)

    # Closing write-end of pipe
    os.close(write_file_descriptor)


if __name__ == "__main__":
    # Adding standart input file descriptor for watching
    descriptors_for_read_from.append(sys.stdin.fileno())

    # Creating a pipe and adding read pipe end to watching
    read_pipe_file_descriptor, write_pipe_file_descriptor = os.pipe()
    descriptors_for_read_from.append(read_pipe_file_descriptor)

    # Start a thread to simulate external input to the pipe
    threading.Thread(
        target=simulate_external_input, args=(write_pipe_file_descriptor,)
    ).start()

    # Running event loop
    event_loop()

    # Closing read-end of pipe
    os.close(read_pipe_file_descriptor)
