#include "crypto.h"
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>

// A sample 32-byte AES key (for testing only). In real usage, load from a file or generate securely.
static const uint8_t DEMO_KEY[32] = {
    0x60,0x3d,0xeb,0x10,0x15,0xca,0x71,0xbe,
    0x2b,0x73,0xae,0xf0,0x85,0x7d,0x77,0x81,
    0x1f,0x35,0x2c,0x07,0x3b,0x61,0x08,0xd7,
    0x2d,0x98,0x10,0xa3,0x09,0x14,0xdf,0xf4
};

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: Chaotic_cryptology.exe <input_file>\n";
        return 1;
    }

    // 1) Read the entire input file into a buffer
    std::ifstream ifs(argv[1], std::ios::binary);
    if (!ifs) {
        std::cerr << "Error: Unable to open file: " << argv[1] << "\n";
        return 1;
    }
    std::vector<uint8_t> plaintext((std::istreambuf_iterator<char>(ifs)),
                                   std::istreambuf_iterator<char>());
    ifs.close();

    int pt_len = static_cast<int>(plaintext.size());
    if (pt_len <= 0) {
        std::cerr << "Error: Input file is empty\n";
        return 1;
    }

    // 2) Encrypt
    int max_out_len = pt_len + 12 + 16;
    std::vector<uint8_t> enc_buf(max_out_len);
    int enc_len = 0;
    int ret = chaotic_aes_encrypt(
        plaintext.data(), pt_len,
        DEMO_KEY, 32,
        enc_buf.data(), &enc_len
    );
    if (ret != 0) {
        std::cerr << "Error: Encryption failed (code=" << ret << ")\n";
        return 1;
    }
    // Write to "output.enc"
    std::ofstream ofs_enc("output.enc", std::ios::binary);
    ofs_enc.write(reinterpret_cast<char*>(enc_buf.data()), enc_len);
    ofs_enc.close();
    std::cout << "[OK] Wrote encrypted file: output.enc (" << enc_len << " bytes)\n";

    // 3) Decrypt back for verification
    std::vector<uint8_t> dec_buf(pt_len);
    int dec_len = 0;
    ret = chaotic_aes_decrypt(
        enc_buf.data(), enc_len,
        DEMO_KEY, 32,
        dec_buf.data(), &dec_len
    );
    if (ret != 0) {
        std::cerr << "Error: Decryption failed (code=" << ret << ")\n";
        return 1;
    }
    // Write decrypted output to "output.dec.bin"
    std::ofstream ofs_dec("output.dec.bin", std::ios::binary);
    ofs_dec.write(reinterpret_cast<char*>(dec_buf.data()), dec_len);
    ofs_dec.close();
    std::cout << "[OK] Wrote decrypted file: output.dec.bin (" << dec_len << " bytes)\n";

    return 0;
}
