#include <stdio.h>
#include <stdint.h>
volatile uint32_t iv[5]={0x67452301,0xefcdab89,0x98badcfe,0x10325476,0xc3d2e1f0};
int main(){printf("%x\n",iv[0]);}
