import sys
from PIL import Image

img = Image.open("/home/kali/ctfagent/workspaces/nctf26-tisserands/artifacts/affiche.png").convert("RGB")
w, h = img.size
pix = img.load()

bits = []
for y in range(h):
    for x in range(w):
        r, g, b = pix[x, y]
        bits.append(r & 1)

def bits_to_bytes(bits):
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        out.append(byte)
    return bytes(out)

all_bytes = bits_to_bytes(bits)
length = int.from_bytes(all_bytes[0:4], "big")
print("Declared length (bytes):", length)
print("Total available bytes in red channel:", len(all_bytes))

if 0 < length < len(all_bytes) - 4:
    msg = all_bytes[4:4+length]
    print("RAW:", msg)
    try:
        print("UTF-8:", msg.decode("utf-8"))
    except Exception as e:
        print("decode failed:", e)
else:
    print("Length looks implausible, dumping first 64 bytes after header for inspection:")
    print(all_bytes[4:68])
