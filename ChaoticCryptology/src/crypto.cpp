#include "crypto.h"
#include "chaotic.h"

#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>

#include <vector>
#include <cstring>
#include <iostream>

static constexpr int AES_KEY_LEN = 32;     // 256 bits
static constexpr int AES_GCM_IV_LEN = 12;  // 96 bits nonce
static constexpr int AES_GCM_TAG_LEN = 16; // 128 bits tag

static void print_openssl_errors() {
    unsigned long errCode;
    while ((errCode = ERR_get_error()) != 0) {
        char* errStr = ERR_error_string(errCode, NULL);
        std::cerr << "[OpenSSL ERR] " << errStr << std::endl;
    }
}

int chaotic_aes_encrypt(
    const uint8_t* plaintext,
    int plaintext_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_buffer,
    int* out_len
) {
    if (key_len != AES_KEY_LEN) return -1;
    if (plaintext_len <= 0) return -2;

    // 1) Sinh keystream chaotic
    const double SEED = 0.5;
    const double R = 3.9;
    std::vector<uint8_t> keystream = generate_chaotic_keystream(SEED, R, (std::size_t)plaintext_len);

    // 2) XOR plaintext <-> keystream
    std::vector<uint8_t> pre_aes(plaintext_len);
    for (int i = 0; i < plaintext_len; ++i) {
        pre_aes[i] = plaintext[i] ^ keystream[i];
    }

    // 3) Tạo nonce (IV) ngẫu nhiên 12 bytes
    std::vector<uint8_t> iv(AES_GCM_IV_LEN);
    if (1 != RAND_bytes(iv.data(), AES_GCM_IV_LEN)) {
        print_openssl_errors();
        return -3;
    }

    // 4) Chuẩn bị AES-GCM encrypt
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        print_openssl_errors();
        return -4;
    }

    int len = 0;
    int ciphertext_len = 0;
    std::vector<uint8_t> ciphertext_buf(plaintext_len);

    if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -5;
    }
    if (1 != EVP_EncryptInit_ex(ctx, nullptr, nullptr, aes_key, iv.data())) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -6;
    }

    if (1 != EVP_EncryptUpdate(ctx,
                               ciphertext_buf.data(),
                               &len,
                               pre_aes.data(),
                               plaintext_len)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -7;
    }
    ciphertext_len = len;

    if (1 != EVP_EncryptFinal_ex(ctx, ciphertext_buf.data() + len, &len)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -8;
    }
    ciphertext_len += len;

    std::vector<uint8_t> tag(AES_GCM_TAG_LEN);
    if (1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_LEN, tag.data())) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -9;
    }
    EVP_CIPHER_CTX_free(ctx);

    // 5) Gộp [nonce||tag||ciphertext] vào out_buffer
    int total_len = AES_GCM_IV_LEN + AES_GCM_TAG_LEN + ciphertext_len;
    std::memcpy(out_buffer, iv.data(), AES_GCM_IV_LEN);
    std::memcpy(out_buffer + AES_GCM_IV_LEN, tag.data(), AES_GCM_TAG_LEN);
    std::memcpy(out_buffer + AES_GCM_IV_LEN + AES_GCM_TAG_LEN,
                ciphertext_buf.data(), ciphertext_len);

    *out_len = total_len;
    return 0;
}

int chaotic_aes_decrypt(
    const uint8_t* in_buffer,
    int in_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_plaintext,
    int* out_plaintext_len
) {
    if (key_len != AES_KEY_LEN) return -1;
    if (in_len < (AES_GCM_IV_LEN + AES_GCM_TAG_LEN + 1)) return -2;

    const uint8_t* iv = in_buffer;
    const uint8_t* tag = in_buffer + AES_GCM_IV_LEN;
    const uint8_t* ciphertext = in_buffer + AES_GCM_IV_LEN + AES_GCM_TAG_LEN;
    int ciphertext_len = in_len - AES_GCM_IV_LEN - AES_GCM_TAG_LEN;

    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        print_openssl_errors();
        return -3;
    }

    if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -4;
    }
    if (1 != EVP_DecryptInit_ex(ctx, nullptr, nullptr, aes_key, iv)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -5;
    }

    int len = 0;
    std::vector<uint8_t> pre_aes(ciphertext_len);
    if (1 != EVP_DecryptUpdate(ctx,
                               pre_aes.data(),
                               &len,
                               ciphertext,
                               ciphertext_len)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -6;
    }
    int plain_len = len;

    if (1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_LEN, (void*)tag)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -7;
    }
    if (1 != EVP_DecryptFinal_ex(ctx, pre_aes.data() + len, &len)) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -8;
    }
    plain_len += len;
    EVP_CIPHER_CTX_free(ctx);

    const double SEED = 0.5;
    const double R = 3.9;
    std::vector<uint8_t> keystream = generate_chaotic_keystream(SEED, R, (std::size_t)plain_len);

    for (int i = 0; i < plain_len; ++i) {
        out_plaintext[i] = pre_aes[i] ^ keystream[i];
    }
    *out_plaintext_len = plain_len;
    return 0;
}
