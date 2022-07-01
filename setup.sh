#!/bin/bash
error() {
    echo $1 >&2
    exit 1
}
log() {
    echo "${GREEN}setup: ${1}${NC}"
}
test_in_virtualenv() {
    python <<EOF
import sys
if sys.prefix != sys.base_prefix:
    # virtualenv activated
    sys.exit(0)
else:
    sys.exit(1)
EOF
}
GREEN='\033[0;32m'
NC='\033[0m'

which virtualenv >/dev/null || ( error "error: could not find virtualenv; install it using pip:\n\tpip install virtualenv" )
which python >/dev/null || ( error "error: could not find python" )

if [ ! -f ./bin/activate ]; then
    log "creating virtualenv"
    virtualenv .
else
    log "virtualenv already created"
fi

test_in_virtualenv
if [ $? -eq 1 ]; then
    log "activating virtualenv"
    source ./bin/activate
else
    log "virtualenv already activated"
fi

log "installing/upgrading packages"
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
