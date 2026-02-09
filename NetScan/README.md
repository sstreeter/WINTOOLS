# 🔍 WINTOOLS: NetScan
Cross-platform subnet discovery, vendor mapping, and network topology visualization.

## 📋 Overview
**NetScan** is a Python-based utility for discovering devices on a local area network. It uses `nmap` for scanning and Wireshark's `manuf` database for identifying device hardware vendors.

### Core Features
*   **Subnet Scanning**: Parallel scanning of entire IP ranges.
*   **Vendor Mapping**: Automatically identifies device manufacturers (Apple, HP, Dell, etc.).
*   **Device Classification**: Groups devices into categories (Mac/iPhone, PC, Tablet).
*   **Visual Topology**: Generates an interactive graph of the discovered network.
*   **Discovery Persistence**: Keeps track of discovered devices and their MAC addresses.

## 🛠️ Requirements
*   **Nmap CLI**: Must be installed and available in the system PATH.
    *   macOS: `brew install nmap`
    *   Windows: [Download from nmap.org](https://nmap.org/download.html)
*   **Python Dependencies**:
    ```bash
    pip install python-nmap tqdm requests plotly networkx
    ```

## 🔒 Data Privacy
*   **Subnet Protection**: The file `nets.txt` is where you store your internal network ranges. It is automatically ignored by `.gitignore` to prevent leaking your network topology to GitHub or other repositories.
*   **Stubs**: Use the provided comments in `nets.txt` as a template.

## 🚀 Usage
1.  **Configure Subnets**: Edit `nets.txt` in the `NetScan` directory. Add one subnet per line (e.g., `192.168.1.0/24`).
2.  **Run Discovery**:
    ```bash
    python NetScan.py
    ```
3.  **View Report**: The script will output a text summary and open an interactive Plotly graph in your browser.

## 📁 Structure
*   `NetScan.py`: The main discovery engine.
*   `nets.txt`: Configuration file for target subnets.
*   `manuf`: Wireshark's vendor database (automatically downloaded).
