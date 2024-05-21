# Async in Python: some examples from low-level to asyncio module

All output will be stored in `output.txt`

## 0. Sync example (`sync_example.py`)
Just boilerplate for other examples. Here we have two things:
1. We can write to file, using stdin
2. We can wrtie to file from created pipe

In this code, we have blocking operation `os.read()`, and we can't write data asynchronously - we have to wait for data from standard input before we can move on and get data over other sources (think of it as if stdin is a DB and until we enter some information, we aggregate it inside the database).

While we, as a database, are thinking, our program cannot pass on the flow of execution. This is the main point of asynchrony in Python - to solve the I/O problem by passing the execution thread on.

How to use this example (and other examples in same manere):
- Open `output.txt` in tab
- Launch `sync_example.py`. It will start our writing to pipe in another thread (just for showcase).
- Try to type something in `stdin`. You will see how blocking `os.read()` affects on output.
- Send EOF by `Ctrl+D` for exiting from loop (not instantly, another thread will wait till writing to pipe stops)


## 1. Async example based on `select` (`select_async.py`)
Based on OS's `select` call via standart Python's `select` module
https://en.wikipedia.org/wiki/Select_(Unix)

![select_diagram](imgs/select-system-call-diagram.jpg)

Instead of iterating over descriptors, we will use `select()`. It monitors sockets, open files, and pipes (anything with a fileno() method that returns a valid file descriptor) until they become readable or writable, or a communication error occurs. In this example we will use only readable things to monitor stdin and pipe's read-end.


## 2. Async example based on high-level `selector` module (`selector_async.py`)
High-level I/O API with same principle as `select` module https://docs.python.org/3/library/selectors.html

Concrete implementation of default select mechanism depends on OS (`epoll` for UNIX by default)

Example in repo do almost same things as `select` example, but we need to register descriptors via selector object `.register()` method and in event loop we will read registered events. After catching registered event, we will use function, passed to data keyword arg as our callback function for writing data into file.
