#include <stdio.h>
#include <string.h>
int check(const char*s){return strcmp(s,"hunter2")==0;}
int main(int c,char**v){char b[64]; if(c>1&&check(v[1])){puts("Correct password!");return 0;} puts("Wrong password");return 1;}
