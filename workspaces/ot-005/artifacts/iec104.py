import socket, struct

def build_u(ctrl1):
    return bytes([0x68, 0x04, ctrl1, 0x00, 0x00, 0x00])

def build_i(asdu, tx=0, rx=0):
    # I format: control1 = (tx_seq << 1) & 0xFE, control2 = (tx_seq >> 7) & 0xFF
    # control3 = (rx_seq << 1) & 0xFE, control4 = (rx_seq >> 7) & 0xFF
    c1 = (tx << 1) & 0xFE
    c2 = (tx >> 7) & 0xFF
    c3 = (rx << 1) & 0xFE
    c4 = (rx >> 7) & 0xFF
    apci = bytes([0x68, 4+len(asdu), c1, c2, c3, c4])
    return apci + asdu

class IEC104:
    def __init__(self, host, port):
        self.s = socket.socket()
        self.s.settimeout(5)
        self.s.connect((host,port))
        self.tx=0; self.rx=0
        
    def u(self, ctrl1):
        self.s.send(build_u(ctrl1))
        return self.s.recv(1024)
        
    def i(self, asdu):
        f = build_i(asdu, self.tx, self.rx)
        self.s.send(f)
        self.tx += 1
        return self.s.recv(4096)
        
    def startdt(self):
        r=self.u(0x07)
        return r

def gi_asdu(ca=1, qoi=20):
    # TypeId 100 C_IC_NA_1: VSQ=1, COT=act(6), CA LE, IOA 0, QOI
    asdu = bytes([0x64, 0x01, 0x06, ca & 0xff, (ca>>8)&0xff, 0x00, 0x00, 0x00, qoi])
    return asdu
