import subprocess
import sys
import random
import re

def get_current_mac(interface):
    try:
        output = subprocess.check_output(["ifconfig", interface]).decode('utf-8')
        search_result = re.search(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", output)
        if search_result:
            return search_result.group(0)
    except:
        return None

def generate_random_mac(vendor_prefix=None):
    hex_chars = "0123456789abcdef"
    if vendor_prefix:
        parts = vendor_prefix.split(":")
    else:
        parts = [random.choice(hex_chars) + random.choice(hex_chars)]
    
    while len(parts) < 6:
        parts.append(random.choice(hex_chars) + random.choice(hex_chars))
    return ":".join(parts)

def change_mac(interface, new_mac):
    subprocess.call(["ifconfig", interface, "down"])
    subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
    subprocess.call(["ifconfig", interface, "up"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sudo python mac_pro.py <interface>")
        sys.exit(1)

    target_interface = sys.argv[1]
    
    vendors = {
        "1": ("Apple", "00:25:00"),
        "2": ("Samsung", "00:00:f0"),
        "3": ("Intel", "00:03:47"),
        "4": ("Cisco", "00:00:0c")
    }

    print("[*] Options:")
    print("1. Completely Random MAC")
    print("2. Specific Vendor MAC (Apple, Samsung, etc.)")
    print("3. Manual Input")
    
    mode = input("Select mode (1, 2, or 3): ")

    if mode == "1":
        new_mac = generate_random_mac()
    elif mode == "2":
        print("\nAvailable Vendors:")
        for key, value in vendors.items():
            print(f"{key}. {value[0]}")
        v_choice = input("Select vendor: ")
        if v_choice in vendors:
            new_mac = generate_random_mac(vendors[v_choice][1])
        else:
            sys.exit("Invalid vendor.")
    elif mode == "3":
        new_mac = input("Enter full MAC: ")
    else:
        sys.exit("Invalid choice.")

    change_mac(target_interface, new_mac)
    
    updated_mac = get_current_mac(target_interface)
    if updated_mac == new_mac:
        print(f"[+] MAC changed to {updated_mac} ({vendors.get(v_choice, ['Custom'])[0] if mode=='2' else 'Random/Manual'})")
    else:
        print("[-] Failure.")
