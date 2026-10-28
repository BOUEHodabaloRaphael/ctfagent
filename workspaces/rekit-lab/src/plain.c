#include <stdio.h>
#include <string.h>
int main(){char in[64];scanf("%63s",in);if(!strcmp(in,"CTF{plain_strcmp_flag}"))puts("ok");else puts("no");}
