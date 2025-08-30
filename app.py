import random
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os

# --- الإعدادات ---
# هام: ضع هنا رابط ملف البروكسيات الخاص بك (يجب أن يكون رابطًا مباشرًا لملف txt)
PROXY_URL = "https://github.com/0xfff0800/TikTok-Checker/blob/main/proxy.txt" 
# يمكنك استخدام هذا الرابط كمثال، أو استبداله برابطك الخاص

# --- تهيئة التطبيق ---
app = Flask(__name__)
proxies = []

# --- وظائف مساعدة ---

def load_proxies():
    """
    تقوم هذه الوظيفة بسحب قائمة البروكسيات من الرابط المحدد وتخزينها في الذاكرة.
    """
    global proxies
    try:
        print("-> Loading proxies...")
        response = requests.get(PROXY_URL, timeout=10)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            # إزالة أي أسطر فارغة
            proxies = [p.strip() for p in proxies if p.strip()]
            print(f"-> Successfully loaded {len(proxies)} proxies.")
        else:
            print(f"-> Failed to load proxies. Status code: {response.status_code}")
            proxies = []
    except Exception as e:
        print(f"-> An error occurred while loading proxies: {e}")
        proxies = []

def get_random_proxy():
    """
    تختار بروكسي عشوائي من القائمة.
    """
    if not proxies:
        return None
    proxy = random.choice(proxies)
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

def create_session():
    """
    تُنشئ جلسة طلبات مع إعدادات إعادة المحاولة.
    """
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def check_username_logic(username):
    """
    منطق الفحص الأساسي، مأخوذ من الكود الخاص بك مع تعديلات.
    """
    session = create_session()
    proxy_dict = get_random_proxy()
    
    if not proxy_dict:
        return {"status": "error", "message": "No proxies available"}

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    ]
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.tiktok.com/",
    }
    
    try:
        response = session.get(
            f"https://www.tiktok.com/@{username}",
            headers=headers,
            proxies=proxy_dict,
            timeout=15,
            stream=True
        )
        
        if response.status_code == 404:
            return {"status": "available", "username": username}
        
        if response.status_code == 200:
            # طريقة الفحص من الكود الأصلي
            if "statusCode\":10221" in response.text or "Couldn't find this account" in response.text:
                 return {"status": "available", "username": username}
            else:
                 return {"status": "taken", "username": username}
                 
        return {"status": "taken", "username": username}

    except requests.exceptions.RequestException as e:
        print(f"Request error for {username} with proxy {proxy_dict}: {e}")
        return {"status": "error", "message": "Proxy or network error"}

# --- نقطة النهاية (API Endpoint) ---

@app.route('/check', methods=['GET'])
def check_username_endpoint():
    username = request.args.get('username')
    if not username or len(username) < 3:
        return jsonify({"status": "error", "message": "Invalid username provided"}), 400
    
    result = check_username_logic(username)
    return jsonify(result)

# --- التشغيل ---
if __name__ == '__main__':
    load_proxies()
    # يتم تشغيل الخادم بواسطة Gunicorn في بيئة الإنتاج
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)