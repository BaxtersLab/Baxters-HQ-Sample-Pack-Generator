import socket
import threading
import time

class HotRodConnector:
    """
    TCP connector with:
      - handshake
      - heartbeat
      - linked/unlinked states
      - log callbacks
    """
    def __init__(self, host="127.0.0.1", port=8765, heartbeat_interval=5.0):
        self.host = host
        self.port = port
        self.connected = False      # TCP connected
        self.linked = False         # handshake complete
        self._sock = None
        self._listener_thread = None
        self._heartbeat_thread = None
        self._stop_flag = False
        self._heartbeat_interval = heartbeat_interval

        self._callbacks = {
            "on_connect": None,
            "on_disconnect": None,
            "on_linked": None,
            "on_unlinked": None,
            "on_message": None,
            "on_log": None,
        }

    def set_callback(self, event, fn):
        self._callbacks[event] = fn

    def _log(self, msg: str):
        cb = self._callbacks.get("on_log")
        if cb:
            try:
                cb(msg)
            except Exception:
                pass

    # --------------------------------------------------------
    #  CONNECT
    # --------------------------------------------------------
    def connect(self):
        self._stop_flag = False
        self._log(f"Connecting to HRT at {self.host}:{self.port}...")
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            self.connected = True

            if self._callbacks["on_connect"]:
                try:
                    self._callbacks["on_connect"]()
                except Exception:
                    pass

            # Start listener
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()

            # Send handshake
            self._send_handshake()

            # Start heartbeat
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

        except Exception as exc:
            self._log(f"HRT connect failed: {exc}")
            self._cleanup(disconnected=True)

    # --------------------------------------------------------
    #  HANDSHAKE
    # --------------------------------------------------------
    def _send_handshake(self):
        self._log("Sending HRT handshake...")
        self.send('{"type":"handshake","client":"HQSPG","version":"1.0"}\n')

    # --------------------------------------------------------
    #  HEARTBEAT
    # --------------------------------------------------------
    def _heartbeat_loop(self):
        while not self._stop_flag and self.connected:
            time.sleep(self._heartbeat_interval)
            try:
                self.send('{"type":"heartbeat"}\n')
            except Exception as exc:
                self._log(f"HRT heartbeat failed: {exc}")
                self._cleanup(disconnected=True)
                break

    # --------------------------------------------------------
    #  LISTENER
    # --------------------------------------------------------
    def _listen(self):
        buf = ""
        try:
            while self.connected and not self._stop_flag:
                data = self._sock.recv(4096)
                if not data:
                    break
                buf += data.decode(errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self._handle_line(line)
        finally:
            self._cleanup(disconnected=True)

    # --------------------------------------------------------
    #  MESSAGE HANDLER
    # --------------------------------------------------------
    def _handle_line(self, line: str):
        self._log(f"HRT <= {line}")

        if '"type":"handshake_ok"' in line:
            self.linked = True
            if self._callbacks["on_linked"]:
                try:
                    self._callbacks["on_linked"]()
                except Exception:
                    pass

        elif '"type":"handshake_error"' in line:
            self.linked = False
            if self._callbacks["on_unlinked"]:
                try:
                    self._callbacks["on_unlinked"]()
                except Exception:
                    pass

        else:
            if self._callbacks["on_message"]:
                try:
                    self._callbacks["on_message"](line)
                except Exception:
                    pass

    # --------------------------------------------------------
    #  SEND
    # --------------------------------------------------------
    def send(self, msg: str):
        if not self.connected or not self._sock:
            raise RuntimeError("HRT not connected")
        self._log(f"HRT => {msg.strip()}")
        self._sock.sendall(msg.encode())

    # --------------------------------------------------------
    #  DISCONNECT
    # --------------------------------------------------------
    def disconnect(self):
        self._log("Disconnecting from HRT...")
        self._stop_flag = True
        self._cleanup(disconnected=True)

    # --------------------------------------------------------
    #  CLEANUP
    # --------------------------------------------------------
    def _cleanup(self, disconnected: bool):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

        self._sock = None
        was_connected = self.connected
        self.connected = False

        if self.linked:
            self.linked = False
            if self._callbacks["on_unlinked"]:
                try:
                    self._callbacks["on_unlinked"]()
                except Exception:
                    pass

        if disconnected and was_connected:
            if self._callbacks["on_disconnect"]:
                try:
                    self._callbacks["on_disconnect"]()
                except Exception:
                    pass
