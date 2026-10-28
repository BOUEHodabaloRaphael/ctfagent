#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
flag=${FLAG_PATH:-$root/flag}
vm_timeout=${VM_TIMEOUT:-180}
upload_timeout=${UPLOAD_TIMEOUT:-30}
max_payload_bytes=$((16 * 1024 * 1024))

[[ $vm_timeout =~ ^[1-9][0-9]*$ ]] && ((vm_timeout <= 3600)) || {
	echo "invalid VM_TIMEOUT" >&2
	exit 2
}
[[ $upload_timeout =~ ^[1-9][0-9]*$ ]] && ((upload_timeout <= 300)) || {
	echo "invalid UPLOAD_TIMEOUT" >&2
	exit 2
}
[[ -f $flag && -r $flag ]] || {
	echo "flag is not readable" >&2
	exit 1
}

umask 077
work=$(mktemp -d /tmp/spi-tpm-run.XXXXXX)
overlay=$work/overlay
runtime_initramfs=$work/initramfs.cpio.gz
payload_file=$work/payload

cleanup()
{
	case $work in
	/tmp/spi-tpm-run.*) rm -rf -- "$work" ;;
	esac
}
trap cleanup EXIT

ulimit -c 0

printf 'Base64 payload (single line, empty to skip, max 16 MiB):\n'
payload_status=0
(
	set -o pipefail
	timeout --foreground --signal=KILL "${upload_timeout}s" head -n 1 |
		(
			ulimit -f "$((max_payload_bytes / 1024))"
			trap '' XFSZ
			base64 --decode > "$payload_file" 2>/dev/null
		)
) || payload_status=$?
if ((payload_status != 0)); then
	echo "payload is invalid, exceeds 16 MiB, or timed out" >&2
	exit 1
fi
payload_size=$(stat -c %s -- "$payload_file")
if ((payload_size > 0)); then
	printf 'Accepted %s-byte payload as ~/payload.\n' "$payload_size"
else
	rm -f -- "$payload_file"
	echo 'No payload supplied.'
fi

mkdir -p "$overlay"
chmod 0755 "$overlay"
umask 022
install -m 0400 "$flag" "$overlay/flag"
if [[ -f $payload_file ]]; then
	install -d -m 0755 "$overlay/home/spi-tpm"
	mv -- "$payload_file" "$overlay/home/spi-tpm/payload"
	chmod 0555 "$overlay/home/spi-tpm/payload"
fi

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
	-smp 2 \
	-m 64M \
	-kernel "$root/Image" \
	-initrd "$runtime_initramfs" \
	-append "console=ttyAMA0,115200 rdinit=/init quiet loglevel=0 printk.devkmsg=off panic=-1 spi_stm32.polling_limit_us=0"
status=$?
set -e
exit "$status"
