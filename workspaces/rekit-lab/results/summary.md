| check | correct behaviour | result |
|---|---|---|
| strings-flag | finds a plaintext flag | PASS |
| wide-flag | finds a UTF-16 flag | PASS |
| packer-upx | detects UPX | PASS |
| packer-fp | does not call an unpacked binary UPX | **FAIL** |
| unpack-upx | unpacks UPX | PASS |
| rc4-tp | flags RC4 on an RC4 binary | PASS |
| rc4-fp-plain | does not flag RC4 on a strcmp binary | **FAIL** |
| rc4-fp-tea | does not flag RC4 on a TEA binary | **FAIL** |
| tea | detects TEA (delta 0x9e3779b9, stored as sub 0x61c88647) | **FAIL** |
| md5-only | MD5 IV alone is not reported as SHA1 | **FAIL** |
| md5-tp | reports MD5 | PASS |
| sha1-only | SHA1 IV is not reported as MD5 too | **FAIL** |
| md5-be | finds big-endian byte-array constants | **FAIL** |
| canary-only: canary | canary detected | PASS |
| canary-only: fortify | Fortify must be No when only a canary is present | **FAIL** |
| fortify-only: fortify | Fortify detected (__strcpy_chk) | PASS |
| fortify-only: canary | no canary | PASS |
| nx-off | executable stack reported as NX off | PASS |
| no-pie | -no-pie reported as PIE off | PASS |
| full-relro | Full RELRO | PASS |
| cap-covers-main | -cap output contains main (0x1159) | **FAIL** |
| patch-lists-jump | -patch lists the jump at 0x1194 | PASS |
| invert-jump | wrong password granted, right one denied | PASS |
| nop-out | nopped jump changes behaviour | PASS |
