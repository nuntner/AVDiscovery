import socket
import struct
from zeroconf import ServiceBrowser, Zeroconf
import time

def ssdp_discovery(timeout=2):
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_ST = "ssdp:all"

    ssdp_request = f"""M-SEARCH * HTTP/1.1\r
HOST: {SSDP_ADDR}:{SSDP_PORT}\r
MAN: "ssdp:discover"\r
MX: 1\r
ST: {SSDP_ST}\r
\r
""".encode('utf-8')

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # Set a timeout
    sock.settimeout(timeout)
    # Send the SSDP request
    sock.sendto(ssdp_request, (SSDP_ADDR, SSDP_PORT))

    responses = []
    try:
        while True:
            data, addr = sock.recvfrom(65507)
            responses.append((data, addr))
    except socket.timeout:
        pass

    return responses

class DeviceListener:
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            addresses = ['.'.join(map(str, addr)) for addr in info.addresses]
            device = {
                'name': name,
                'type': service_type,
                'address': addresses,
                'port': info.port,
                'properties': {k.decode('utf-8'): v.decode('utf-8') for k, v in info.properties.items()}
            }
            self.devices.append(device)
            print(f"Discovered device: {device}")

if __name__ == "__main__":
    # SSDP Discovery
    print("Starting SSDP Discovery...")
    ssdp_devices = ssdp_discovery()
    print(f"SSDP Discovery found {len(ssdp_devices)} devices.")
    for data, addr in ssdp_devices:
        print(f"Device at {addr}:\n{data.decode('utf-8', errors='replace')}\n")

    # mDNS Discovery
    print("Starting mDNS Discovery...")
    zeroconf = Zeroconf()
    listener = DeviceListener()
    service_types = [
        "_services._dns-sd._udp.local.",
        "_http._tcp.local.",
        # You can add more service types here
    ]

    browsers = []
    for service_type in service_types:
        browser = ServiceBrowser(zeroconf, service_type, listener)
        browsers.append(browser)

    # Allow some time for discovery
    time.sleep(5)
    zeroconf.close()

    print(f"mDNS Discovery found {len(listener.devices)} devices.")
