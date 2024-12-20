#!/bin/sh

# Function to install packages in a manylinux environment
install_manylinux() {
    # Install packages using yum
    yum install -y perl-core perl-devel
    # Install cpanminus manually
    curl -L https://cpanmin.us | perl - App::cpanminus
    # Update Perl List::Util module using cpan
    cpanm List::Util
}

# Function to install packages in a musl-linux environment (e.g., Alpine)
install_musllinux() {
    # Install packages using apk
    apk add --no-cache perl perl-dev
    # Configure cpan to be non-interactive
    echo 'o conf init / no' | cpan
    echo 'o conf commit' | cpan
    # Update Perl List::Util module using cpan
    cpan -fi List::Util
}

# Detect the environment: Check for presence of apk or yum
if command -v apk >/dev/null 2>&1; then
    echo "Detected musl-linux environment"
    install_musllinux
elif command -v yum >/dev/null 2>&1; then
    echo "Detected manylinux environment"
    install_manylinux
else
    echo "Unsupported Linux distribution"
    exit 1
fi
