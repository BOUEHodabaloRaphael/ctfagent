#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    s = socket.socket()
    s.settimeout(180)
    try:
        s.connect((HOST, PORT))
        # STARTDT ACT
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print('STARTDT:', r.hex() if r else 'none')
        tx = [0]; rx = [0]
        def send_i(asdu):
            apci = bytes([0x68, len(asdu)+4, tx[0]&0xFF,(tx[0]>>8)&0xFF, rx[0]&0xFF,(rx[0]>>8)&0xFF])
            tx[0] += 2
            s.send(apci+asdu)
        def send_s():
            # S-frame: control = 0x01 00 00 00? Or format 0x01 followed by rx
            apci = bytes([0x68, 0x04, 0x01, 0x00, rx[0]&0xFF, (rx[0]>>8)&0xFF])
            s.send(apci)
        
        # Send GI
        # C_IC_NA_1: Type 100, VSQ=1, COT=6 (activation), OA=0, CA=1 (LE), IOA=0, QOI=20
        asdu = bytes([100, 0x01, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x14])
        send_i(asdu)
        time.sleep(15)
        all_data = b''
        while True:
            try:
                s.settimeout(10)
                r = s.recv(8192)
                if not r: break
                all_data += r
                print('RCV:', r.hex())
                # try to parse - look for I-frames
                # send S-ack if needed
                if len(r) >= 6 and r[0] == 0x68:
                    # check if it's I-frame (bit0 of ctrl1 is 0)
                    if (r[2] & 0x01) == 0: # I-frame
                        # extract rx from our perspective
                        pass
            except socket.timeout:
                break
            except:
                break
        print('TOTAL LEN:', len(all_data))
        if b'CTF{' in all_data:
            print(all_data)
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
