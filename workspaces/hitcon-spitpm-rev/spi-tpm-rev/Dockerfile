FROM archlinux:base-devel-20261004.0.606936@sha256:996c3a1d6b0d87b01242f6fcd8cfa3ad3eece1a67ab5c8f108e20af1d7b97bdd

RUN sed -i \
	's%^Include = /etc/pacman.d/mirrorlist$%SigLevel = Never\nServer = https://archive.archlinux.org/repos/2026/10/04/$repo/os/$arch%' \
	/etc/pacman.conf \
	&& pacman -Syu --noconfirm --needed \
		cpio dtc openssl socat \
	&& pacman -Scc --noconfirm \
	&& useradd --uid 1000 --create-home --shell /usr/bin/nologin spi-tpm

USER spi-tpm
WORKDIR /opt/spi-tpm

EXPOSE 1337

CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork,backlog=4096", "EXEC:/opt/spi-tpm/connection.sh,stderr"]
