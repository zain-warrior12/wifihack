#!/usr/bin/env python3
"""
WiFi Tool for Termux (Android) - Works on Non-Rooted Devices

Setup in Termux:
    pkg update && pkg upgrade
    pkg install python termux-api root-repo
    pip install colorama
    
Also install "Termux:API" app from F-Droid
Grant location permission to Termux:API app in Android settings!
"""

import subprocess
import json
import time
import os
import sys
import hashlib
import binascii
from colorama import Fore, Style, init

init(autoreset=True)

def run_cmd(cmd, timeout=15):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                               text=True, timeout=timeout)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception as e:
        return str(e), -1

def check_permissions():
    """Check and request necessary permissions"""
    print(f"{Fore.YELLOW}[*] Checking permissions...")
    
    # Try to trigger permission request
    run_cmd("termux-wifi-enable true", timeout=5)
    time.sleep(1)
    
    # Check if location is enabled (required for WiFi scanning)
    out, _ = run_cmd("termux-location", timeout=10)
    if "permission" in out.lower() or not out:
        print(f"{Fore.YELLOW}[!] Please grant Location permission to Termux:API app")
        print(f"{Fore.CYAN}    Settings > Apps > Termux:API > Permissions > Location")

def scan_networks_termux():
    """Scan using termux-wifi-scaninfo"""
    print(f"{Fore.YELLOW}[*] Scanning with termux-api...")
    
    # First trigger a fresh scan
    run_cmd("termux-wifi-enable true", timeout=5)
    time.sleep(2)
    
    out, code = run_cmd("termux-wifi-scaninfo", timeout=20)
    if code == 0 and out:
        try:
            networks = json.loads(out)
            if networks:
                return networks
        except:
            pass
    return []

def scan_networks_dumpsys():
    """Alternative scan using dumpsys (works on some devices)"""
    print(f"{Fore.YELLOW}[*] Trying alternative scan method...")
    
    out, code = run_cmd("dumpsys wifi | grep -E 'SSID|BSSID|level'", timeout=10)
    networks = []
    
    if out:
        lines = out.split('\n')
        current = {}
        for line in lines:
            if 'SSID:' in line:
                if current.get('ssid'):
                    networks.append(current)
                current = {'ssid': line.split('SSID:')[-1].strip().strip('"')}
            elif 'BSSID:' in line:
                current['bssid'] = line.split('BSSID:')[-1].strip()
            elif 'level' in line.lower():
                try:
                    level = int(''.join(filter(lambda x: x.isdigit() or x == '-', line)))
                    current['rssi'] = level
                except:
                    pass
        if current.get('ssid'):
            networks.append(current)
    
    return networks


def get_current_wifi():
    """Get current WiFi connection info"""
    out, code = run_cmd("termux-wifi-connectioninfo", timeout=10)
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            pass
    return None

def scan_all_methods():
    """Try all scanning methods"""
    # Method 1: termux-api
    networks = scan_networks_termux()
    if networks:
        return networks
    
    # Method 2: dumpsys
    networks = scan_networks_dumpsys()
    if networks:
        return networks
    
    # Method 3: Show current connection at least
    print(f"{Fore.YELLOW}[*] Checking current connection...")
    current = get_current_wifi()
    if current and current.get('ssid'):
        return [current]
    
    return []

def display_networks(networks):
    """Display networks"""
    if not networks:
        print(f"{Fore.RED}[-] No networks found!")
        print(f"{Fore.YELLOW}[!] Tips:")
        print(f"    1. Grant Location permission to Termux:API app")
        print(f"    2. Enable Location/GPS on your device")
        print(f"    3. Make sure WiFi is enabled")
        print(f"    4. Try: termux-wifi-enable true")
        return []
    
    print(f"\n{Fore.GREEN}[+] Found {Fore.YELLOW}{len(networks)}{Fore.GREEN} networks:")
    print(f"{Fore.CYAN}{'━' * 75}")
    
    for i, net in enumerate(networks, 1):
        ssid = net.get('ssid', net.get('SSID', 'Hidden')) or 'Hidden'
        bssid = net.get('bssid', net.get('BSSID', 'Unknown'))
        level = net.get('rssi', net.get('level', net.get('signal_level', 'N/A')))
        caps = net.get('capabilities', '')
        
        auth = 'WPA2' if 'WPA2' in str(caps) else 'WPA' if 'WPA' in str(caps) else 'Open'
        
        print(f"{Fore.WHITE}{i:2}. {Fore.GREEN}SSID: {Fore.YELLOW}{str(ssid):22} "
              f"{Fore.CYAN}| BSSID: {Fore.MAGENTA}{bssid} "
              f"{Fore.CYAN}| {Fore.WHITE}{level} dBm "
              f"{Fore.CYAN}| {Fore.RED}{auth}")
    
    print(f"{Fore.CYAN}{'━' * 75}")
    return networks

def get_network_by_index(idx, networks):
    """Get network by index number"""
    try:
        return networks[int(idx) - 1]
    except:
        return None

def pbkdf2_check(password, ssid):
    """Generate WPA PSK from password and SSID (for offline verification)"""
    try:
        psk = hashlib.pbkdf2_hmac('sha1', password.encode(), ssid.encode(), 4096, 32)
        return binascii.hexlify(psk).decode()
    except:
        return None

def connect_via_intent(ssid, password):
    """Try to connect using Android intent (opens WiFi settings)"""
    print(f"{Fore.YELLOW}[*] Opening WiFi settings...")
    print(f"{Fore.CYAN}[*] Network: {ssid}")
    print(f"{Fore.CYAN}[*] Password to try: {password}")
    
    # Open WiFi settings
    run_cmd("am start -a android.settings.WIFI_SETTINGS", timeout=5)
    
    print(f"\n{Fore.GREEN}[+] WiFi settings opened!")
    print(f"{Fore.YELLOW}[!] Manually select '{ssid}' and enter the password above")
    
    input(f"\n{Fore.CYAN}[?] Press Enter after trying to connect...")
    
    # Check if connected
    time.sleep(2)
    current = get_current_wifi()
    if current and current.get('ssid') == ssid:
        return True
    return False


def test_passwords_offline(ssid, wordlist_path):
    """
    Test passwords offline by generating PSK hashes
    This doesn't actually connect but validates password format
    and generates hashes for later use
    """
    if not os.path.exists(wordlist_path):
        print(f"{Fore.RED}[-] Wordlist not found: {wordlist_path}")
        return
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip() and len(line.strip()) >= 8]
    except Exception as e:
        print(f"{Fore.RED}[-] Error reading wordlist: {e}")
        return
    
    print(f"\n{Fore.GREEN}[+] Loaded {len(passwords)} valid passwords (8+ chars)")
    print(f"{Fore.YELLOW}[*] Generating PSK hashes for: {ssid}")
    print(f"{Fore.CYAN}[*] This prepares passwords for manual testing\n")
    
    # Save results
    output_file = f"psk_{ssid.replace(' ', '_')}.txt"
    
    with open(output_file, 'w') as out:
        out.write(f"# PSK hashes for SSID: {ssid}\n")
        out.write(f"# Format: password:psk_hash\n\n")
        
        for i, pwd in enumerate(passwords, 1):
            psk = pbkdf2_check(pwd, ssid)
            print(f"{Fore.CYAN}[{i}/{len(passwords)}] {Fore.WHITE}{pwd:20} {Fore.GREEN}-> {Fore.YELLOW}{psk[:16]}...", end='\r')
            out.write(f"{pwd}:{psk}\n")
    
    print(f"\n\n{Fore.GREEN}[+] Saved to: {output_file}")
    print(f"{Fore.YELLOW}[*] Top 10 passwords to try manually:")
    
    for pwd in passwords[:10]:
        print(f"    {Fore.WHITE}• {pwd}")

def semi_auto_attack(ssid, wordlist_path):
    """Semi-automatic attack - opens WiFi settings for each password"""
    if not os.path.exists(wordlist_path):
        print(f"{Fore.RED}[-] Wordlist not found!")
        return
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip() and len(line.strip()) >= 8]
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}")
        return
    
    print(f"\n{Fore.GREEN}[+] Loaded {len(passwords)} passwords")
    print(f"{Fore.YELLOW}[*] Semi-auto mode: Will show each password to try")
    print(f"{Fore.CYAN}[*] Press Enter to try next, 'q' to quit, 's' to skip 10\n")
    
    i = 0
    while i < len(passwords):
        pwd = passwords[i]
        print(f"\n{Fore.CYAN}[{i+1}/{len(passwords)}] {Fore.WHITE}Password: {Fore.YELLOW + Style.BRIGHT}{pwd}")
        
        choice = input(f"{Fore.CYAN}[Enter=try, s=skip10, o=open wifi, q=quit]: {Fore.WHITE}").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 's':
            i += 10
            continue
        elif choice == 'o':
            if connect_via_intent(ssid, pwd):
                print(f"\n{Fore.GREEN}{'=' * 50}")
                print(f"{Fore.GREEN}[+] CONNECTED! Password: {Fore.RED}{pwd}")
                print(f"{Fore.GREEN}{'=' * 50}")
                return
        
        i += 1
    
    print(f"\n{Fore.RED}[-] Finished without finding password")

def print_banner():
    banner = f"""
{Fore.GREEN + Style.BRIGHT}
╦ ╦╦╔═╗╦  ╔╦╗╔═╗╔═╗╦  
║║║║╠╣ ║   ║ ║ ║║ ║║  
╚╩╝╩╚  ╩   ╩ ╚═╝╚═╝╩═╝
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.YELLOW}[*] Termux WiFi Tool - Works on Non-Rooted Devices
{Fore.GREEN}[*] For Educational Purposes Only  
{Fore.RED}[!] Unauthorized Access is Illegal
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Style.RESET_ALL}"""
    print(banner)


def main():
    print_banner()
    
    # Check permissions
    check_permissions()
    
    # Initial scan
    networks = scan_all_methods()
    networks = display_networks(networks)
    
    # Show current connection
    current = get_current_wifi()
    if current and current.get('ssid'):
        print(f"\n{Fore.GREEN}[+] Connected to: {Fore.YELLOW}{current.get('ssid')}")
        print(f"    {Fore.CYAN}IP: {current.get('ip', 'N/A')}")
    
    # Menu
    while True:
        print(f"\n{Fore.CYAN}╔═══════════════════════════════════════╗")
        print(f"{Fore.CYAN}║{Fore.WHITE}  1. Scan networks                     {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  2. View network details              {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  3. Generate PSK hashes (offline)     {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  4. Semi-auto password test           {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  5. Open WiFi settings                {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  6. Show current connection           {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.WHITE}  0. Exit                              {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚═══════════════════════════════════════╝")
        
        choice = input(f"{Fore.CYAN}[?] Select: {Fore.WHITE}").strip()
        
        if choice == '1':
            networks = scan_all_methods()
            networks = display_networks(networks)
        
        elif choice == '2':
            if not networks:
                print(f"{Fore.RED}[-] No networks. Scan first!")
                continue
            idx = input(f"{Fore.CYAN}[?] Enter network # or BSSID: {Fore.WHITE}").strip()
            
            net = get_network_by_index(idx, networks) if idx.isdigit() else None
            if not net:
                for n in networks:
                    if n.get('bssid', '').lower() == idx.lower():
                        net = n
                        break
            
            if net:
                print(f"\n{Fore.GREEN}[+] Network Details:")
                for k, v in net.items():
                    print(f"    {Fore.CYAN}{k}: {Fore.YELLOW}{v}")
            else:
                print(f"{Fore.RED}[-] Not found!")
        
        elif choice == '3':
            if not networks:
                ssid = input(f"{Fore.CYAN}[?] Enter SSID manually: {Fore.WHITE}").strip()
            else:
                idx = input(f"{Fore.CYAN}[?] Enter network # or SSID: {Fore.WHITE}").strip()
                net = get_network_by_index(idx, networks) if idx.isdigit() else None
                ssid = net.get('ssid') if net else idx
            
            wordlist = input(f"{Fore.CYAN}[?] Wordlist path: {Fore.WHITE}").strip().strip('"\'')
            test_passwords_offline(ssid, wordlist)
        
        elif choice == '4':
            if not networks:
                ssid = input(f"{Fore.CYAN}[?] Enter SSID: {Fore.WHITE}").strip()
            else:
                idx = input(f"{Fore.CYAN}[?] Enter network #: {Fore.WHITE}").strip()
                net = get_network_by_index(idx, networks)
                ssid = net.get('ssid') if net else input(f"{Fore.CYAN}[?] SSID: {Fore.WHITE}").strip()
            
            wordlist = input(f"{Fore.CYAN}[?] Wordlist path: {Fore.WHITE}").strip().strip('"\'')
            semi_auto_attack(ssid, wordlist)
        
        elif choice == '5':
            run_cmd("am start -a android.settings.WIFI_SETTINGS", timeout=5)
            print(f"{Fore.GREEN}[+] WiFi settings opened!")
        
        elif choice == '6':
            current = get_current_wifi()
            if current:
                print(f"\n{Fore.GREEN}[+] Current Connection:")
                for k, v in current.items():
                    print(f"    {Fore.CYAN}{k}: {Fore.YELLOW}{v}")
            else:
                print(f"{Fore.RED}[-] Not connected or unable to get info")
        
        elif choice == '0':
            print(f"{Fore.GREEN}[+] Bye!")
            break
        
        else:
            print(f"{Fore.RED}[-] Invalid option!")

if __name__ == "__main__":
    main()
