import subprocess
import sys
import re

def nmap_and_gobuster(ip_address, nmap_options, gobuster_dir_options, gobuster_subdomain_options):
    # Run Nmap scan
    nmap_output = subprocess.check_output(['python', 'nmap.py', ip_address] + nmap_options.split(), text=True)

    # Print Nmap output
    print("Nmap Output:")
    print(nmap_output)

    # Find web services in Nmap output
    web_services = re.findall(r'(?i)^(?:(?:\d+/open/.+)|(?:http|https)\s+open\s+\S+)', nmap_output, re.MULTILINE)
    if web_services:
        print("\nWeb services discovered:")
        for service in web_services:
            if "http" in service:
                url = re.search(r'(https?://\S+)', service).group(1)
                print(url)
                # Run Gobuster on web service URL
                print(f"\nRunning Gobuster on {url}...")
                gobuster_process = subprocess.Popen(['python', 'gobuster.py', url, gobuster_dir_options, gobuster_subdomain_options], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                gobuster_output, _ = gobuster_process.communicate()
                # Print Gobuster output
                print("\nGobuster Output:")
                print(gobuster_output)

if __name__ == "__main__":
    # Check if the required arguments are provided
    if len(sys.argv) < 5:
        print("Usage: python nmap_and_gobuster.py <IP_ADDRESS> <NMAP_OPTIONS> <DIR_OPTIONS> <SUBDOMAIN_OPTIONS>")
        sys.exit(1)

    ip_address = sys.argv[1]
    nmap_options = sys.argv[2]
    gobuster_dir_options = sys.argv[3]
    gobuster_subdomain_options = sys.argv[4]

    nmap_and_gobuster(ip_address, nmap_options, gobuster_dir_options, gobuster_subdomain_options)
