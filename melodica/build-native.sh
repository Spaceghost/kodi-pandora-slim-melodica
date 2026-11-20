#!/usr/bin/env bash
# Rebuild the portable tuner library using Zig's bundled cross-compilers.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
src=melodica/source
out=plugin.audio.pandoraslim.melodica/resources/lib/native
compile() {
    local target=$1 directory=$2 name=$3
    mkdir -p "$out/$directory"
    "${ZIG:-zig}" cc -target "$target" -shared -fPIC -Os -s -I"$src" "$src/blowfish.c" "$src/wire.c" -o "$out/$directory/$name"
}
compile x86_64-linux-musl linux-x86_64 libwire.so
compile aarch64-linux-musl linux-aarch64 libwire.so
compile x86_64-macos darwin-x86_64 libwire.dylib
compile aarch64-macos darwin-aarch64 libwire.dylib
compile x86_64-windows-gnu windows-x86_64 wire.dll
compile x86-windows-gnu windows-x86 wire.dll
