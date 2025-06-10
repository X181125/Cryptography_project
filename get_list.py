from scapy.all import get_windows_if_list

print("[Attacker] Danh sách interface đầy đủ:")
for iface in get_windows_if_list():
    print(f"- Name: {iface['name']}")
    print(f"  Description: {iface['description']}")
    print(f"  Win Name: {iface['win_name']}")
    print()
