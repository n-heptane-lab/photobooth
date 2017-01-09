with import <nixpkgs> {}; stdenv.mkDerivation {
 name = "foo";
 buildInputs = [ python3 raspberrypi-userland pymqtt picamera pillow ];
 LD_LIBRARY_PATH="${raspberrypi-userland}/lib";
}