from scapy.all import sniff, TCP, Raw

def packet_callback(pkt):
    if pkt.haslayer(TCP) and pkt.haslayer(Raw):
        payload = pkt[Raw].load
        print(f"[!] Intercepted {len(payload)} bytes: {payload[:20].hex()}...")

print("[*] Sniffing packets on port 8000...")
sniff(filter="tcp port 8000", prn=packet_callback, store=False)
