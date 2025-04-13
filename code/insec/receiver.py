from scapy.layers.inet import IP, IPOption_LSRR, UDP
from scapy.sendrecv import sniff

def decode_ips_to_message(ip_list):
    chars = []
    for ip in ip_list:
        octets = [int(x) for x in ip.split('.')]
        chars += [chr(o) for o in octets if o != 0]
    return ''.join(chars)

def extract_lsrr(pkt):
    ip_layer = pkt[IP]
    
    for opt in ip_layer.options:
        if isinstance(opt, IPOption_LSRR):
            ip_data = opt.routers
            return ip_data
    return []

def recv_callback(pkt):
    if IP in pkt and UDP in pkt:
        visible = pkt[UDP].payload.load.decode() if pkt[UDP].payload else ''

        src_ip = pkt[IP].src
        src_port = pkt[UDP].sport

        visible = pkt[UDP].payload.load.decode() if pkt[UDP].payload else ''
        ip_list = extract_lsrr(pkt)
        covert = decode_ips_to_message(ip_list)

        print(f"From {src_ip}:{src_port} came:")
        print(f"    Visible Message: '{visible}'")
        print(f"    Covert Message: '{covert}'")
    
if __name__ == "__main__":
    print("Receiver running on port 8888...")
    sniff(filter="udp", iface="eth0", prn=recv_callback, store=0)