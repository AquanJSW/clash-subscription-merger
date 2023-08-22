import socket


def get_tcp_port_picker(port=1024):
    """Get a generator that yields free tcp ports."""
    max_port = 65535
    while port <= max_port:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            yield port
        except OSError:
            pass
        port += 1

    raise IOError('no free tcp ports')
