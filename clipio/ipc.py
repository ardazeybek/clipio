"""Single-instance channel: the running app listens on a local socket, `clipio` commands talk to it."""
import getpass
import os
import re

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket


# Socket name for this user (a named pipe on Windows, a socket file elsewhere)
def server_name() -> str:
    if override := os.environ.get("CLIPIO_IPC_NAME"):
        return override
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    return "clipio-" + re.sub(r"[^A-Za-z0-9_-]", "_", user)


# Send one command to the running app and return its reply (None when it is not running)
def send(command: str, timeout_ms: int = 2000) -> str | None:
    sock = QLocalSocket()
    sock.connectToServer(server_name())
    if not sock.waitForConnected(timeout_ms):
        return None
    sock.write((command.strip() + "\n").encode("utf-8"))
    sock.flush()
    sock.waitForBytesWritten(timeout_ms)
    reply = b""
    while not reply.endswith(b"\n"):
        reply += bytes(sock.readAll())   # the app may already have answered and closed
        if reply.endswith(b"\n") or not sock.waitForReadyRead(timeout_ms):
            break
    reply += bytes(sock.readAll())
    sock.abort()
    return reply.decode("utf-8", errors="replace").strip()


# True when a Clipio app is already running for this user
def is_running() -> bool:
    return send("ping", 500) == "pong"


class _Connection(QObject):
    """One client connection: collects a line, answers it and closes."""

    def __init__(self, sock, handler, parent=None):
        super().__init__(parent)
        self._sock = sock
        self._handler = handler
        self._buf = bytearray()
        self._answered = False
        sock.readyRead.connect(self._read)
        sock.disconnected.connect(self._done)
        if sock.bytesAvailable():
            self._read()   # the command may have arrived before readyRead was connected

    # Collect bytes until a full line is in; then answer and close
    def _read(self) -> None:
        self._buf.extend(bytes(self._sock.readAll()))
        if b"\n" not in self._buf or self._answered:
            return
        self._answered = True
        line = self._buf.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
        self._sock.write((str(self._handler(line)) + "\n").encode("utf-8"))
        self._sock.flush()
        self._sock.disconnectFromServer()

    # Free the socket and this helper once the client is gone
    def _done(self) -> None:
        self._sock.deleteLater()
        self.deleteLater()


class Server(QObject):
    """Receives one-line commands; `handler(command) -> reply` runs on the main thread."""

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self._handler = handler
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._accept)

    # Start listening; remove a stale socket left by a crashed instance first
    def listen(self) -> bool:
        name = server_name()
        if self._server.listen(name):
            return True
        QLocalServer.removeServer(name)
        return self._server.listen(name)

    # Hand every waiting connection to its own helper
    def _accept(self) -> None:
        while self._server.hasPendingConnections():
            _Connection(self._server.nextPendingConnection(), self._handler, self)

    # Stop listening
    def close(self) -> None:
        self._server.close()
