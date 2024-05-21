import os
import sys
import threading
import time
from collections import deque
from select import select

OUTPUT_FILE = "output.txt"

tasks_queue = deque()
to_read = {}
stop_event_loop = False


def simulate_external_input(write_end_fd: int):

    try:
        for _ in range(10):
            os.write(write_end_fd, "External message from pipe\n".encode())
            time.sleep(1)

    finally:
        os.close(write_end_fd)


def write_to_file(read_fd: int):

    while True:

        # 7. First yield before blocking operation (pipe_fd),
        # return control place where next() was called

        # 11. First yield before blocking operation (stdin_fd),
        # return control place where next() was called

        # 18. Second called next() (pipe_fd) will start from here and do all
        # other logic below yield, write data into file and came
        # here before another blocking operation, again return read_fd and flow control
        # where next() was called
        yield read_fd
        data = os.read(read_fd, 1024)

        if not data and read_fd == sys.stdin.fileno():
            print("EOF was called from stdin, exit...")
            global stop_event_loop
            stop_event_loop = True
            break

        with open(OUTPUT_FILE, "a") as f:
            f.write(data.decode())


def event_loop():

    # 4. While queue[generator as task] (we have 2 tasks now) or
    # to_read[read_fd: generator as task] not empty...
    while tasks_queue or to_read:

        if stop_event_loop:
            break

        # 13. Now tasks queue is empty
        while not tasks_queue:
            readable, _, _ = select(to_read, [], [])

            # 14. For every ready-to-read fd...
            for read_fd in readable:
                # 15. Add new tasks (generators with saved state)
                # and remove it from read_fd dict by read_fd (both pipe_fd & stdin_fd)
                tasks_queue.append(to_read.pop(read_fd))

        try:
            # 5. Get first task ( generator_obj(pipe_fd) ) from queue
            # 9. Get second task ( generator_obj(stdin_fd) ) from queue
            # 16. Get first task ( generator_obj(pipe_fd) ) from queue
            task = tasks_queue.popleft()
            # 6. Yield read_fd from generator(pipe_fd)
            # 10. Yield read_fd from generator(stdin_fd)
            # 17. Yield read_fd from generator(pipe_fd)
            read_fd = next(task)
            # 8. Update to_read dict like [pipe_fd: generator_obj(pipe_fd)]
            # 12. Update to_read dict like [stdin_fd: generator_obj(stdin_fd)]
            # 19. Update to_read dict like [stdin_fd: generator_obj(pipe_fd)].
            # All other logic will do in endless cycle.
            to_read[read_fd] = task

        except StopIteration:
            print("StopIteration reached")


if __name__ == "__main__":
    read_end_pipe_descriptor, write_end_pipe_descriptor = os.pipe()

    # 1. Generator obj for writin to file from pipe
    tasks_queue.append(write_to_file(read_end_pipe_descriptor))
    # 2. Generator obj for writin to file from stdin
    tasks_queue.append(write_to_file(sys.stdin.fileno()))

    external_input_thread = threading.Thread(
        target=simulate_external_input,
        args=(write_end_pipe_descriptor,),
    )
    external_input_thread.start()

    try:
        # 3. Staring event loop
        event_loop()
    finally:
        external_input_thread.join()
        os.close(read_end_pipe_descriptor)
