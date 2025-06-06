#ifndef CHAOTIC_H
#define CHAOTIC_H

#include <cstddef>
#include <cstdint>
#include <vector>

/**
 * Generate a keystream based on the logistic map:
 *   x_{n+1} = r * x_n * (1 - x_n)
 *
 * @param seed   : initial x₀ (0 < seed < 1), e.g. 0.5
 * @param r      : logistic parameter (e.g. 3.9)
 * @param length : number of bytes to generate
 *
 * @return std::vector<uint8_t> of size = length, each element in [0..255]
 */
std::vector<uint8_t> generate_chaotic_keystream(double seed, double r, std::size_t length);

#endif // CHAOTIC_H
