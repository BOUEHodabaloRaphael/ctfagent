#include <stdio.h>
#include <stdint.h>
void enc(uint32_t v[2],const uint32_t k[4]){uint32_t a=v[0],b=v[1],s=0;for(int i=0;i<32;i++){s+=0x9e3779b9;a+=((b<<4)+k[0])^(b+s)^((b>>5)+k[1]);b+=((a<<4)+k[2])^(a+s)^((a>>5)+k[3]);}v[0]=a;v[1]=b;}
int main(){uint32_t v[2]={1,2},k[4]={1,2,3,4};enc(v,k);printf("%x %x\n",v[0],v[1]);}
