#!/bin/sh
# Build the lab samples into work/. Run from workspaces/rekit-lab/.
set -e
W=work; S=src
cc() { gcc "$@" 2>&1 | grep -iE "error" || true; }
cc -O0 -o $W/plain          $S/plain.c
cc -O1 -o $W/xor_inline     $S/xor_inline.c
cc -O0 -o $W/xor_const      $S/xor_const.c
cc -O1 -o $W/tea            $S/tea.c
cc -O0 -o $W/rc4            $S/rc4.c
cc -O0 -o $W/md5only        $S/md5only.c
cc -O0 -o $W/sha1only       $S/sha1only.c
cc -O0 -o $W/md5_be         $S/md5_be.c
cc -O0 -fstack-protector-all -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -o $W/canary_only $S/canary.c
cc -O2 -fno-stack-protector -D_FORTIFY_SOURCE=2 -o $W/fortify_only $S/fortify.c
cc -O0 -fno-stack-protector -z execstack -o $W/nx_off $S/canary.c
cc -O0 -no-pie -Wl,-z,relro,-z,now -o $W/nopie_fullrelro $S/canary.c
cc -O0 -o $W/wide           $S/wide.c
cc -O0 -o $W/upxfake        $S/upxfake.c
cc -O0 -o $W/crackme        $S/crackme.c
cp $W/plain $W/plain_upx && upx -q $W/plain_upx >/dev/null 2>&1 || true
cp $W/plain $W/plain_stripped && strip $W/plain_stripped
echo "built: $(ls $W | wc -l) samples"
