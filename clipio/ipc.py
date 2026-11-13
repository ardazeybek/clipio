"""Local socket channels: `clipio` commands and the panel talk to the background service,
and the service talks to the panel process. role "" is the service, role "panel" the panel."""
import getpass
import hashlib
import os
import re

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket

PANEL = "panel"
MAX_NAME = 32           # longest socket name (fits macOS' 104-byte socket path limit)
_pending: set = set()   # sockets of fire-and-forget messages still on their way


# Socket name for this user and role (a named pipe on Windows, a socket file elsewhere)
def server_name(role: str = "") -> str:
    if override := os.environ.get("CLIPIO_IPC_NAME"):
        base = override
    else:
        try:
            user = getpass.getuser()
        except Exception:
            user = "user"
        base = "clipio-" + re.sub(r"[^A-Za-z0-9_-]", "_", user)
    name = f"{base}-{role}" if role else base
    # macOS keeps socket paths under 104 bytes and its temp folder is long: shorten long names
    if len(name) > MAX_NAME:
        name = name[:MAX_NAME - 9] + "-" + hashlib.sha1(name.encode()).hexdigest()[:8]
    return name


# Send one command and wait for its reply (None when nobody listens)
def send(command: str, timeout_ms: int = 2000, role: str = "") -> str | None:
    sock = QLocalSocket()
    sock.connectToServer(server_name(role))
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


# True when the Clipio service (or, with role "panel", the panel) is running for this user
def is_running(role: str = "") -> bool:
    return send("ping", 500, role) == "pong"


# Send a command without waiting (needs a running Qt event loop); on_fail runs when nobody listens
def post(command: str, role: str = "", on_fail=None) -> None:
    sock = QLocalSocket()
    _pending.add(sock)
    sent = []   # set once connected: later errors (the other side hanging up) are not failures

    # Write the line once connected, then hang up
    def connected():
        sent.append(True)
        sock.write((command.strip() + "\n").encode("utf-8"))
        sock.flush()
        sock.disconnectFromServer()

    # Nobody listens
    def failed(_err):
        if sent or sock not in _pending:
            return
        finish()
        if on_fail:
            on_fail()

    # Forget the socket
    def finish():
        if sock in _pending:
            _pending.discard(sock)
            sock.deleteLater()

    sock.connected.connect(connected)
    sock.errorOccurred.connect(failed)
    sock.disconnected.connect(finish)
    sock.connectToServer(server_name(role))


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
        reply = str(self._handler(line))
        if self._sock.state() == QLocalSocket.LocalSocketState.ConnectedState:   # a fire-and-forget sender may be gone
            self._sock.write((reply + "\n").encode("utf-8"))
            self._sock.flush()
            self._sock.disconnectFromServer()

    # Answer a line that came with the hang-up (fire-and-forget senders), then free the socket
    def _done(self) -> None:
        if not self._answered:
            self._read()
        self._sock.deleteLater()
        self.deleteLater()


class Server(QObject):
    """Receives one-line commands; `handler(command) -> reply` runs on the main thread."""

    def __init__(self, handler, parent=None, role: str = ""):
        super().__init__(parent)
        self._handler = handler
        self._role = role
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._accept)

    # Start listening; remove a stale socket left by a crashed instance first
    def listen(self) -> bool:
        name = server_name(self._role)
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
