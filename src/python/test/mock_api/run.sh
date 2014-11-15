#!/bin/bash

set -e

./api.py --port $1 > /dev/null 2>&1 &
MOCK_SERVER_PID=$!

cleanup() {
    kill $MOCK_SERVER_PID
}

trap cleanup EXIT

export DX_APISERVER_PROTOCOL=http
export DX_APISERVER_HOST=localhost
export DX_APISERVER_PORT=$((5000+$1))
#export _DX_DEBUG=1

for i in {1..1024}; do
    wire_md5=$(dx download test --output - 2>/dev/null | md5sum | cut -f 1 -d " ")
    desc_md5=$(dx api file-test describe | jq --raw-output .md5)
    echo $i $wire_md5 $desc_md5
    if ! [[ $wire_md5 == $desc_md5 ]]; then
        exit 1
    fi
done
