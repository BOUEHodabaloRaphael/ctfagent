#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
flag=${FLAG_PATH:-$root/flag}
vm_timeout=${VM_TIMEOUT:-180}

[[ $vm_timeout =~ ^[1-9][0-9]*$ ]] && ((vm_timeout <= 3600)) || {
	echo "invalid VM_TIMEOUT" >&2
	exit 2
}
[[ -f $flag && -r $flag ]] || {
	echo "flag is not readable" >&2
	exit 1
}

umask 077
work=$(mktemp -d /tmp/spi-tpm-reverse.XXXXXX)
overlay=$work/overlay
runtime_initramfs=$work/initramfs.cpio.gz
cleanup()
{
	case $work in /tmp/spi-tpm-reverse.*) rm -rf -- "$work" ;; esac
}
trap cleanup EXIT
ulimit -c 0

mkdir -p "$overlay"
chmod 0755 "$overlay"
umask 022
install -m 0400 "$flag" "$overlay/flag"
cp -- "$root/initramfs.cpio.gz" "$runtime_initramfs"
(
	cd "$overlay"
	LC_ALL=C find . -print0 | sort -z | \
		cpio --quiet --reproducible --null -o --format=newc --owner=0:0
) | gzip -9n >> "$runtime_initramfs"
rm -rf -- "$overlay"

ulimit -n 64
set +e
timeout --foreground --signal=KILL "${vm_timeout}s" \
	"$root/qemu-system-aarch64" \
	-machine virt,gic-version=3 \
	-cpu cortex-a57 \
	-nodefaults \
	-no-user-config \
	-no-reboot \
	-sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny \
	-device spi-tpm-dma,id=spi0_dma \
	-device spi-tpm-sram,id=spi0_sram,size=8192 \
	-device stm32h7-spi,id=spi0,dma-backend=spi0_dma,sram-backend=spi0_sram,fifo-size=32 \
	-device "spi-tpm,bus=ssi,firmware-path=$root/libspi_tpm_firmware.so" \
	-display none \
	-monitor none \
	-serial stdio \
	-nic none \
	-smp 1 \
	-m 64M \
	-kernel "$root/Image" \
	-initrd "$runtime_initramfs" \
	-append "console=ttyAMA0,115200 rdinit=/init quiet loglevel=0 printk.devkmsg=off panic=-1 spi_stm32.polling_limit_us=0"
status=$?
set -e
exit "$status"
