"""Small shared helpers (entropy, hexdump, defanging, formatting)."""
from __future__ import annotations

import math
import re
from collections import Counter


ENTROPY_SAMPLE = 4 * 1024 * 1024


def entropy(data: bytes, sample: int = ENTROPY_SAMPLE) -> float:
    """Shannon entropy in bits/byte (0.0 .. 8.0).

    Exact for inputs up to ``sample`` bytes; larger inputs are estimated from 64 evenly spaced
    chunks totalling ``sample`` bytes (the estimate is within ~0.01 bit for typical data).
    """
    if not data:
        return 0.0
    if len(data) > sample:
        chunk = sample // 64
        step = len(data) // 64
        data = b"".join(data[i * step:i * step + chunk] for i in range(64))
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in Counter(data).values())


def block_entropy(data: bytes, block: int = 4096, max_blocks: int = 2048) -> list[float]:
    """Entropy per fixed-size block, used for entropy maps. Large files are sub-sampled."""
    if not data:
        return []
    count = (len(data) + block - 1) // block
    step = max(1, count // max_blocks)
    return [round(entropy(data[i * block:(i + 1) * block]), 3) for i in range(0, count, step)]


def hexdump(data: bytes, base: int = 0, width: int = 16) -> str:
    lines = []
    for i in range(0, len(data), width):
        row = data[i:i + width]
        hx = " ".join(f"{b:02x}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        lines.append(f"{base + i:08x}  {hx:<{width * 3 - 1}}  |{asc}|")
    return "\n".join(lines)


def defang(value: str) -> str:
    """Make an indicator safe to paste in reports (hxxp, [.])."""
    v = re.sub(r"(?i)^http", lambda m: "hxxp" if m.group(0).islower() else "HXXP", value)
    v = v.replace("://", "[://]") if v.lower().startswith("hxxp") else v
    # defang dots in the host-looking part only (keeps paths readable)
    m = re.match(r"^(hxxps?\[://\])?([^/\s]+)(.*)$", v, re.I | re.S)
    if m:
        scheme, host, rest = m.group(1) or "", m.group(2), m.group(3)
        host = host.replace(".", "[.]").replace("@", "[@]")
        return scheme + host + rest
    return v


def parse_int(text: str) -> int:
    """Parse 0x.. / decimal integers given on the command line."""
    return int(text.strip().replace("_", ""), 0)


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{n} B"
