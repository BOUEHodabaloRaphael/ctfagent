#include <stdio.h>
/* Benign stand-in: carries typical malware indicators as data only. */
static const char *c2[] = {"http://185.220.101.45/gate.php", "https://evil-update.example.net/payload.bin",
  "admin@evil-update.example.net"};
static const char *persist = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater";
static const char *drop = "C:\\Users\\Public\\svchost32.exe";
/* "config" XOR-ed with 0x5a: http://10.13.37.1/c2 */
static const unsigned char cfg[] = {0x32,0x2e,0x2e,0x2a,0x60,0x75,0x75,0x6b,0x6a,0x74,0x6b,0x69,0x74,0x69,0x6d,0x74,0x6b,0x75,0x39,0x68};
int main(){ puts(c2[0]); puts(persist); puts(drop); return cfg[0]; }
