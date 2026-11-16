#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int c,char**v){char b[64];strcpy(b,v[1]);fgets(b,64,stdin);system(b);printf(b);return 0;}
