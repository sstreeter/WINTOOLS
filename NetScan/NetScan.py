"""
Network Discovery Script
========================

This script performs parallel subnet scanning, identifies device types,
retrieves MAC addresses, maps vendors using the Wireshark manuf file,
and visualizes the network using Plotly.

Requirements:
-------------
1. Install Nmap (CLI tool)
   macOS  : brew install nmap
   Linux  : sudo apt install nmap
   Windows: https://nmap.org/download.html (add to PATH)

2. Install Python packages:
   pip install python-nmap tqdm requests plotly networkx

Note:
-----
Do NOT use `pip install nmap` — that package does not exist.
Use `python-nmap`, which is the correct Python wrapper for the Nmap CLI tool.

Author: [Your Name]
"""

import os
import re
import sys
import socket
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_network
from tqdm import tqdm
import requests
import nmap
import networkx as nx
import plotly.graph_objects as go

# Constants
MANUF_URL = "https://www.wireshark.org/download/automated/data/manuf"
MANUF_FILE = "manuf"
MANUF_HASH_FILE = "manuf_hash.txt"
NETS_FILE = "nets.txt"
MAX_THREADS = 8

# Download and verify manuf file
def get_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_manuf_file():
    try:
        response = requests.get(MANUF_URL)
        response.raise_for_status()
        with open(MANUF_FILE, 'wb') as f:
            f.write(response.content)
        print("✅ Wireshark manuf file downloaded.")
        return True
    except requests.RequestException as e:
        print(f"❌ Error downloading manuf file: {e}")
        return False

def check_and_download_manuf():
    last_hash = None
    if os.path.exists(MANUF_HASH_FILE):
        with open(MANUF_HASH_FILE, 'r') as f:
            last_hash = f.read().strip()

    if not download_manuf_file():
        return False

    current_hash = get_file_hash(MANUF_FILE)
    if current_hash != last_hash:
        print("🔁 Manuf file has been updated.")
        with open(MANUF_HASH_FILE, 'w') as f:
            f.write(current_hash)
    else:
        print("✔️ Manuf file is up to date.")
    return True

def parse_manuf_file():
    vendor_dict = {}
    with open(MANUF_FILE, 'r') as file:
        for line in file:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            mac_prefix = parts[0].lower()
            vendor = " ".join(parts[1:])
            vendor_dict[mac_prefix] = vendor
    return vendor_dict

def get_vendor_from_mac(mac, vendor_dict):
    if mac == 'N/A':
        return "Unknown"
    mac_prefix = ":".join(mac.lower().split(":")[0:3])
    return vendor_dict.get(mac_prefix, "Unknown")

def classify_device(vendor):
    if "Apple" in vendor:
        return "Mac/iPhone"
    elif "Samsung" in vendor or "Huawei" in vendor:
        return "Tablet/Phone"
    elif "Microsoft" in vendor or "Windows" in vendor:
        return "PC"
    elif "Lenovo" in vendor or "Dell" in vendor or "HP" in vendor:
        return "PC"
    else:
        return "Unknown"

def normalize_mac(mac):
    parts = mac.split(':')
    normalized_parts = [p.zfill(2) for p in parts]
    return ':'.join(normalized_parts)

def get_mac_from_arp(ip):
    try:
        output = subprocess.check_output(f"arp -n {ip}", shell=True).decode('utf-8')
        mac_address = re.search(r"([a-f0-9]{1,2}[:-]){5}[a-f0-9]{1,2}", output, re.I)
        if mac_address:
            return normalize_mac(mac_address.group(0).lower())
    except:
        pass
    return "N/A"

def read_subnets(file_path):
    subnets = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                subnets.append(line)
    return subnets

# Scan individual IP
def scan_ip(ip, vendor_dict):
    scanner = nmap.PortScanner()
    try:
        scanner.scan(hosts=str(ip), arguments='-sn')
        if ip in scanner.all_hosts():
            mac = scanner[ip]['addresses'].get('mac', get_mac_from_arp(str(ip)))
            vendor = get_vendor_from_mac(mac, vendor_dict)
            return {'ip': str(ip), 'mac': mac, 'vendor': vendor, 'type': classify_device(vendor)}
    except Exception:
        pass
    return None

# Main scanning routine per subnet
def scan_subnet(subnet, vendor_dict):
    print(f"\n🔍 Scanning subnet: {subnet}")
    found_devices = []
    network = ip_network(subnet, strict=False)
    dead_count = 0

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(scan_ip, ip, vendor_dict): ip for ip in network.hosts()}
        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Scanning {subnet}"):
            result = future.result()
            if result:
                found_devices.append(result)
            else:
                dead_count += 1

    if len(found_devices) == 0:
        print(f"⚠️ Entire network {subnet} appears to be dead. Consider removing it.")
    return subnet, found_devices

# Network graph visualization
def visualize_network(all_devices):
    G = nx.Graph()

    for device in all_devices:
        ip = device['ip']
        G.add_node(ip, label=ip, vendor=device['vendor'], type=device['type'])

    for i, d1 in enumerate(all_devices):
        for j, d2 in enumerate(all_devices):
            if i < j:
                G.add_edge(d1['ip'], d2['ip'])

    pos = nx.kamada_kawai_layout(G)
    node_x, node_y, node_text, node_colors = [], [], [], []

    for node, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        info = G.nodes[node]
        node_text.append(f"{info['label']}<br>{info['vendor']} ({info['type']})")

        if info['type'] == "Mac/iPhone":
            node_colors.append('blue')
        elif info['type'] == "PC":
            node_colors.append('green')
        elif info['type'] == "Tablet/Phone":
            node_colors.append('orange')
        else:
            node_colors.append('gray')

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers', text=node_text,
                             marker=dict(size=20, color=node_colors, opacity=0.8,
                                         line=dict(width=1, color='black'))))
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', hoverinfo='none',
                             line=dict(width=0.5, color='black')))
    fig.update_layout(title="Network Discovery", showlegend=False,
                      xaxis=dict(showgrid=False, zeroline=False),
                      yaxis=dict(showgrid=False, zeroline=False))
    fig.show()

# Run the program
if __name__ == "__main__":
    if not os.path.exists(NETS_FILE):
        print(f"❌ {NETS_FILE} not found. Please create it with your target subnets.")
        sys.exit(1)

    check_and_download_manuf()
    vendor_dict = parse_manuf_file()
    subnets = read_subnets(NETS_FILE)

    all_devices = []
    summary = []

    for subnet in subnets:
        subnet, devices = scan_subnet(subnet, vendor_dict)
        all_devices.extend(devices)
        summary.append((subnet, len(devices)))

    # Report
    print("\n📊 Scan Summary:")
    for subnet, count in summary:
        print(f" - {subnet}: {count} device(s) found")
    print(f"📦 Total devices found: {len(all_devices)}")

    if all_devices:
        visualize_network(all_devices)
