#ifndef CRYPTO_H
#define CRYPTO_H

#include <cstddef>
#include <cstdint>

#ifdef _WIN32
  // Khi build DLL trên Windows, đánh dấu __declspec(dllexport)
  #define EXPORT extern "C" __declspec(dllexport)
#else
  #define EXPORT extern "C"
#endif

/**
 * Perform Chaotic-XOR + AES-GCM encryption.
 *
 * @param plaintext      : pointer to the input plaintext buffer
 * @param plaintext_len  : length of the plaintext in bytes
 * @param aes_key        : pointer to the AES-256 key (must be exactly 32 bytes)
 * @param key_len        : length of aes_key (must be 32)
 * @param out_buffer     : caller-allocated buffer (size >= plaintext_len + 12 + 16)
 *                         to receive: [nonce(12) || tag(16) || ciphertext]
 * @param out_len        : on output, *out_len = total bytes written into out_buffer
 *
 * @return 0 on success; non-zero on error (e.g. key_len != 32, OpenSSL failure…)
 */
EXPORT int chaotic_aes_encrypt(
    const uint8_t* plaintext,
    int plaintext_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_buffer,
    int* out_len
);

/**
 * Perform Chaotic-XOR + AES-GCM decryption.
 *
 * @param in_buffer          : pointer to buffer containing [nonce||tag||ciphertext]
 * @param in_len             : length of in_buffer (>= 12+16+1)
 * @param aes_key            : pointer to AES-256 key (must be exactly 32 bytes)
 * @param key_len            : length of aes_key (must be 32)
 * @param out_plaintext      : caller-allocated buffer (size >= in_len - 12 - 16)
 *                            to receive the plaintext
 * @param out_plaintext_len  : on output, *out_plaintext_len = number of plaintext bytes
 *
 * @return 0 on success; non-zero on error (e.g. GCM tag mismatch…)
 */
EXPORT int chaotic_aes_decrypt(
    const uint8_t* in_buffer,
    int in_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_plaintext,
    int* out_plaintext_len
);

#endif // CRYPTO_H
