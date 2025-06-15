import os
import sys
import time
import struct
import random
import string
import datetime

import numpy as np
import scipy.stats

from scapy.layers.inet import IP, IPOption, UDP
from scapy.sendrecv import send

# Max amount of CHARS the LSRR can take without breaking the packets
MAX_CHARS = 36

def encode_message_to_ips(message: str):
    """
    Convert a message string into a list of fake IP addresses by encoding
    4 characters (32 bits) at a time.
    """
    # Pad message to a multiple of 4 bytes
    padded = message.ljust((len(message) + 3) // 4 * 4, '\x00')
    ips = []

    for i in range(0, len(padded), 4):
        chunk = padded[i:i+4]
        ip_parts = struct.unpack("BBBB", chunk.encode())
        ip_str = ".".join(map(str, ip_parts))
        ips.append(ip_str)

    return ips

def split_into_chunks(msg: str):
    return [msg[i:i + MAX_CHARS] for i in range(0, len(msg), MAX_CHARS)]

def send_covert_packet(dst_ip: str, dst_port: str, covert_msg: str, is_covert=True, msg_id=0, msg_len=12):
    visible_msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    encoded_ips = encode_message_to_ips(covert_msg)

    # LSRR option: type=131 (0x83), length=3 + 4*number_of_ips, pointer=4 (start at first IP)
    option_data = struct.pack("!BBB", 131, 3 + 4*len(encoded_ips), 4)
    for ip in encoded_ips:
        option_data += struct.pack("!4B", *[int(octet) for octet in ip.split('.')])

    lsrr_option = IPOption(option_data)

    # Construct the packet
    pkt = IP(dst=dst_ip, options=[lsrr_option])/UDP(dport=dst_port)/(("is_covert_" if is_covert else "is_visible_") + f"{msg_id}_{msg_len}_" + visible_msg) 
    send(pkt)
    print(f"Covert message sent to {dst_ip}:{dst_port} with LSRR-encoded data.")
    print(f"  Covert message: '{covert_msg}'")

def send_large_covert_message(dst_ip, dst_port, full_covert_msg, is_covert=True, msg_id=0, msg_len=12):
    chunks = split_into_chunks(full_covert_msg)

    for covert_chunk in chunks:
        send_covert_packet(dst_ip, dst_port, covert_chunk, is_covert=is_covert, msg_id=msg_id, msg_len=msg_len)
        time.sleep(0.1)  # slight delay between packets

def run_experiment_phase3(dst_ip, dst_port, msg_len=12, delay=0.1, is_covert=True, msg_id=0):
    """
    Run a single experiment phase to send a covert message of specified length
    and measure the time taken.
    """
    with open('dummy_text.txt', 'r') as f:
        dummy_text = f.read().strip()

    if is_covert:
        rand_start = random.randint(0, len(dummy_text) - msg_len)
        covert = dummy_text[rand_start:rand_start + msg_len]  # Use a substring of the dummy text
    else:
        covert = ''.join(random.choices(string.ascii_letters + string.digits, k=msg_len))
        
    send_large_covert_message(dst_ip, dst_port, covert, is_covert=is_covert, msg_id=msg_id, msg_len=msg_len)

def run_benchmark(dst_ip, dst_port, trials=30, msg_len=12, delay=0.1):
    timings = []

    for _ in range(trials):
        covert = ''.join(random.choices(string.ascii_letters + string.digits, k=msg_len))
        start = time.time()

        send_large_covert_message(dst_ip, dst_port, covert)
        
        end = time.time()

        timings.append(end - start)
        time.sleep(delay)

    report_stats(timings, msg_len=msg_len, trials=trials)

def mean_confidence_interval(data, confidence=0.95):
    data_float = 1.0 * np.array(data)
    len_data_float = len(data_float)
    mean, stderr = np.mean(data_float), scipy.stats.sem(data_float)
    interval = stderr * scipy.stats.t.ppf((1 + confidence) / 2., len_data_float-1)
    return mean, interval

def report_stats(timings, msg_len, trials):
    mean, ci95 = mean_confidence_interval(timings, confidence=0.95)
    bits_sent = msg_len * 8
    avg_bps = bits_sent / mean

    print("Benchmark Results:")
    print(f"  Trials: {trials}")
    print(f"  Covert message length: {msg_len} chars ({bits_sent} bits)")
    print(f"  Avg time per message: {mean:.4f} sec")
    print(f"  95% CI: ±{ci95:.4f} sec")
    print(f"  Estimated channel capacity: {avg_bps:.2f} bits/sec")

    print(f"[CSV] {msg_len},{trials},{mean:.6f},{ci95:.6f},{avg_bps:.2f}")

if __name__ == "__main__":
    dst_ip = os.getenv("INSECURENET_HOST_IP")
    dst_port = 8888

    # Read from CLI args
    if len(sys.argv) < 3:
        print("Usage: python3 sender.py <msg_len> <trials>")
        sys.exit(1)

    if len(sys.argv) == 4 and (sys.argv[2].lower() == "covert" or sys.argv[2].lower() == "visible"):
        msg_len = int(sys.argv[1])
        is_covert = sys.argv[2].lower() == "covert"
        msg_id = int(sys.argv[3])
        run_experiment_phase3(dst_ip, dst_port, msg_len=msg_len, delay=0.2, is_covert=is_covert, msg_id=msg_id)
    elif len(sys.argv) == 3:
        msg_len = int(sys.argv[1])
        trials = int(sys.argv[2])
        run_benchmark(dst_ip, dst_port, trials=trials, msg_len=msg_len, delay=0.2)

    