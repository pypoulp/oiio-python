#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Function to install packages in a manylinux environment
install_manylinux() {
    echo "Detected manylinux environment"
    # Install packages using yum
    # Perl required to build OpenSSL
    yum install -y perl-core perl-devel libatomic devtoolset-10-libatomic-devel
    # Install cpanminus manually
    curl -L https://cpanmin.us | perl - App::cpanminus
    # Update Perl List::Util module using cpan
    cpanm List::Util
}

# Function to install packages in a musl-linux environment (e.g., Alpine)
install_musllinux() {
    echo "Detected musl-linux environment"
    # Install packages using apk
    apk add --no-cache perl perl-dev 
    # Configure cpan to be non-interactive
    echo 'o conf init / no' | cpan
    echo 'o conf commit' | cpan
    # Update Perl List::Util module using cpan
    cpan -fi List::Util
    # Add libatomic
    apk add --no-cache libatomic libatomic_ops-dev libatomic_ops-static
}

# Detect the environment: Check for presence of apk or yum
if command -v apk >/dev/null 2>&1; then
    install_musllinux
elif command -v yum >/dev/null 2>&1; then
    install_manylinux
else
    echo "Unsupported Linux distribution"
    exit 1
fi
