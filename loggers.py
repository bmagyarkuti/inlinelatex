import logging
from sys import stdout

console_handler = logging.StreamHandler(stream=stdout)

server_logger = logging.getLogger('server_logger')
server_logger.setLevel(logging.INFO)
server_logger.addHandler(console_handler)

tex_logger = logging.getLogger('tex_logger')

