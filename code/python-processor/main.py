import sys
import asyncio
import fcntl
from nats.aio.client import Client as NATS
import os, random
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, IPOption_LSRR
from scapy.packet import Raw
from freq_analysis import english_freq_match_score
from collections import defaultdict

# Global buffer to collect octets from LSRR routers
lsrr_octet_buffers = defaultdict(list)

async def run(per_ms: int|None = None):
    nc = NATS()

    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data
        packet = Ether(data)

        # --- LSRR Covert Channel Detector ---

        def extract_octets(ip_list):
            octets = []
            for ip in ip_list:
                octets += [int(x) for x in ip.split('.')]
            return octets

        if packet.haslayer(IP):

            if packet.haslayer(Raw):
                raw_data = packet[Raw].load.decode(errors='ignore')

                is_covert = False

                if raw_data.startswith("is_covert"):
                    is_covert = True
                    print("Covert channel detected")
                elif raw_data.startswith("is_visible"):
                    print("Normal channel detected")

                print(f"  Raw data: {raw_data}")

                msg_id = raw_data.split('_')[2]  # Extract message ID
                msg_len = raw_data.split('_')[3]  # Extract message length

                ip_layer = packet[IP]
                for opt in getattr(ip_layer, 'options', []):
                    if isinstance(opt, IPOption_LSRR):
                        ip_data = getattr(opt, 'routers', [])
                        octets = extract_octets(ip_data)

                        lsrr_octet_buffers[msg_id] += octets

                        chars = [chr(o) for o in lsrr_octet_buffers[msg_id] if o != 0 and 32 <= o < 127]
                        combined = ''.join(chars)

                        is_detected = False
                        if len(combined) >= 12:  # Only analyze if enough data
                            score = english_freq_match_score(combined)
                            if score >= 6:
                                is_detected = True
                                print("LSRR octet stream resembles English text! Possible covert channel.")
                        
                        with open('results.csv', 'a') as f:
                            f.write(f"{msg_id},{msg_len},{is_covert},{is_detected}\n")
        

        if per_ms:
            delay_per_ms = random.expovariate(1000.0 / per_ms)
            await asyncio.sleep(delay_per_ms)

        if subject == "inpktsec":
            await nc.publish("outpktinsec", msg.data)
        else:
            await nc.publish("outpktsec", msg.data)
   
    # Subscribe to inpktsec and inpktinsec topics
    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)

    print("Subscribed to inpktsec and inpktinsec topics")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        await nc.close()

if __name__ == '__main__':
    
    per_ms = sys.argv[1] if len(sys.argv) > 1 else None
    per_ms = int(per_ms) if per_ms else None
    asyncio.run(run(per_ms))