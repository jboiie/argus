"""Regression test: --self-check must never touch the network.

Blocks socket.socket.connect process-wide and runs both modules'
--self-check paths under it. Any accidental network call (API key check
alone doesn't count - only an actual outbound connection does) raises
immediately instead of silently succeeding, hanging, or - as happened
once - falling through to a real live run.
"""

import asyncio
import socket
import sys


class NetworkCallAttempted(Exception):
    pass


_real_connect = socket.socket.connect
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _blocked_connect(self, address, *args, **kwargs):
    # Windows' proactor event loop opens a loopback socketpair just to
    # construct an event loop at all (asyncio.run's own internals, nothing
    # to do with this module's code) - only a connection to a real,
    # non-loopback host counts as the network call this test guards against.
    host = address[0] if isinstance(address, tuple) else address
    if host not in _LOOPBACK:
        raise NetworkCallAttempted(f"socket.connect called with address={address!r}")
    return _real_connect(self, address, *args, **kwargs)


def main() -> None:
    socket.socket.connect = _blocked_connect
    try:
        sys.argv = ["drift.sampler", "--self-check"]
        import drift.sampler as sampler
        sampler.main()
        print("drift.sampler --self-check: no network calls, passed.")

        sys.argv = ["drift.faithfulness_variants", "--self-check"]
        import drift.faithfulness_variants as variants
        asyncio.run(variants.main())
        print("drift.faithfulness_variants --self-check: no network calls, passed.")
    finally:
        socket.socket.connect = _real_connect

    print("\nAll --self-check paths passed with zero network calls.")


if __name__ == "__main__":
    main()
