#!/usr/bin/env python3
"""
Safe, improved version of the Facebook login tool for development and testing.

Important:
- This script does NOT bypass Facebook verification or security checks.
- If Facebook responds that verification is required, the script reports that
  and does not attempt to circumvent it.
- For local development you can enable `test_mode=True` to simulate responses.
"""

import random
import string
import json
import time
import requests
import uuid
import base64
import io
import struct
import sys
import os

# COLORS AND STYLING
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def animated_print(text, delay=0.005, color=GREEN):
    for char in text:
        sys.stdout.write(color + char + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_logo():
    logo_text = f"""
  _   _    _    ____  _____ _____ __  __
 | \\ | |  / \\  |  _ \\| ____| ____|  \\/  |
 |  \\| | / _ \\ | | | |  _| |  _| | |\\/| |
 | |\\  |/ ___ \\| |_| | |___| |___| |  | |
 |_| \\_/_/   \\_\\____/|_____|_____|_|  |_|
          {BOLD}FACEBOOK LOGIN TOOL{RESET}
    """
    colors = [RED, GREEN, YELLOW, CYAN]
    for line in logo_text.split('\n'):
        color = random.choice(colors)
        sys.stdout.write(color + line + "\n")
        time.sleep(0.02)
    print(RESET)

# Minimal dependency check for pycryptodome
try:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except Exception:
    print(f"{YELLOW}Warning: pycryptodome not available. Encryption will not work.{RESET}")
    AES = PKCS1_v1_5 = RSA = get_random_bytes = None

class FacebookPasswordEncryptor:
    @staticmethod
    def get_public_key():
        """
        Attempt to fetch public key from Facebook endpoint.
        Returns tuple (public_key_pem_string, key_id) or raises Exception.
        """
        url = 'https://b-graph.facebook.com/pwd_key_fetch'
        params = {
            'version': '2',
            'flow': 'CONTROLLER_INITIALIZATION',
            'method': 'GET',
            'fb_api_req_friendly_name': 'pwdKeyFetch',
            'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations',
            'access_token': '438142079694454|fc0a7caa49b192f64f6f5a6d9643bb28'
        }
        try:
            resp = requests.post(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            public_key = data.get('public_key')
            key_id = str(data.get('key_id', '25'))
            if not public_key:
                raise Exception("No public_key in response")
            return public_key, key_id
        except Exception as e:
            raise Exception(f"Public key fetch error: {e}")

    @staticmethod
    def encrypt(password, public_key=None, key_id="25"):
        """
        Encrypt password similarly to FB4A flow. If pycryptodome not installed,
        raise informative exception.
        """
        if AES is None or RSA is None:
            raise Exception("Encryption dependencies not available. Install pycryptodome.")
        if public_key is None:
            public_key, key_id = FacebookPasswordEncryptor.get_public_key()

        try:
            rand_key = get_random_bytes(32)
            iv = get_random_bytes(12)

            pubkey = RSA.import_key(public_key)
            cipher_rsa = PKCS1_v1_5.new(pubkey)
            encrypted_rand_key = cipher_rsa.encrypt(rand_key)

            cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
            current_time = int(time.time())
            cipher_aes.update(str(current_time).encode("utf-8"))
            encrypted_passwd, auth_tag = cipher_aes.encrypt_and_digest(password.encode("utf-8"))

            buf = io.BytesIO()
            buf.write(bytes([1, int(key_id)]))
            buf.write(iv)
            buf.write(struct.pack("<h", len(encrypted_rand_key)))
            buf.write(encrypted_rand_key)
            buf.write(auth_tag)
            buf.write(encrypted_passwd)

            encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"#PWD_FB4A:2:{current_time}:{encoded}"
        except Exception as e:
            raise Exception(f"Encryption error: {e}")


class FacebookAppTokens:
    APPS = {
        'FB_ANDROID': {'name': 'Facebook For Android', 'app_id': '350685531728'},
        'MESSENGER_ANDROID': {'name': 'Facebook Messenger For Android', 'app_id': '256002347743983'},
        'FB_LITE': {'name': 'Facebook For Lite', 'app_id': '275254692598279'},
        'MESSENGER_LITE': {'name': 'Facebook Messenger For Lite', 'app_id': '200424423651082'},
        'ADS_MANAGER_ANDROID': {'name': 'Ads Manager App For Android', 'app_id': '438142079694454'},
        'PAGES_MANAGER_ANDROID': {'name': 'Pages Manager For Android', 'app_id': '121876164619130'}
    }

    @staticmethod
    def get_app_id(app_key):
        app = FacebookAppTokens.APPS.get(app_key)
        return app['app_id'] if app else None

    @staticmethod
    def get_all_app_keys():
        return list(FacebookAppTokens.APPS.keys())

    @staticmethod
    def extract_token_prefix(token):
        for i, char in enumerate(token):
            if char.islower():
                return token[:i]
        return token


class FacebookLogin:
    API_URL = "https://b-graph.facebook.com/auth/login"
    ACCESS_TOKEN = "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    API_KEY = "882a8490361da98702bf97a021ddc14d"
    SIG = "214049b9f17c38bd767de53752b53946"

    BASE_HEADERS = {
        "content-type": "application/x-www-form-urlencoded",
        "x-fb-net-hni": "45201",
        "zero-rated": "0",
        "x-fb-sim-hni": "45201",
        "x-fb-connection-quality": "EXCELLENT",
        "x-fb-friendly-name": "authenticate",
        "x-fb-connection-bandwidth": "78032897",
        "x-tigon-is-retry": "False",
        "authorization": "OAuth null",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "3342",
        "priority": "u=3,i",
        "x-fb-http-engine": "Liger",
        "x-fb-client-ip": "True",
        "x-fb-server-cluster": "True"
    }

    def __init__(self, uid_phone_mail, password, machine_id=None,
                 convert_token_to=None, convert_all_tokens=False,
                 session=None, test_mode=False):
        """
        test_mode: if True, simulate a successful login for development/testing.
        """
        self.uid_phone_mail = uid_phone_mail
        self.test_mode = bool(test_mode)

        # If not already an encrypted token, attempt to encrypt (may raise)
        if password.startswith("#PWD_FB4A"):
            self.password = password
        else:
            # if test_mode and encryption deps are missing, skip encrypt
            if self.test_mode and (AES is None or RSA is None):
                self.password = password  # will not be sent in test mode
            else:
                try:
                    self.password = FacebookPasswordEncryptor.encrypt(password)
                except Exception as e:
                    # For real runs, propagate; for test_mode, allow plain password
                    if self.test_mode:
                        self.password = password
                    else:
                        raise

        if convert_all_tokens:
            self.convert_token_to = FacebookAppTokens.get_all_app_keys()
        elif convert_token_to:
            self.convert_token_to = convert_token_to if isinstance(convert_token_to, list) else [convert_token_to]
        else:
            self.convert_token_to = []

        self.session = session or requests.Session()

        self.device_id = str(uuid.uuid4())
        self.adid = str(uuid.uuid4())
        self.secure_family_device_id = str(uuid.uuid4())
        self.machine_id = machine_id if machine_id else self._generate_machine_id()
        self.jazoest = ''.join(random.choices(string.digits, k=5))
        self.sim_serial = ''.join(random.choices(string.digits, k=20))

        self.headers = self._build_headers()
        self.data = self._build_data()

    @staticmethod
    def _generate_machine_id():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=24))

    def _build_headers(self):
        headers = self.BASE_HEADERS.copy()
        headers.update({
            "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","retry_attempt":"0"},"application_tags":"unknown"}',
            "user-agent": "Dalvik/2.1.0 (Linux; U; Android 9; FBAN/FB4A)"
        })
        return headers

    def _build_data(self):
        base_data = {
            "format": "json",
            "email": self.uid_phone_mail,
            "password": self.password,
            "credentials_type": "password",
            "generate_session_cookies": "1",
            "locale": "vi_VN",
            "client_country_code": "VN",
            "api_key": self.API_KEY,
            "access_token": self.ACCESS_TOKEN
        }
        base_data.update({
            "adid": self.adid,
            "device_id": self.device_id,
            "generate_analytics_claim": "1",
            "community_id": "",
            "linked_guest_account_userid": "",
            "cpl": "true",
            "try_num": "1",
            "family_device_id": self.device_id,
            "secure_family_device_id": self.secure_family_device_id,
            "sim_serials": f'["{self.sim_serial}"]',
            "openid_flow": "android_login",
            "openid_provider": "google",
            "openid_tokens": "[]",
            "account_switcher_uids": f'["{self.uid_phone_mail}"]',
            "machine_id": self.machine_id,
            "jazoest": self.jazoest,
            "meta_inf_fbmeta": "V2_UNTAGGED",
            "advertiser_id": self.adid,
            "encrypted_msisdn": "",
            "currently_logged_in_userid": "0",
            "fb_api_req_friendly_name": "authenticate",
            "fb_api_caller_class": "Fb4aAuthHandler",
            "sig": self.SIG
        })
        return base_data

    def _convert_token(self, access_token, target_app):
        """
        Convert token to another app using auth.getSessionforApp.
        Returns dict or None on failure.
        """
        try:
            app_id = FacebookAppTokens.get_app_id(target_app)
            if not app_id:
                return None
            resp = self.session.post(
                'https://api.facebook.com/method/auth.getSessionforApp',
                data={
                    'access_token': access_token,
                    'format': 'json',
                    'new_app_id': app_id,
                    'generate_session_cookies': '1'
                },
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()
            if 'access_token' in result:
                token = result['access_token']
                prefix = FacebookAppTokens.extract_token_prefix(token)
                cookies_dict = {}
                cookies_string = ""
                if 'session_cookies' in result:
                    for cookie in result['session_cookies']:
                        cookies_dict[cookie['name']] = cookie['value']
                        cookies_string += f"{cookie['name']}={cookie['value']}; "
                return {
                    'token_prefix': prefix,
                    'access_token': token,
                    'cookies': {
                        'dict': cookies_dict,
                        'string': cookies_string.rstrip('; ')
                    }
                }
            return None
        except Exception:
            return None

    def _parse_success_response(self, response_json):
        original_token = response_json.get('access_token')
        original_prefix = FacebookAppTokens.extract_token_prefix(original_token) if original_token else ''
        result = {
            'success': True,
            'original_token': {
                'token_prefix': original_prefix,
                'access_token': original_token
            },
            'cookies': {}
        }

        if 'session_cookies' in response_json:
            cookies_dict = {}
            cookies_string = ""
            for cookie in response_json['session_cookies']:
                cookies_dict[cookie['name']] = cookie['value']
                cookies_string += f"{cookie['name']}={cookie['value']}; "
            result['cookies'] = {
                'dict': cookies_dict,
                'string': cookies_string.rstrip('; ')
            }

        if self.convert_token_to and original_token:
            result['converted_tokens'] = {}
            for target_app in self.convert_token_to:
                converted = self._convert_token(original_token, target_app)
                if converted:
                    result['converted_tokens'][target_app] = converted

        return result

    def login(self):
        """
        Attempt to login. If test_mode is True, simulate a success for development.
        Otherwise, perform a network request and return parsed result.
        """
        animated_print("[*] Attempting Straight Login...", color=CYAN)
        if self.test_mode:
            # NOTE: This is a SIMULATED success for development/testing only.
            simulated_token = "SIMULATEDTOKEN1234567890"
            res = {
                'success': True,
                'original_token': {
                    'token_prefix': 'SIM',
                    'access_token': simulated_token
                },
                'cookies': {
                    'dict': {'c_user': '1000', 'xs': 'simxs'},
                    'string': 'c_user=1000; xs=simxs'
                },
                'converted_tokens': {}
            }
            animated_print("[!] RUNNING IN TEST MODE — RESPONSE SIMULATED", color=YELLOW)
            return res

        try:
            resp = self.session.post(self.API_URL, headers=self.headers, data=self.data, timeout=15)
            resp.raise_for_status()
            response_json = resp.json()

            # Successful login
            if 'access_token' in response_json:
                return self._parse_success_response(response_json)

            # Known error structure from Facebook
            if 'error' in response_json:
                err = response_json['error']
                message = err.get('message') or err.get('error_user_msg') or str(err)
                # If message indicates verification required or checkpoint, return informative error
                return {
                    'success': False,
                    'error': message,
                    'error_user_msg': err.get('error_user_msg')
                }

            # Fallback unknown response
            return {'success': False, 'error': 'Unknown response format', 'raw': response_json}

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timed out'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {e}'}
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON response'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    clear_screen()
    show_logo()
    print(GREEN + "=" * 60)
    animated_print("  Facebook Login Tool (By NADEEM) - SAFE VERSION", color=YELLOW)
    print("=" * 60 + RESET)

    uid_phone_mail = input(GREEN + "Enter Email/Phone: " + RESET).strip()
    print(GREEN + "━" * 60 + RESET)
    password = input(GREEN + "Enter Password: " + RESET).strip()
    print(GREEN + "━" * 60 + RESET)

    # Toggle test_mode=True for local testing only (does not contact FB).
    fb_login = FacebookLogin(
        uid_phone_mail=uid_phone_mail,
        password=password,
        convert_all_tokens=True,
        test_mode=False
    )

    result = fb_login.login()

    if result.get('success'):
        print(GREEN + "\n" + "=" * 80)
        animated_print(" LOGIN SUCCESS ", color=GREEN)
        print("=" * 80)
        print(f"\n{YELLOW}TYPE: {RESET}{result['original_token'].get('token_prefix')}")
        print(f"{RED}{result['original_token'].get('access_token')}{RESET}")
        print(GREEN + "-" * 80 + RESET)

        if 'converted_tokens' in result and result['converted_tokens']:
            print(RED + "=" * 80)
            animated_print(" [ SCARY MODE ] ALL TOKENS GENERATED ", color=RED)
            print("=" * 80 + RESET)
            for app_key, token_data in result['converted_tokens'].items():
                print(f"\n{YELLOW}APP: {app_key} ({token_data.get('token_prefix')}){RESET}")
                print(f"{RED}{token_data.get('access_token')}{RESET}")
                print(GREEN + "-" * 80 + RESET)

        print("\n" + "=" * 80)
        animated_print(" COOKIES (NETSCAPE/JSON) ", color=CYAN)
        print("=" * 80)
        print(f"{YELLOW}{result['cookies'].get('string')}{RESET}")
        print(GREEN + "-" * 80 + RESET)

    else:
        print(RED + "\n" + "=" * 80)
        animated_print(" LOGIN FAILED ", color=RED)
        print("=" * 80)
        animated_print(f"Error: {result.get('error')}", color=YELLOW)
        if result.get('error_user_msg'):
            animated_print(f"Message: {result.get('error_user_msg')}", color=YELLOW)
        # Helpful guidance
        print()
        animated_print("Guidance:", color=CYAN)
        animated_print("- If Facebook requires verification, open https://www.facebook.com and resolve the checkpoint there.", color=CYAN)
        animated_print("- Do NOT attempt to bypass verification — use legitimate account recovery or Facebook's support.", color=CYAN)
        animated_print("- If you are developing, set test_mode=True to simulate successful login locally.", color=CYAN)
        print(RESET)


if __name__ == "__main__":
    main()
