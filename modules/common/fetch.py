import io
import tls
import time
import socket
import json


class HTTPException(Exception):
    def __init__(self, fetch):
        self.fetch = fetch
        super().__init__(f"HTTP errror {fetch.http_status}")


class AsyncFetch:
    FETCH_BLOCK_SIZE = 1024
    buffer = bytearray(FETCH_BLOCK_SIZE)

    STATUS_TEXT = ["Idle", "Fetching", "Done", "Error"]
    IDLE = 0
    FETCHING = 1
    DONE = 2
    ERROR = 3

    def __init__(self, host, port=None, use_tls=True, debug=False):
        self._debug = debug

        self._fetch = None  # hold the pending fetch
        self._sock = None  # hold the open socket

        self._last_update = None  # keep track of the last updated time

        self._buffer = None  # buffer for BytesIO and StringIO
        self._buffer_len = 0  # amount of data actually in our buffer

        self._interval = 0  # fetch interval in seconds
        self._path = None
        self._file = None  # Target file, or none to fetch to a stream

        self._on_complete = None
        self._on_error = None

        self._data = None
        self._method = "GET"

        self._headers = {}
        self._response_headers = {}
        self._status_code = None

        self._use_tls = use_tls

        self._host = host
        self._port = port or 443 if use_tls else 80

        self._status = AsyncFetch.IDLE

    def fetch(self, path, file=None, interval=None, headers=None, data=None, method=None, blocking=False):
        if self._fetch:
            raise RuntimeError("Cannot interrupt a running fetch...")

        if path.startswith(("http://", "https://")):
            raise ValueError("fetch requires a relative path, not a full URL.")

        self._buffer_len = 0

        if interval is not None:
            self._interval = interval

        # Make sure we re-trigger is the interval is 0 (no-repeat)
        if self._interval == 0:
            self._last_update = None

        if headers is not None:
            self._headers = headers

        self._path = path[1:] if path.startswith("/") else path
        self._file = file
        self._data = data

        if method is not None:
            self._method = method

        if "User-Agent" not in self._headers:
            self._headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.4 Safari/605.1.15"

        if blocking:
            self.finish()
            return self.stream

        return None

    def _http_fetch(self):
        self._status_code = None
        self._response_headers = {}

        self._headers["Connection"] = "keep-alive"

        if self._data is not None and self._method == "GET":
            self._method = "POST"

        if self._sock is None:
            # New socket required
            sock_family, sock_type, sock_proto, _, sock_addr = socket.getaddrinfo(self._host, self._port, 0, socket.SOCK_STREAM)[0]
            self._sock = socket.socket(sock_family, sock_type, sock_proto)
            self._sock.setblocking(True)
            try:
                self._sock.connect(sock_addr)
                if self._use_tls:
                    context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
                    context.verify_mode = tls.CERT_NONE
                    self._sock = context.wrap_socket(self._sock, server_hostname=self._host, do_handshake_on_connect=True)
                yield

            except OSError as e:
                self._sock.close()
                self._sock = None
                raise e

        self._sock.setblocking(True)

        try:
            self._sock.write(f"{self._method} /{self._path} HTTP/1.0\r\nHost: {self._host}\r\n".encode("UTF-8"))

            for k in self._headers:
                _ = self._sock.write(f"{k}: {self._headers[k]}\r\n".encode("UTF-8"))

            if self._data:
                self._sock.write(f"Content-Length: {len(self._data)}\r\n\r\n".encode("UTF-8"))
                self._sock.write(self._data)

            else:
                self._sock.write(b"\r\n")

            self._sock.setblocking(False)

            while True:
                yield

                line = self._sock.readline()

                if line is None:
                    continue

                elif line.startswith(b"\r\n"):
                    break

                elif line.startswith(b"HTTP/"):
                    self._status_code = int(line.decode("UTF-8").strip().split(" ")[1])

                elif b": " in line:
                    k, v = line.decode("UTF-8").strip().split(": ")
                    self._response_headers[k] = v

            if "chunked" in self._response_headers.get("Transfer-Encoding", ()):
                raise ValueError("Unsupported Transfer-Encoding chunked")

        except OSError:
            self._sock.close()
            self._sock = None
            raise

        self._content_length = int(self._response_headers.get("Content-Length", 0))

        if self._debug:
            print(f"Got {self._content_length} bytes")

    def _fetch_to_stream(self):
        # Grab the data
        yield from self._http_fetch()

        self._sock.setblocking(False)

        self._buffer_len = 0

        bytes_available = self._content_length

        if self._file:
            stream = open(self._file, "wb")
            if self._debug:
                print("Streaming to {self._file}")

        else:
            if self._buffer is None:
                self._buffer = io.BytesIO(bytes_available)
            stream = self._buffer
            stream.seek(0)
            if self._debug:
                print("Streaming to buffer")

        while self._buffer_len < bytes_available:
            yield
            length = self._sock.readinto(AsyncFetch.buffer)
            if length in (0, None):
                continue
            self._buffer_len += length
            self._content_length -= length
            if self._debug:
                print(f"Fetched {self._buffer_len}/{bytes_available} bytes")
            stream.write(AsyncFetch.buffer[:length])

        # Leave the BytesIO stream open
        if self._file:
            stream.close()

    def update(self):
        self._status = AsyncFetch.IDLE

        if self._path is not None:
            if self._last_update is None or (self._interval > 0 and self.duration > int(self._interval * 1000)):
                # Don't overwrite an existing fetch operation if the interval comes up...
                if self._fetch is None and self._debug:
                    print("Fetch started")
                self._fetch = self._fetch or self._fetch_to_stream()

            if self._fetch:
                try:
                    next(self._fetch)
                    self._status = AsyncFetch.FETCHING

                except StopIteration as e:
                    if self._debug:
                        print("Fetch done")
                    self._last_update = time.ticks_ms()
                    self._fetch = None

                    if self._status_code == 200:
                        self._status = AsyncFetch.DONE
                        if callable(self._on_complete):
                            self._on_complete(self)

                    else:
                        self._status = AsyncFetch.ERROR
                        if not callable(self._on_error) or not self._on_error(self):
                            raise HTTPException(self) from e

        return self._status

    @property
    def duration(self):
        return time.ticks_diff(time.ticks_ms(), self._last_update)

    @property
    def status(self):
        return self._status

    @property
    def source(self):
        return self._path

    @property
    def destination(self):
        return self._file

    @property
    def http_status(self):
        return self._status_code

    @property
    def http_response_headers(self):
        return self._response_headers

    @property
    def stream(self):
        # Return a FileIO for a saved file or a StringIO containing the buffer value
        return open(self._file, "r") if self._file else io.StringIO(memoryview(self._buffer.getvalue())[: self._buffer_len], encoding="UTF-8")

    def to_json(self):
        return json.load(self.stream)

    def finish(self):
        # Force a blocking finish of the fetch command
        while self.update() != AsyncFetch.DONE:
            pass

    def on_complete(self, handler):
        self._on_complete = handler

    def on_error(self, handler):
        self._on_error = handler


if __name__ == "__main__":

    api = AsyncFetch("postman-echo.com", 443, use_tls=True, debug=True)
    # api = AsyncFetch("pimoroni.github.io", 443, use_tls=True, debug=True)

    # Run update once before we have a valid fetch
    assert api.update() == AsyncFetch.IDLE

    # Handler for the completed fetch
    @api.on_complete
    def handle_complete(fetch):
        global t_start
        print(fetch.to_json())

    # Handler for an HTTP error
    # .update() will additionally raise an Exception
    @api.on_error
    def handle_error(fetch):
        # print(fetch.stream.read())
        if fetch.http_status == 404:
            fetch.fetch("/feed2image/jokeapi-59.json")
            return True  # Don't raise an exception at the "update" call site

        if fetch.http_status == 302:
            if "location" in fetch.http_response_headers:
                print(f"302 redirect to: {fetch.http_response_headers['location']}")

        return False  # We can't handle this, raise

    # Start a fetch
    api.fetch("/")
    # api.fetch("/get", interval=0, method="GET")
    # api.fetch("/post", interval=0, method="POST", data='{"test": 1}'.encode("UTF-8"), headers={"content-type": "application/json"})
    # api.fetch("/post", interval=0, method="POST", data='test=1&another=2'.encode("UTF-8"), headers={"content-type": "application/x-www-form-urlencoded"})
    # api.fetch("/feed2image/jokeapi-5999.json")

    while True:
        t_start = time.ticks_ms()

        try:
            api.update()
        except HTTPException as e:
            print("Exception was raised!")
            if e.fetch.http_status != 404:
                raise e

        t_took = time.ticks_diff(time.ticks_ms(), t_start)
        if t_took > 0 or api.status == AsyncFetch.IDLE:
            print(f"update took: {t_took}ms, status: {AsyncFetch.STATUS_TEXT[api.status]}")
        if api.status == AsyncFetch.IDLE:
            break
