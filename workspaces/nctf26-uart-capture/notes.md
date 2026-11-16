# uart-capture (HARDWARE, 100pts)

Status: SOLVED (by user directly on the platform, confirmed match with agent's independent decode).

## Challenge
Logic analyzer capture (`capture.csv`): time_ns, d0_uart, d1_refclk. ASCII message
transmitted over UART on d0; d1 is a reference clock (toggled every 3000ns, not
directly used for decode).

## Method
- Sample step in CSV: 1000ns.
- d0 idle high; found start-bit falling edges, measured inter-edge gaps -> finest
  common granularity 8000ns = 1 UART bit period (125000 baud).
- Standard 8N1 async frame: start bit (0), 8 data bits LSB-first, stop bit (1).
  Sampled mid-bit (start + samples_per_bit*(n+0.5)) for each of 8 bits + stop.
- All 29 decoded stop bits == 1 (valid framing throughout), clean ASCII result,
  no manual guessing needed.

## Flag
`NCTF{uart_8n1_lsb_first_125k}` — submitted by user, correct.

## Tooling note
Script path: `workspaces/nctf26-uart-capture/artifacts/` holds `capture.csv`.
No reusable standalone decoder script was saved yet — if more UART/logic-analyzer
CSV challenges show up, promote the inline decode (see this session's history)
into `src/tools/forensics/uart_decode.py` (generic 8N1 LSB-first decoder, bit
period auto-detected from the finest inter-edge gap on the data line).
