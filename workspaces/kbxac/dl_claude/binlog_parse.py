#!/usr/bin/env python3
"""Minimal MySQL binlog v4 parser - enough to extract UPDATE_ROWS events
for runtime_config and their timestamps, without needing mysqlbinlog."""
import struct
import sys

EVENT_NAMES = {
    2: "QUERY_EVENT",
    4: "ROTATE_EVENT",
    15: "FORMAT_DESCRIPTION_EVENT",
    16: "XID_EVENT",
    19: "TABLE_MAP_EVENT",
    23: "WRITE_ROWS_EVENTv1",
    24: "UPDATE_ROWS_EVENTv1",
    25: "DELETE_ROWS_EVENTv1",
    30: "WRITE_ROWS_EVENTv2",
    31: "UPDATE_ROWS_EVENTv2",
    32: "DELETE_ROWS_EVENTv2",
    33: "GTID_EVENT",
    34: "ANONYMOUS_GTID_EVENT",
    35: "PREVIOUS_GTIDS_EVENT",
}

def parse_file(path, table_filter=None):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:4] == b'\xfebin', f"bad magic {data[:4]!r}"
    pos = 4
    table_map = {}  # table_id -> table_name
    events = []
    checksum_len = 4  # assume CRC32 (common default); will auto-detect from FDE
    first = True
    while pos < len(data):
        if pos + 19 > len(data):
            break
        timestamp, event_type, server_id, event_size, next_pos = struct.unpack_from('<IBIII', data, pos)
        header_len = 19
        body_start = pos + header_len
        body_end = pos + event_size
        if body_end > len(data):
            break
        body = data[body_start:body_end]
        name = EVENT_NAMES.get(event_type, f"TYPE_{event_type}")

        if event_type == 15:
            # FORMAT_DESCRIPTION_EVENT: last byte(s) indicate checksum algorithm (byte before crc, if present)
            # Body: 2(version) + 50(server version str) + 4(create ts) + 1(header len) + N(post header lens)
            # checksum algo byte is body[-5] typically (1 byte) followed by 4-byte crc
            if len(body) >= 1:
                algo = body[-5] if len(body) >= 5 else 0
                checksum_len = 4 if algo == 1 else 0
        elif event_type == 19:
            # TABLE_MAP_EVENT
            b = body[:-checksum_len] if checksum_len else body
            table_id = int.from_bytes(b[0:6], 'little')
            # flags = b[6:8]
            off = 8
            schema_len = b[off]; off += 1
            schema = b[off:off+schema_len].decode(errors='replace'); off += schema_len
            off += 1  # null term
            table_len = b[off]; off += 1
            table = b[off:off+table_len].decode(errors='replace'); off += table_len
            table_map[table_id] = (schema, table)
        elif event_type in (24, 31):  # UPDATE_ROWS v1/v2
            b = body[:-checksum_len] if checksum_len else body
            table_id = int.from_bytes(b[0:6], 'little')
            tbl = table_map.get(table_id, ('?', '?'))
            if table_filter is None or tbl[1] == table_filter:
                events.append((timestamp, event_type, tbl, b))
        pos = next_pos if next_pos > pos else body_end
        first = False
    return events, table_map

if __name__ == '__main__':
    import glob
    for fn in sys.argv[1:]:
        print(f"=== {fn} ===")
        events, tmap = parse_file(fn, table_filter='runtime_config')
        print("tables seen:", tmap)
        for ts, et, tbl, b in events:
            print(ts, EVENT_NAMES.get(et), tbl, len(b), 'bytes raw row data')
