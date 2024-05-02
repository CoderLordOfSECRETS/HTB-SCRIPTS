import subprocess
import argparse

def nmap_scan(target_ip, options):
    if options == "--optimal":
        # If --optimal option is passed, use Nmap's aggressive scan options
        nmap_command = f"nmap -A {target_ip}"
    else:
        # Use the provided options for the Nmap scan
        nmap_command = f"nmap {options} {target_ip}"

    try:
        # Execute the Nmap command using subprocess
        result = subprocess.run(
            nmap_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Print the Nmap scan results
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stderr.decode())

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Automatically perform Nmap scans")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("options", nargs="*", help="Nmap options or --optimal for best options")
    args = parser.parse_args()

    target_ip = args.target
    options = " ".join(args.options)

    # Perform Nmap scan
    nmap_scan(target_ip, options)
