#!/usr/bin/env bash
set -euo pipefail

connection_timeout=${CONNECTION_TIMEOUT:-180}
pow_timeout=${POW_TIMEOUT:-300}
pow_bits=${POW_BITS:-8}
pow_scrypt_n=${POW_SCRYPT_N:-32768}
pow_bypass=${POW_BYPASS:-0}
runner=${CHALLENGE_RUNNER:-/opt/spi-tpm/run.sh}

[[ $connection_timeout =~ ^[1-9][0-9]*$ ]] &&
	((connection_timeout <= 3600)) || {
	echo "invalid CONNECTION_TIMEOUT" >&2
	exit 2
}
[[ $pow_timeout =~ ^[1-9][0-9]*$ ]] && ((pow_timeout <= 600)) || {
	echo "invalid POW_TIMEOUT" >&2
	exit 2
}
[[ $pow_bits =~ ^[0-9]+$ ]] && ((pow_bits >= 1 && pow_bits <= 12)) || {
	echo "invalid POW_BITS" >&2
	exit 2
}
[[ $pow_scrypt_n =~ ^[0-9]+$ ]] &&
	((pow_scrypt_n >= 1024 && pow_scrypt_n <= 65536 &&
	  (pow_scrypt_n & (pow_scrypt_n - 1)) == 0)) || {
	echo "invalid POW_SCRYPT_N" >&2
	exit 2
}
[[ $pow_bypass == 0 || $pow_bypass == 1 ]] || {
	echo "invalid POW_BYPASS" >&2
	exit 2
}
[[ -x $runner ]] || {
	echo "challenge runner is not executable" >&2
	exit 2
}

if ((pow_bypass == 0)); then
	prefix=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
	printf '%s\n' \
		'proof-of-work scrypt' \
		"prefix $prefix" \
		"n $pow_scrypt_n" \
		'r 8' \
		'p 1' \
		"bits $pow_bits" \
		'find a decimal nonce such that scrypt(prefix || nonce, salt="spi-tpm-pow-v1:" || prefix) has the requested leading zero bits' \
		'nonce'
	if ! IFS= read -r -t "$pow_timeout" -n 21 nonce; then
		echo 'proof-of-work timed out' >&2
		exit 1
	fi
	if [[ ! $nonce =~ ^[0-9]{1,20}$ ]]; then
		echo 'invalid proof-of-work nonce' >&2
		exit 1
	fi
	if ! digest=$(openssl kdf -keylen 32 \
		-kdfopt "pass:$prefix$nonce" \
		-kdfopt "salt:spi-tpm-pow-v1:$prefix" \
		-kdfopt "n:$pow_scrypt_n" \
		-kdfopt r:8 -kdfopt p:1 \
		-kdfopt maxmem_bytes:134217728 SCRYPT 2>/dev/null); then
		echo 'proof-of-work verification failed' >&2
		exit 2
	fi
	digest=${digest//:/}
	[[ $digest =~ ^[[:xdigit:]]{64}$ ]] || {
		echo 'proof-of-work verification failed' >&2
		exit 2
	}
	full_nibbles=$((pow_bits / 4))
	remainder=$((pow_bits % 4))
	zeroes=0000000000000000000000000000000000000000000000000000000000000000
	valid=1
	[[ ${digest:0:full_nibbles} == ${zeroes:0:full_nibbles} ]] || valid=0
	if ((valid && remainder)); then
		nibble=${digest:full_nibbles:1}
		value=$((16#$nibble))
		((value < (1 << (4 - remainder)))) || valid=0
	fi
	if ((valid == 0)); then
		echo 'invalid proof-of-work' >&2
		exit 1
	fi
	echo 'proof-of-work accepted'
fi

exec timeout --signal=TERM --kill-after=1s \
	"${connection_timeout}s" "$runner"
