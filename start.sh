#! /bin/sh
[ -n "$BERBALANG_LOG" ] || BERBALANG_LOG=info
export BERBALANG_LOG

[ -n "$BUILD" ] || BUILD="--release"

if [ -f "./berbalang" ]; then
  # only makes sense inside of docker
  ./berbalang $*
else
  export RUST_BACKTRACE=1
  export RUSTFLAGS="--emit=asm"
  ./target/release/berbalang $*
fi
