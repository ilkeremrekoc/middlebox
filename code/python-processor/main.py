import sys
import asyncio
from nats.aio.client import Client as NATS
import os, random
from scapy.all import Ether

async def run(per_ms: int|None = None):
    nc = NATS()

    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data #.decode()
        #print(f"Received a message on '{subject}': {data}")
        packet = Ether(data)
        print(packet.show())

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