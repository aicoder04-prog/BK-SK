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

# Scary/Stylish Colors
RED = "\033[91m"
GREEN = "\033[92m"
SCARY = "\033[38;5;196m" # Blood Red
SCARY_TOKEN = "\033[38;5;82m" # Neon Green
BOLD = "\033[1m"
RESET = "\033[0m"

def animated_print(text, delay=0.01, color=GREEN):
    """Prints text with a typewriter animation."""
    for char in text:
        sys.stdout.write(color + char + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def draw_line():
    print(BOLD + RED + "━" * 60 + RESET)

def clear_screen():
    sys.stdout.write("\x1b[2J\x1b[H")

def show_logo():
    """Flickering Animation for Logo"""
    logo_text = f"""
{BOLD}{SCARY}
  _   _    _    ____  _____ _____ __  __ 
 | \ | |  / \  |  _ \| ____| ____|  \/  |
 |  \| | / _ \ | | | |  _| |  _| | |\/| |
 | |\  |/ ___ \| |_| | |___| |___| |  | |
 |_| \_/_/   \_\____/|_____|_____|_|  |_|
{RESET}"""
    # Simple flicker effect
    for _ in range(3):
        clear_screen()
        time.sleep(0.1)
        print(logo_text)
        time.sleep(0.1)
        clear_screen()
        time.sleep(0.05)
    
    print(logo_text)
    animated_print("          [ SYSTEM INITIALIZED: BY NADEEM ]", 0.03, RED)
    draw_line()

# Crypto libraries check
try:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    print(f"{RED}Error: 'pycryptodome' module not found.{RESET}")
    print(f"{GREEN}Run: pip install pycryptodome{RESET}")
    exit()

class FacebookPasswordEncryptor:
    @staticmethod
    def get_public_key():
        try:
            url = 'https://b-graph.facebook.com/pwd_key_fetch'
            params = {
                'version': '2',
                'flow': 'CONTROLLER_INITIALIZATION',
                'method': 'GET',
                'fb_api_req_friendly_name': 'pwdKeyFetch',
                'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations',
                'access_token': '438142079694454|fc0a7caa49b192f64f6f5a6d9643bb28'
            }
            response = requests.post(url, params=params).json()
            return response.get('public_key'), str(response.get('key_id', '25'))
        except Exception as e:
            raise Exception(f"Public key fetch error: {e}")

    @staticmethod
    def encrypt(password, public_key=None, key_id="25"):
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
        "x-fb-net-hni": "45201", "zero-rated": "0", "x-fb-sim-hni": "45201",
        "x-fb-connection-quality": "EXCELLENT", "x-fb-friendly-name": "authenticate",
        "x-fb-connection-bandwidth": "78032897", "x-tigon-is-retry": "False",
        "authorization": "OAuth null", "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "3342", "priority": "u=3,i", "x-fb-http-engine": "Liger"
    }
    
    def __init__(self, uid_phone_mail, password, machine_id=None, convert_all_tokens=True):
        self.uid_phone_mail = uid_phone_mail
        self.password = password if password.startswith("#PWD_FB4A") else FacebookPasswordEncryptor.encrypt(password)
        self.convert_token_to = FacebookAppTokens.get_all_app_keys() if convert_all_tokens else []
        self.session = requests.Session()
        self.device_id = str(uuid.uuid4())
        self.machine_id = machine_id if machine_id else ''.join(random.choices(string.ascii_letters + string.digits, k=24))
        self.headers = self._build_headers()
        self.data = self._build_data()
    
    def _build_headers(self):
        headers = self.BASE_HEADERS.copy()
        headers["user-agent"] = "Dalvik/2.1.0 (Linux; U; Android 9; 23113RKC6C Build/PQ3A.190705.08211809) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/vi_VN;FBBV/480086274;FBCR/MobiFone;FBMF/Redmi;FBBD/Redmi;FBDV/23113RKC6C;FBSV/9;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=1280,height=720};FB_FW/1;FBRV/0;]"
        return headers
    
    def _build_data(self):
        return {
            "format": "json", "email": self.uid_phone_mail, "password": self.password,
            "credentials_type": "password", "generate_session_cookies": "1",
            "locale": "vi_VN", "client_country_code": "VN", "api_key": self.API_KEY,
            "access_token": self.ACCESS_TOKEN, "device_id": self.device_id, "sig": self.SIG
        }

    def _convert_token(self, access_token, target_app):
        try:
            app_id = FacebookAppTokens.get_app_id(target_app)
            response = requests.post('https://api.facebook.com/method/auth.getSessionforApp',
                data={'access_token': access_token, 'format': 'json', 'new_app_id': app_id, 'generate_session_cookies': '1'}).json()
            if 'access_token' in response:
                return response['access_token']
            return None
        except: return None

    def login(self):
        try:
            animated_print("[*] ACCESSING DATABASE...", 0.05, RED)
            response = self.session.post(self.API_URL, headers=self.headers, data=self.data).json()
            
            if 'access_token' in response:
                token = response['access_token']
                cookies = "".join([f"{c['name']}={c['value']}; " for c in response.get('session_cookies', [])])
                results = {'success': True, 'main_token': token, 'cookies': cookies, 'converted': {}}
                for app in self.convert_token_to:
                    conv = self._convert_token(token, app)
                    if conv: results['converted'][app] = conv
                return results
            
            if 'error' in response:
                error_data = response.get('error', {}).get('error_data', {})
                if 'login_first_factor' in error_data:
                    draw_line()
                    animated_print("[!] 2FA SECURITY ALERT DETECTED", 0.05, RED)
                    draw_line()
                    otp = input(f"{BOLD}{SCARY}[?] ENTER 2FA CODE: {RESET}").strip()
                    draw_line()
                    # (Simplified 2FA logic for speed)
                    return {'success': False, 'error': '2FA Required (Manual check needed)'}
                return {'success': False, 'error': response['error'].get('message')}
            return {'success': False, 'error': 'Connection Failed'}
        except Exception as e: return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    show_logo()
    
    # User Inputs with Lines
    u_mail = input(f"{BOLD}{GREEN}[+] UID/PHONE: {RESET}").strip()
    draw_line()
    u_pass = input(f"{BOLD}{GREEN}[+] PASSWORD:  {RESET}").strip()
    draw_line()
    
    fb = FacebookLogin(u_mail, u_pass)
    res = fb.login()
    
    if res['success']:
        print(f"\n{BOLD}{SCARY}[ SUCCESSFUL INTRUSION ]{RESET}")
        draw_line()
        
        animated_print(f"[MAIN_TOKEN]:", 0.02, RED)
        print(f"{SCARY_TOKEN}{res['main_token']}{RESET}")
        draw_line()
        
        if res['converted']:
            animated_print("[CONVERTED_TOKENS]:", 0.02, RED)
            for app, tk in res['converted'].items():
                print(f"{BOLD}{GREEN}[{app}]{RESET} -> {SCARY_TOKEN}{tk}{RESET}")
                draw_line()
        
        animated_print("[SESSION_COOKIES]:", 0.02, RED)
        print(f"{GREEN}{res['cookies']}{RESET}")
        draw_line()
    else:
        print(f"\n{BOLD}{RED}[ ACCESS DENIED ]{RESET}")
        draw_line()
        animated_print(f"REASON: {res.get('error')}", 0.05, RED)
        draw_line()
