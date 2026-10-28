#!/usr/bin/env python3
"""Minimal ttyd websocket client driver (non-interactive)."""
import sys
import base64
import asyncio
import websockets

HOST = "nsa.chal.hitconctf.com"
PORT = 30307
USER = "player"
PASS = "eb80976f-91e5-445f-ac94-f7ddf42601f3"

async def run(commands, read_seconds=2.0):
    auth = base64.b64encode(f"{USER}:{PASS}".encode()).decode()
    uri = f"ws://{HOST}:{PORT}/ws"
    headers = {"Authorization": f"Basic {auth}"}
    async with websockets.connect(uri, subprotocols=["tty"], additional_headers=headers, max_size=None) as ws:
        # ttyd init handshake
        await ws.send('{"AuthToken":"","columns":200,"rows":50}')
        out = []
        async def reader():
            try:
                while True:
                    msg = await ws.recv()
                    if isinstance(msg, bytes) and len(msg) > 0 and msg[0:1] == b'0':
                        text = msg[1:].decode(errors="replace")
                        out.append(text)
                        print(text, end="", flush=True)
            except websockets.exceptions.ConnectionClosed:
                pass
        reader_task = asyncio.create_task(reader())
        await asyncio.sleep(0.5)
        for cmd in commands:
            await ws.send(b'0' + (cmd + "\n").encode())
            await asyncio.sleep(read_seconds)
        reader_task.cancel()
        return "".join(out)

if __name__ == "__main__":
    args = sys.argv[1:]
    read_seconds = 2.0
    if args and args[0].startswith("--wait="):
        read_seconds = float(args[0].split("=", 1)[1])
        args = args[1:]
    cmds = args
    asyncio.run(run(cmds, read_seconds=read_seconds))
