import threading
import time
import socket
import logging
import json
import os
import sys
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


class HRTConnector:
    """
    Handles non-blocking connection attempts to Hot Rod Tuner.
    HRT remains read-only. Protocol is already established.
    """

    def __init__(self, controller):
        self.controller = controller
        self.is_linked = False
        self.thread = None
        self.host = '127.0.0.1'
        self.port = 8090
        # whether the current attempt was manually triggered from Settings
        self.manual_triggered = False

    def start_autolink(self, host: str = '127.0.0.1', port: int = 8090):
        """
        Launch background thread to attempt linking.
        """
        self.host = host
        self.port = port
        # reset manual trigger flag on programmatic starts
        try:
            if not getattr(self, 'manual_triggered', False):
                self.manual_triggered = False
        except Exception:
            pass

        if self.thread is not None and self.thread.is_alive():
            logger.debug('HRT autolink: thread already running')
            return
        self.thread = threading.Thread(target=self._autolink_loop, daemon=True)
        self.thread.start()

    def _autolink_loop(self):
        """
        Attempts to connect to HRT every 2 seconds until successful.
        Non-blocking, safe, read-only.
        """
        logger.info('HRT autolink: starting background attempts to %s:%d', self.host, self.port)
        # Use retry interval recommended by HRT docs (30s)
        retry_interval = 30
        while not self.is_linked:
            try:
                # tell controller we're attempting a link (timestamped)
                try:
                    if hasattr(self.controller, 'record_hrt_attempt'):
                        try:
                            self.controller.record_hrt_attempt()
                        except Exception:
                            pass
                except Exception:
                    pass

                msg = f'HRT: attempting /link POST to {self.host}:{self.port}'
                logger.debug(msg)
                try:
                    # Prefer controller.log_debug (thread-safe) to update debug output
                    if hasattr(self.controller, 'log_debug'):
                        try:
                            self.controller.log_debug(msg)
                        except Exception:
                            pass
                    else:
                        try:
                            mw = getattr(self.controller, 'main_window', None)
                            if mw is not None and hasattr(mw, 'log_debug_message'):
                                mw.log_debug_message(msg)
                        except Exception:
                            pass
                except Exception:
                    pass

                if self._attempt_link():
                    self.is_linked = True
                    msg = f'HRT: /link handshake succeeded at {self.host}:{self.port}'
                    logger.info(msg)
                    try:
                        if hasattr(self.controller, 'log_debug'):
                            try:
                                self.controller.log_debug(msg)
                            except Exception:
                                pass
                        elif hasattr(self.controller, 'main_window') and self.controller.main_window is not None:
                            try:
                                self.controller.main_window.log_debug_message(msg)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        if hasattr(self.controller, 'on_hrt_link_success'):
                            try:
                                self.controller.on_hrt_link_success()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return
                else:
                    msg = f'HRT: no response from {self.host}:{self.port}; retrying in {retry_interval}s'
                    logger.debug(msg)
                    try:
                        if hasattr(self.controller, 'log_debug'):
                            try:
                                self.controller.log_debug(msg)
                            except Exception:
                                pass
                        elif hasattr(self.controller, 'main_window') and self.controller.main_window is not None:
                            try:
                                self.controller.main_window.log_debug_message(msg)
                            except Exception:
                                pass

                        # if this was a manual trigger, show a short toast to inform the user
                        try:
                            if getattr(self, 'manual_triggered', False):
                                try:
                                    # Request a thread-safe toast via controller if available
                                    if hasattr(self.controller, 'request_toast'):
                                        try:
                                            self.controller.request_toast('HRT not responding', duration_ms=3000)
                                        except Exception:
                                            pass
                                    else:
                                        mw = getattr(self.controller, 'main_window', None)
                                        if mw is not None and hasattr(mw, 'show_toast'):
                                            try:
                                                mw.show_toast('HRT not responding', duration_ms=3000)
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                logger.debug('HRT autolink: unexpected error during autolink attempt', exc_info=True)
            time.sleep(retry_interval)

    def _attempt_link(self) -> bool:
        """
        Performs the actual handshake using the established protocol.
        This must match the dev instructions in the HRT folder.
        """
        try:
            url = f'http://{self.host}:{self.port}/link'
            body = {
                "app_name": "HQSPG",
                "exe_path": os.path.abspath(sys.argv[0]) if len(sys.argv) > 0 else os.getcwd(),
                "pid": os.getpid(),
            }
            data = json.dumps(body).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'Content-Type': 'application/json'
            }, method='POST')
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_data = resp.read()
                    try:
                        parsed = json.loads(resp_data.decode('utf-8'))
                        ok = parsed.get('ok', False)
                        if ok:
                            return True
                    except Exception:
                        logger.debug('HRT autolink: unable to parse JSON response', exc_info=True)
            except urllib.error.HTTPError as e:
                logger.debug('HRT autolink: HTTP error %s', e.code)
            except urllib.error.URLError:
                # server not available or connection refused
                pass
            except Exception:
                logger.debug('HRT autolink: unexpected error during HTTP request', exc_info=True)
            # ensure controller knows link is not active
            try:
                if hasattr(self, 'controller') and self.controller is not None:
                    try:
                        setattr(self.controller, 'hrt_is_linked', False)
                    except Exception:
                        pass
            except Exception:
                pass
            return False
        except Exception:
            return False
