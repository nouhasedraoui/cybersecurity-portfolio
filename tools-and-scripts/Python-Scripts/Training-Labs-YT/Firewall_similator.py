import random
import logging
from datetime import datetime

logging.basicConfig(
    filename='firewall_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FirewallSimulator:
    def __init__(self):
        self.blocked_ips = {
            "192.168.1.1", "192.168.1.4", "192.168.1.9",
            "192.168.1.13", "192.168.1.16", "192.168.1.19"
        }

    def generate_traffic(self):
        ip = f"192.168.1.{random.randint(0, 25)}"
        payload_size = random.randint(64, 1500)  
        return ip, payload_size

    def analyze_packet(self, ip):
        if ip in self.blocked_ips:
            return "BLOCK"
        return "ALLOW"

    def run_simulation(self, attempts=15):
        print(f"--- Starting Firewall Simulation at {datetime.now()} ---")
        for _ in range(attempts):
            ip, size = self.generate_traffic()
            action = self.analyze_packet(ip)
            
            log_msg = f"Source: {ip} | Size: {size} bytes | Action: {action}"
            print(log_msg)
            if action == "BLOCK":
                logging.warning(log_msg)
            else:
                logging.info(log_msg)

if __name__ == "__main__":
    firewall = FirewallSimulator()
    firewall.run_simulation(20)
