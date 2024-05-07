#!/usr/bin/env python3

import sys
import subprocess
import socket

# Function to print usage information
def usage():
    print("Usage: {} -d <domain> [-p <port>]".format(sys.argv[0]))
    print("Options:")
    print("  -d <domain>       Specify the target domain")
    print("  -p <port>         Specify the port on the target host (default: 80)")
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
domain = None
port = None
try:
    args = sys.argv[1:]
    while args:
        opt = args.pop(0)
        if opt == "-d":
            domain = args.pop(0)
        elif opt == "-p":
            port = args.pop(0)
        else:
            print("Invalid option: {}".format(opt), file=sys.stderr)
            usage()
    if not domain:
        print("Error: Domain not specified.", file=sys.stderr)
        usage()
except IndexError:
    print("Option {} requires an argument.".format(opt), file=sys.stderr)
    usage()

# Set default port if not provided
if not port:
    port = "80"

# Function to update /etc/hosts file
def update_hosts_file(ip_address, domain):
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

# Perform subdomain enumeration using gobuster
print("Enumerating subdomains for {}...".format(domain))
subprocess.run(["gobuster", "dns", "-d", domain, "-w", "/usr/share/wordlists/subdomains.txt", "-q", "-o", "gobuster_subdomains_{}.txt".format(domain)])

# Parse and update /etc/hosts file with subdomains
subdomain_tree = {}
with open("gobuster_subdomains_{}.txt".format(domain)) as subdomains_file:
    for line in subdomains_file:
        subdomain = line.split()[0]
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
    subprocess.run(["gobuster", "dir", "-u", url, "-w", "/usr/share/wordlists/dirb/common.txt", "-q", "-o", "gobuster_directories_{}.txt".format(domain)])

    # Extract directories and add them to the subdomain tree
    with open("gobuster_directories_{}.txt".format(domain)) as directories_file:
        directories = [line.strip() for line in directories_file]
        current_node.extend(directories)

    # Extract newly discovered subdomains and initiate directory scans
    with open("gobuster_directories_{}.txt".format(domain)) as directories_file:
        for line in directories_file:
            new_subdomain = line.split("//")[1].split("/")[0]
            enumerate_directories_recursive("http://{}".format(new_subdomain), depth + 1, current_node)

# Perform initial directory enumeration
print("Enumerating directories for {}...".format(domain))
enumerate_directories_recursive("http://{}:{}".format(domain, port), 0, subdomain_tree)

# Print subdomain tree
print("Subdomain tree for {}:".format(domain))
print_subdomain_tree(subdomain_tree)

print("Enumeration complete.")
