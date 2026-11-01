"""Story 1.6 (FR-22): the conftest guard blocks the network but not loopback or socketpair."""

import socket

import pytest


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
def test_non_loopback_connect_fails(method: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with pytest.raises(RuntimeError, match="uten nett"):
            getattr(sock, method)(("192.0.2.1", 80))


def test_ipv6_non_loopback_fails() -> None:
    if not socket.has_ipv6:
        pytest.skip("IPv6 er ikke tilgjengelig")
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        with pytest.raises(RuntimeError, match="uten nett"):
            sock.connect(("2001:db8::1", 80, 0, 0))


def test_loopback_connect_works() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(server.getsockname())


def test_socketpair_works() -> None:
    a, b = socket.socketpair()
    with a, b:
        a.sendall(b"ok")
        assert b.recv(2) == b"ok"
