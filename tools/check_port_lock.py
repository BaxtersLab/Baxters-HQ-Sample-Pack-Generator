import socket

PORT = 51837
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('127.0.0.1', PORT))
    print('BIND_OK')
    s.close()
except Exception as e:
    print('BIND_FAILED')
