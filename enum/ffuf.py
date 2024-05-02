import subprocess
import sys
import re
import tempfile

def download_default_wordlists():
    # Create temporary directories to store wordlists
    temp_dir = tempfile.TemporaryDirectory()
    subdomains_file = tempfile.NamedTemporaryFile(dir=temp_dir.name, delete=False)
    directories_file = tempfile.NamedTemporaryFile(dir=temp_dir.name, delete=False)

    # Download default wordlists
    subprocess.run(["wget", "-O", subdomains_file.name, "https://github.com/danielmiessler/SecLists/raw/master/Discovery/DNS/subdomains-top1million-110000.txt"])
    subprocess.run(["wget", "-O", directories_file.name, "https://github.com/danielmiessler/SecLists/raw/master/Discovery/Web-Content/raft-large-directories.txt"])

    return subdomains_file.name, directories_file.name

def run_ffuf(ip_address, dir_options, subdomain_options):
    # Download default wordlists
    subdomains_file, directories_file = download_default_wordlists()

    # Set default wordlists if user doesn't specify any
    if "-w" not in dir_options:
        dir_options += f" -w {directories_file}"
    if "-w" not in subdomain_options:
        subdomain_options += f" -w {subdomains_file}"

    # Run ffuf in dir mode
    print(f"Running ffuf in dir mode with options: {dir_options}")
    dir_output = subprocess.check_output(['ffuf'] + dir_options.split(), text=True)

    # Parse and display directories
    directories = re.findall(r'^\S+ - \[Status: \d+\]', dir_output, re.MULTILINE)
    print("Directories:", ", ".join(directories))

    # Run ffuf in subdomain mode
    print(f"\nRunning ffuf in subdomain mode with options: {subdomain_options}")
    subdomain_output = subprocess.check_output(['ffuf'] + subdomain_options.split(), text=True)

    # Parse and display subdomains
    subdomains = re.findall(r'^\S+ - \[Status: \d+\]', subdomain_output, re.MULTILINE)
    print("Subdomains:", ", ".join(subdomains))

if __name__ == "__main__":
    # Check if the required arguments are provided
    if len(sys.argv) < 4:
        print("Usage: python script.py <IP_ADDRESS> <DIR_OPTIONS> <SUBDOMAIN_OPTIONS>")
        sys.exit(1)

    ip_address = sys.argv[1]
    dir_options = sys.argv[2]
    subdomain_options = sys.argv[3]

    run_ffuf(ip_address, dir_options, subdomain_options)
