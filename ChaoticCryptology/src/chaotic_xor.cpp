#include <cstdint>
#include <cstddef>
#include <cmath>
#include <cstdlib>

extern "C" {

  // Sinh keystream Chaotic
  uint8_t* generate_chaotic_keystream(double seed, double r, int length) {
    double x = seed;
    uint8_t* buf = (uint8_t*)malloc(length);
    for (int i = 0; i < length; ++i) {
      x = r * x * (1.0 - x);
      buf[i] = uint8_t(floor(x * 256.0)) & 0xFF;
    }
    return buf;
  }

  // Giải phóng bộ nhớ
  void free_buffer(uint8_t* p) {
    free(p);
  }

}
