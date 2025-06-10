// ChaoticCryptology.cpp
//
// Single-file implementation of Chaotic-XOR + AES-256-GCM, exporting two C APIs.
// Compile with:
//   cl.exe /EHsc /std:c++17 /LD ChaoticCryptology.cpp /link \
//          /OUT:Chaotic_Cryptology.dll /IMPLIB:Chaotic_Cryptology.lib \
//          /LIBPATH:path\\to\\openssl\\lib libcrypto.lib libssl.lib

#include <cstddef>
#include <cstdint>
#include <vector>
#include <cmath>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <fstream>
#include <iostream>
#include <cstring>

#ifdef _WIN32
  #define DLL_EXPORT extern "C" __declspec(dllexport)
#else
  #define DLL_EXPORT extern "C"
#endif

static constexpr int AES_KEY_LEN      = 32;  // 256 bits
static constexpr int AES_GCM_IV_LEN   = 12;  // 96 bits nonce
static constexpr int AES_GCM_TAG_LEN  = 16;  // 128 bits tag

// Demo key for standalone testing in main(); real usage should load/generate securely.
static const uint8_t DEMO_KEY[AES_KEY_LEN] = {
    0x60,0x3d,0xeb,0x10,0x15,0xca,0x71,0xbe,
    0x2b,0x73,0xae,0xf0,0x85,0x7d,0x77,0x81,
    0x1f,0x35,0x2c,0x07,0x3b,0x61,0x08,0xd7,
    0x2d,0x98,0x10,0xa3,0x09,0x14,0xdf,0xf4
};

static void print_openssl_errors() {
    unsigned long err;
    while ((err = ERR_get_error()) != 0) {
        char buf[256];
        ERR_error_string_n(err, buf, sizeof(buf));
        std::cerr << "[OpenSSL ERR] " << buf << std::endl;
    }
}

/**
 * Generate a keystream based on the logistic map:
 *   x_{n+1} = r * x_n * (1 - x_n)
 */
static std::vector<uint8_t> generate_chaotic_keystream(double seed, double r, std::size_t length) {
    std::vector<uint8_t> ks;
    ks.reserve(length);
    double x = seed;
    for (std::size_t i = 0; i < length; ++i) {
        x = r * x * (1.0 - x);
        uint8_t b = static_cast<uint8_t>(std::floor(x * 256.0)) & 0xFF;
        ks.push_back(b);
    }
    return ks;
}

/**
 * Exported: Chaotic-XOR + AES-256-GCM encryption.
 *
 * out_buf must be at least plaintext_len + 12 + 16 bytes.
 * Returns 0 on success, non-zero on error.
 */
DLL_EXPORT
int chaotic_aes_encrypt(
    const uint8_t* plaintext,
    int plaintext_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_buf,
    int* out_len
) {
    if (key_len != AES_KEY_LEN)      return -1;
    if (plaintext_len <= 0)          return -2;

    // 1) Chaotic XOR
    const double SEED = 0.5, R = 3.9;
    auto ks = generate_chaotic_keystream(SEED, R, plaintext_len);
    std::vector<uint8_t> pre_aes(plaintext_len);
    for (int i = 0; i < plaintext_len; ++i)
        pre_aes[i] = plaintext[i] ^ ks[i];

    // 2) Random IV
    std::vector<uint8_t> iv(AES_GCM_IV_LEN);
    if (RAND_bytes(iv.data(), AES_GCM_IV_LEN) != 1) {
        print_openssl_errors();
        return -3;
    }

    // 3) AES-GCM encrypt
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { print_openssl_errors(); return -4; }
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1 ||
        EVP_EncryptInit_ex(ctx, nullptr, nullptr, aes_key, iv.data()) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -5;
    }

    int len = 0, cipher_len = 0;
    std::vector<uint8_t> cipherbuf(plaintext_len);
    if (EVP_EncryptUpdate(ctx, cipherbuf.data(), &len, pre_aes.data(), plaintext_len) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -6;
    }
    cipher_len = len;
    if (EVP_EncryptFinal_ex(ctx, cipherbuf.data() + len, &len) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -7;
    }
    cipher_len += len;

    std::vector<uint8_t> tag(AES_GCM_TAG_LEN);
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_LEN, tag.data()) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -8;
    }
    EVP_CIPHER_CTX_free(ctx);

    // 4) Output [IV||TAG||CIPHERTEXT]
    int total = AES_GCM_IV_LEN + AES_GCM_TAG_LEN + cipher_len;
    std::memcpy(out_buf,               iv.data(),       AES_GCM_IV_LEN);
    std::memcpy(out_buf + AES_GCM_IV_LEN, tag.data(),   AES_GCM_TAG_LEN);
    std::memcpy(out_buf + AES_GCM_IV_LEN + AES_GCM_TAG_LEN,
                cipherbuf.data(), cipher_len);

    *out_len = total;
    return 0;
}

/**
 * Exported: Chaotic-XOR + AES-256-GCM decryption.
 * Returns 0 on success, non-zero on error.
 */
DLL_EXPORT
int chaotic_aes_decrypt(
    const uint8_t* in_buf,
    int in_len,
    const uint8_t* aes_key,
    int key_len,
    uint8_t* out_plain,
    int* out_plain_len
) {
    if (key_len != AES_KEY_LEN) return -1;
    if (in_len < AES_GCM_IV_LEN + AES_GCM_TAG_LEN + 1) return -2;

    const uint8_t* iv         = in_buf;
    const uint8_t* tag        = in_buf + AES_GCM_IV_LEN;
    const uint8_t* ciphertext = in_buf + AES_GCM_IV_LEN + AES_GCM_TAG_LEN;
    int cipher_len = in_len - AES_GCM_IV_LEN - AES_GCM_TAG_LEN;

    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { print_openssl_errors(); return -3; }
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1 ||
        EVP_DecryptInit_ex(ctx, nullptr, nullptr, aes_key, iv) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -4;
    }

    int len = 0, plain_len = 0;
    std::vector<uint8_t> pre_aes(cipher_len);
    if (EVP_DecryptUpdate(ctx, pre_aes.data(), &len, ciphertext, cipher_len) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -5;
    }
    plain_len = len;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_LEN, (void*)tag) != 1 ||
        EVP_DecryptFinal_ex(ctx, pre_aes.data() + len, &len) != 1) {
        print_openssl_errors();
        EVP_CIPHER_CTX_free(ctx);
        return -6;
    }
    plain_len += len;
    EVP_CIPHER_CTX_free(ctx);

    // Chaotic XOR recovery
    const double SEED = 0.5, R = 3.9;
    auto ks = generate_chaotic_keystream(SEED, R, plain_len);
    for (int i = 0; i < plain_len; ++i)
        out_plain[i] = pre_aes[i] ^ ks[i];

    *out_plain_len = plain_len;
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file>\n";
        return 1;
    }
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();

    // Read input file
    std::ifstream ifs(argv[1], std::ios::binary);
    if (!ifs) { std::cerr << "Error opening " << argv[1] << "\n"; return 1; }
    std::vector<uint8_t> plaintext((std::istreambuf_iterator<char>(ifs)),
                                   std::istreambuf_iterator<char>());
    ifs.close();
    int pt_len = static_cast<int>(plaintext.size());
    if (pt_len <= 0) { std::cerr << "Empty input\n"; return 1; }

    // Encrypt
    std::vector<uint8_t> enc_buf(pt_len + AES_GCM_IV_LEN + AES_GCM_TAG_LEN);
    int enc_len = 0;
    if (chaotic_aes_encrypt(plaintext.data(), pt_len,
                            DEMO_KEY, AES_KEY_LEN,
                            enc_buf.data(), &enc_len) != 0) {
        std::cerr << "Encryption error\n"; return 1;
    }
    std::ofstream ofs_enc("output.enc", std::ios::binary);
    ofs_enc.write(reinterpret_cast<char*>(enc_buf.data()), enc_len);
    ofs_enc.close();
    std::cout << "[OK] Encrypted to output.enc (" << enc_len << " bytes)\n";

    // Decrypt for verification
    std::vector<uint8_t> dec_buf(pt_len);
    int dec_len = 0;
    if (chaotic_aes_decrypt(enc_buf.data(), enc_len,
                            DEMO_KEY, AES_KEY_LEN,
                            dec_buf.data(), &dec_len) != 0) {
        std::cerr << "Decryption error\n"; return 1;
    }
    std::ofstream ofs_dec("output.dec.bin", std::ios::binary);
    ofs_dec.write(reinterpret_cast<char*>(dec_buf.data()), dec_len);
    ofs_dec.close();
    std::cout << "[OK] Decrypted to output.dec.bin (" << dec_len << " bytes)\n";

    EVP_cleanup();
    ERR_free_strings();
    return 0;
}
