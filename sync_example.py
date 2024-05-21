import os
import sys
import threading
import time

OUTPUT_FILE = "output.txt"
descriptors_for_read_from = []


def simulate_external_input(write_end_fd: int):

    try:
        for _ in range(10):
            os.write(write_end_fd, "External message from pipe\n".encode())
            time.sleep(1)

    finally:
        # Ensure the write-end of the pipe is closed
        os.close(write_end_fd)
        # If pipe is closed, we do not need to read from it
        descriptors_for_read_from.pop(0)


def event_loop():
    while True:

        for read in descriptors_for_read_from:
            # Blocking operation (!): waits until there is something to read
            data_from_file_by_descriptor = os.read(read, 1024)

            # If EOF is called from stdin, exit the loop
            if not data_from_file_by_descriptor and read == sys.stdin.fileno():
                print("EOF was called from stdin, exiting...")
                return

            # Write the read data to the output file
            with open(OUTPUT_FILE, "a") as f:
                f.write(data_from_file_by_descriptor.decode())


if __name__ == "__main__":

    # Just some actions for example:
    # 1. Pipe creating
    # 2. Adding descriptors (stdin & pipe read-end) for reading in loop
    # 3. Starting a thread to simulate external writing to the pipe
    # 4. After finishing event_loop(), terminating thread, closing pipe's read-end

    read_end_pipe_descriptor, write_end_pipe_descriptor = os.pipe()

    descriptors_for_read_from.append(read_end_pipe_descriptor)
    descriptors_for_read_from.append(sys.stdin.fileno())

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
