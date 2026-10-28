#include <stdio.h>
int main(){unsigned char S[256],k[]="secret";for(int i=0;i<256;i++)S[i]=i;int j=0;for(int i=0;i<256;i++){j=(j+S[i]+k[i%6])&255;unsigned char t=S[i];S[i]=S[j];S[j]=t;}
unsigned char d[]="hello";int a=0,b=0;for(int n=0;n<5;n++){a=(a+1)&255;b=(b+S[a])&255;unsigned char t=S[a];S[a]=S[b];S[b]=t;d[n]^=S[(S[a]+S[b])&255];}printf("%02x\n",d[0]);}
