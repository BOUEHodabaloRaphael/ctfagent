# Secret Treasures (HTB Hardware, Medium)
Flag: HTB{m3M0ry_5cR4Mbl1Ng_4nd_1CG_423_n07_3n0u9h7!$#}  (seed 73261522)
Files: challenge.zip (pw `hackthebox`) -> files/hw_secret/{embedded_software,flash_memory_dump.bin,input_channel_trace.sal}
Solver: bruteforce_seed.c (gcc -O2; ./bf flash_memory_dump.bin)
