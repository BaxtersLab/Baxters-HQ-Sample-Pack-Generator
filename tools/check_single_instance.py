from PySide6.QtNetwork import QLocalServer

server_name = 'hqspg_single_instance_v1'
server = QLocalServer()
ok = server.listen(server_name)
print(ok)
