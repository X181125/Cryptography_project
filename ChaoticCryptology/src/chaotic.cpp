#include "chaotic.h"
#include <cmath>

/*
 * Generate a keystream based on the logistic map:
 *   x_{n+1} = r * x_n * (1 - x_n)
 * Each iteration, compute byte = floor(x * 256) & 0xFF.
 */
std::vector<uint8_t> generate_chaotic_keystream(double seed, double r, std::size_t length) {
    std::vector<uint8_t> keystream;
    keystream.reserve(length);

    double x = seed;
    for (std::size_t i = 0; i < length; ++i) {
        x = r * x * (1.0 - x);
        uint8_t byte = static_cast<uint8_t>(std::floor(x * 256.0)) & 0xFF;
        keystream.push_back(byte);
    }
    return keystream;
}
