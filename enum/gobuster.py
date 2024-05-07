#!/usr/bin/env python3

import sys
import subprocess
import socket
import argparse
import requests
import os

# Function to print usage information
def usage():
    print("Usage: {} -d <domain> [-p <port>] [-i <ip_address>] [-w <subdomain_wordlist> <dir_wordlist>]".format(sys.argv[0]))
    print("Options:")
    print("  -d <domain>         Specify the target domain")
    print("  -p <port>           Specify the port on the target host (default: 80)")
    print("  -i <ip_address>     Specify the IP address to use for all subdomains (optional)")
    print("  -w <subdomain_wordlist> <dir_wordlist>")
    print("                      Specify custom wordlists for subdomains and directories")
    sys.exit(1)

# Function to resolve IP address of a domain
def resolve_ip(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        print("Error: Failed to resolve IP address for domain '{}'.".format(domain), file=sys.stderr)
        sys.exit(1)

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", help="Specify the target domain", required=True)
parser.add_argument("-p", "--port", help="Specify the port on the target host (default: 80)", default="80")
parser.add_argument("-i", "--ip_address", help="Specify the IP address to use for all subdomains (optional)")
parser.add_argument("-w", "--wordlists", nargs=2, metavar=("subdomain_wordlist", "dir_wordlist"),
                    help="Specify custom wordlists for subdomains and directories")
args = parser.parse_args()

# Check if custom wordlists are provided, otherwise download default wordlists
subdomain_wordlist = args.wordlists[0] if args.wordlists else "subdomains-top1million-110000.txt"
dir_wordlist = args.wordlists[1] if args.wordlists else "directory-list-2.3-big.txt"

# Download default wordlists if they don't exist
if not args.wordlists:
    if not os.path.exists(subdomain_wordlist):
        print("Downloading default subdomain wordlist...")
        subdomain_wordlist_url = "https://github.com/danielmiessler/SecLists/raw/master/Discovery/DNS/subdomains-top1million-110000.txt"
        r = requests.get(subdomain_wordlist_url, allow_redirects=True)
        with open(subdomain_wordlist, 'wb') as f:
            f.write(r.content)
        print("Download complete.")

    if not os.path.exists(dir_wordlist):
        print("Downloading default directory wordlist...")
        dir_wordlist_url = "https://github.com/danielmiessler/SecLists/raw/master/Discovery/Web-Content/directory-list-2.3-big.txt"
        r = requests.get(dir_wordlist_url, allow_redirects=True)
        with open(dir_wordlist, 'wb') as f:
            f.write(r.content)
        print("Download complete.")

# Set default port if not provided
port = args.port

# Function to update /etc/hosts file
def update_hosts_file(ip_address, domain):
    if os.geteuid() != 0:
        print("Warning: Updating /etc/hosts requires root privileges. Please run the script as root or using sudo.")
        return
    with open("/etc/hosts", "a") as hosts_file:
        hosts_file.write("{} {}\n".format(ip_address, domain))

# Function to print subdomain tree
def print_subdomain_tree(subdomain_tree, indent=0):
    for subdomain, ip_address in subdomain_tree.items():
        print("  " * indent + "|- {} ({})".format(subdomain, ip_address))
        if isinstance(ip_address, dict):
            print_subdomain_tree(ip_address, indent + 1)
        elif isinstance(ip_address, list):
            for directory in ip_address:
                print("  " * (indent + 1) + "|- {}".format(directory))

# Function to run a command and wait for completion
def run_command(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in process.stdout:
            sys.stdout.write(line)
        process.communicate()
        if process.returncode != 0:
            print(f"Command failed with exit code {process.returncode}: {command}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# Perform subdomain enumeration using gobuster
print("Enumerating subdomains for {}...".format(args.domain))
subdomain_command = ["gobuster", "dns", "-d", args.domain, "-w", subdomain_wordlist, "-q", "-o", "gobuster_subdomains_{}.txt".format(args.domain)]
run_command(subdomain_command)

# Parse and update /etc/hosts file with subdomains
subdomain_tree = {}
with open("gobuster_subdomains_{}.txt".format(args.domain)) as subdomains_file:
    for line in subdomains_file:
        subdomain = line.split()[0]
        if args.ip_address:
            update_hosts_file(args.ip_address, subdomain)
            print("Found subdomain:", subdomain, "IP:", args.ip_address)
            parts = subdomain.split('.')
            current_level = subdomain_tree
            for part in parts:
                current_level = current_level.setdefault(part, {})
            current_level[subdomain] = args.ip_address
        else:
            ip_address = resolve_ip(subdomain)
            update_hosts_file(ip_address, subdomain)
            print("Found subdomain:", subdomain, "IP:", ip_address)
            parts = subdomain.split('.')
            current_level = subdomain_tree
            for part in parts:
                current_level = current_level.setdefault(part, {})
            current_level[subdomain] = []

# Function to perform directory enumeration recursively
def enumerate_directories_recursive(url, depth, current_node):
    # Perform directory enumeration using gobuster
    directory_command = ["gobuster", "dir", "-u", url, "-w", dir_wordlist, "-q", "-o", "gobuster_directories_{}.txt".format(args.domain)]
    run_command(directory_command)

    # Extract directories and add them to the subdomain tree
    with open("gobuster_directories_{}.txt".format(args.domain)) as directories_file:
        directories = [line.strip() for line in directories_file]
        current_node.extend(directories)

    # Extract newly discovered subdomains and initiate directory scans
    with open("gobuster_directories_{}.txt".format(args.domain)) as directories_file:
        for line in directories_file:
            new_subdomain = line.strip()
            enumerate_directories_recursive("http://{}".format(new_subdomain), depth + 1, current_node)

# Perform initial directory enumeration
print("Enumerating directories for {}...".format(args.domain))
enumerate_directories_recursive("http://{}:{}".format(args.domain, port), 0, subdomain_tree)

# Print subdomain tree
print("Subdomain tree for {}:".format(args.domain))
print_subdomain_tree(subdomain_tree)

print("Enumeration complete.")
