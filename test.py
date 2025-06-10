with open("static/encrypted_segments/sample1.enc", "rb") as f:
    data = f.read()
    iv, tag, ct = data[:12], data[12:28], data[28:]
    print("IV:", iv.hex())
    print("TAG:", tag.hex())
    print("Ciphertext length:", len(ct))
