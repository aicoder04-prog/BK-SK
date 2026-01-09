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
import threading

# ==========================================
# COLORS AND STYLING
# ==========================================
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

COLOR_LIST = [RED, GREEN, YELLOW, BLUE, CYAN]
CURRENT_COLOR = GREEN

def color_shifter():
    """Background thread to change the global color every 2 seconds."""
    global CURRENT_COLOR
    while True:
        CURRENT_COLOR = random.choice(COLOR_LIST)
        time.sleep(2)

# Start color shifter thread
threading.Thread(target=color_shifter, daemon=True).start()

def animated_print(text, delay=0.01, color=None):
    """Prints text with a typewriter animation effect."""
    use_color = color if color else CURRENT_COLOR
    for char in text:
        sys.stdout.write(use_color + char + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_animation(duration=3):
    """Displays a professional loading animation."""
    chars = ["⠙", "⠘", "⠰", "⠴", "⠤", "⠦", "⠆", "⠃", "⠋", "⠉"]
    end_time = time.time() + duration
    while time.time() < end_time:
        for char in chars:
            sys.stdout.write(f"\r{CURRENT_COLOR}[{char}] {BOLD}PLEASE WAIT... FETCHING PROFILE DATA{RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write("\r" + " " * 50 + "\r")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_logo():
    logo_lines = [
            "     ███╗   ██╗ █████╗ ██████╗ ███████╗███████╗███╗   ███╗",
            "     ████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║",
            "     ██╔██╗ ██║███████║██║  ██║█████╗  █████╗  ██╔████╔██║",
            "     ██║╚██╗██║██╔══██║██║  ██║██╔══╝  ██╔══╝  ██║╚██╔╝██║",
            "     ██║ ╚████║██║  ██║██████╔╝███████╗███████╗██║ ╚═╝ ██║",
            "     ╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝",
            "                [ TOKEN GRENADE V7 TOOL v2.0 ]             "
    ]
    for line in logo_lines:
        print(CURRENT_COLOR + BOLD + line + RESET)
        time.sleep(0.05)
    print(CURRENT_COLOR + "═" * 70 + RESET)

# ==========================================
# CORE CLASSES (Preserved)
# ==========================================

class FacebookPasswordEncryptor:
    @staticmethod
    def get_public_key():
        try:
            url = 'https://b-graph.facebook.com/pwd_key_fetch'
            params = {
                'version': '2', 'flow': 'CONTROLLER_INITIALIZATION', 'method': 'GET',
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
        'CONVO_TOKEN V7': {'name': 'Facebook Messenger For Android', 'app_id': '256002347743983'},
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
            if char.islower(): return token[:i]
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
    
    def __init__(self, uid_phone_mail, password, convert_all_tokens=False):
        self.uid_phone_mail = uid_phone_mail
        self.password = password if password.startswith("#PWD_FB4A") else FacebookPasswordEncryptor.encrypt(password)
        self.convert_token_to = FacebookAppTokens.get_all_app_keys() if convert_all_tokens else []
        self.session = requests.Session()
        self.device_id = str(uuid.uuid4())
        self.adid = str(uuid.uuid4())
        self.sim_serial = ''.join(random.choices(string.digits, k=20))
        self.headers = self._build_headers()
        self.data = self._build_data()

    def _build_headers(self):
        h = self.BASE_HEADERS.copy()
        h["user-agent"] = "Dalvik/2.1.0 (Linux; U; Android 9; 23113RKC6C Build/PQ3A.190705.08211809) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/vi_VN;FBBV/480086274;FBCR/MobiFone;FBMF/Redmi;FBBD/Redmi;FBDV/23113RKC6C;FBSV/9;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=1280,height=720};FB_FW/1;FBRV/0;]"
        return h

    def _build_data(self):
        return {
            "format": "json", "email": self.uid_phone_mail, "password": self.password,
            "credentials_type": "password", "generate_session_cookies": "1",
            "locale": "vi_VN", "client_country_code": "VN", "api_key": self.API_KEY,
            "access_token": self.ACCESS_TOKEN, "adid": self.adid, "device_id": self.device_id,
            "generate_analytics_claim": "1", "fb_api_req_friendly_name": "authenticate",
            "fb_api_caller_class": "Fb4aAuthHandler", "sig": self.SIG
        }

    def get_profile_info(self, token):
        try:
            info = requests.get(f"https://graph.facebook.com/me?fields=name,picture.type(large)&access_token={token}").json()
            return info.get('name', 'N/A'), info.get('picture', {}).get('data', {}).get('url', 'N/A')
        except:
            return "N/A", "N/A"

    def login(self):
        try:
            animated_print("[*] LOGGING IN...", color=CURRENT_COLOR)
            loading_animation(2)
            response = self.session.post(self.API_URL, headers=self.headers, data=self.data).json()
            
            if 'access_token' in response:
                token = response['access_token']
                name, dp_url = self.get_profile_info(token)
                
                # Success UI
                print(CURRENT_COLOR + "═" * 70)
                animated_print(f" LOGIN SUCCESSFUL ✅", color=GREEN)
                print(CURRENT_COLOR + "═" * 70)
                animated_print(f" NAME: {name}", color=CYAN)
                animated_print(f" DP URL: {dp_url}", color=CYAN)
                print(CURRENT_COLOR + "═" * 70)
                
                results = {'success': True, 'name': name, 'dp': dp_url, 'token': token, 'cookies': ""}
                if 'session_cookies' in response:
                    results['cookies'] = "; ".join([f"{c['name']}={c['value']}" for c in response['session_cookies']])
                return results
            return {'success': False, 'error': response.get('error', {}).get('message', 'Unknown Error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ==========================================
# MAIN EXECUTION
# ==========================================
try:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Install pycryptodome first!")
    exit()

if __name__ == "__main__":
    clear_screen()
    show_logo()
    
    print(CURRENT_COLOR + "═" * 70)
    animated_print("  V7 TOKENS GRENADE CONVO USING 100 WORKING", color=YELLOW)
    print(CURRENT_COLOR + "═" * 70 + RESET)

    user = input(CURRENT_COLOR + "ENTER GMAIL/PHONE NUMBER➠ " + RESET).strip()
    print(CURRENT_COLOR + "═" * 70 + RESET)
    
    pw = input(CURRENT_COLOR + "ENTER PASSWORD➠ " + RESET).strip()
    print(CURRENT_COLOR + "═" * 70 + RESET)
    
    fb = FacebookLogin(user, pw, convert_all_tokens=True)
    res = fb.login()
    
    if res['success']:
        print(f"\n{YELLOW}ACCESS TOKEN: {RESET}")
        print(f"{GREEN}{res['token']}{RESET}")
        print(CURRENT_COLOR + "═" * 70 + RESET)
        
        print(f"\n{YELLOW}COOKIES: {RESET}")
        print(f"{CYAN}{res['cookies']}{RESET}")
        print(CURRENT_COLOR + "═" * 70 + RESET)
    else:
        print(RED + "\n" + "═" * 70)
        animated_print(f" LOGIN FAILED: {res['error']}", color=RED)
        print(CURRENT_COLOR + "═" * 70 + RESET)
