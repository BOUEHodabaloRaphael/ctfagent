#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
static uint8_t *f;
static uint32_t s;
static uint32_t rg(){ s=s*0x41c64e6du+0x8042au; return s%0xFFFFFFu; }
// asm: x - (((x*0x101 hi)... ) approximates x mod (2^24-1)
static uint32_t rg2(){ s=s*0x41c64e6du+0x8042au; uint32_t x=s; uint32_t t=(uint32_t)(((uint64_t)0x101*x)>>32); t=t+((x-t)>>1); t>>=23; return x-((t<<24)-t);}
int main(int c,char**v){
 FILE*fp=fopen(v[1],"rb"); f=malloc(1<<24); fread(f,1,1<<24,fp);
 for(uint32_t seed=0;seed<100000000u;seed++){
  s=seed; char out[50]; int ok=1;
  for(int i=0;i<49;i++){ uint32_t a=(rg2()&0xff0000)+(rg2()&0xff00)+(rg2()&0xff); out[i]=f[a&0xffffff]; if(i==3){ if(!(out[0]=='H'&&out[1]=='T'&&out[2]=='B'&&out[3]=='{')){ok=0;break;} } }
  if(ok){out[49]=0;printf("%u %s\n",seed,out);}
 }
}
