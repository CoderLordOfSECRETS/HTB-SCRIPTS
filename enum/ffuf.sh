#!/bin/bash

# Default values
IP_TO_BIND="127.0.0.1"
PORT="80"
STARTING_DOMAIN=""
VHOST_WORDLIST="combined_subdomains.txt"
EXTENSION_WORDLIST="raft-large-extensions.txt"
DIR_WORDLIST="directory-list-2.3-big.txt"
OUTPUT_DIR="ffuf_results"
HOSTS_FILE="/etc/hosts"

# Function to display usage
usage() {
    echo "Usage: $0 -d <starting_domain> [-i <ip_to_bind>] [-p <port>] [-vh <vhost_wordlist>] [-e <extension_wordlist>] [-d <dir_wordlist>]"
    exit 1
}

# Parse flags
while getopts ":d:i:p:vh:e:di:" opt; do
    case ${opt} in
        d )
            STARTING_DOMAIN="$OPTARG"
            ;;
        i )
            IP_TO_BIND="$OPTARG"
            ;;
        p )
            PORT="$OPTARG"
            ;;
        vh )
            VHOST_WORDLIST="$OPTARG"
            ;;
        e )
            EXTENSION_WORDLIST="$OPTARG"
            ;;
        di )
            DIR_WORDLIST="$OPTARG"
            ;;
        \? )
            echo "Invalid option: $OPTARG" 1>&2
            usage
            ;;
        : )
            echo "Invalid option: $OPTARG requires an argument" 1>&2
            usage
            ;;
    esac
done
shift $((OPTIND -1))

# Check if starting domain is provided
if [ -z "$STARTING_DOMAIN" ]; then
    echo "Please provide a starting domain."
    usage
fi

# Create output directory if not exists
mkdir -p "$OUTPUT_DIR"

# Download wordlists if not present
if [ ! -f "$VHOST_WORDLIST" ]; then
    wget -O "$VHOST_WORDLIST" https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/combined_subdomains.txt
fi

if [ ! -f "$EXTENSION_WORDLIST" ]; then
    wget -O "$EXTENSION_WORDLIST" https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-large-extensions.txt
fi

if [ ! -f "$DIR_WORDLIST" ]; then
    wget -O "$DIR_WORDLIST" https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-big.txt
fi

# Add domains to /etc/hosts
while read -r domain; do
    echo "$IP_TO_BIND $domain" >> "$HOSTS_FILE"
done < <(echo "$STARTING_DOMAIN")

# Run vhost scan
ffuf -w "$VHOST_WORDLIST" -u "http://$STARTING_DOMAIN" -H "Host: FUZZ" -fs 0 -o "$OUTPUT_DIR/vhost_results.txt"

# Extract unique vhosts
cut -d ' ' -f 2 "$OUTPUT_DIR/vhost_results.txt" | sort -u > "$OUTPUT_DIR/unique_vhosts.txt"

# Run extension scan
ffuf -w "$EXTENSION_WORDLIST" -u "http://$STARTING_DOMAIN/FUZZ" -o "$OUTPUT_DIR/extension_results.txt"

# Run recursive dir search
while read -r vhost; do
    while read -r extension; do
        ffuf -w "$DIR_WORDLIST" -u "http://$vhost/FUZZ.$extension" -o "$OUTPUT_DIR/${vhost}_${extension}_dir_results.txt" -fc 404 -fs 0 -e "robots.txt"
    done < "$EXTENSION_WORDLIST"
done < "$OUTPUT_DIR/unique_vhosts.txt"
