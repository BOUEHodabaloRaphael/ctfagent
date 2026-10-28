#include <stdio.h>
#include <stdint.h>
volatile uint32_t iv[4]={0x67452301,0xefcdab89,0x98badcfe,0x10325476};
int main(){printf("%x\n",iv[0]);}
