from flask import Flask, request, Response, redirect, url_for
from DrissionPage import ChromiumPage, ChromiumOptions
import threading
import time

app = Flask(__name__)

browser_lock = threading.Lock()
page = None

def get_page():
    global page
    if page is None:
        co = ChromiumOptions()
        co.set_browser_path('/usr/bin/chromium')
        
        # === Docker 环境参数 ===
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')
        
        # === 伪装配置 ===
        co.set_argument('--headless=new') 
        co.set_user_agent(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        co.set_argument('--lang=zh-CN')
        co.set_argument('--window-size=1366,768')
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--blink-settings=imagesEnabled=false')
        
        co.set_local_port(9222)
        page = ChromiumPage(co)
    return page

def ensure_cf_pass(p):
    """过盾检测"""
    for i in range(20):
        try:
            title = p.title.lower()
            if "just a moment" not in title and "attention" not in title and "security" not in title and "cloudflare" not in title:
                if p.ready_state == 'complete':
                    return True
            if p.ele('@type=checkbox', timeout=0.5):
                p.ele('@type=checkbox').click()
            elif p.ele('@id=challenge-stage', timeout=0.5):
                stage = p.ele('@id=challenge-stage')
                if stage.shadow_root: stage.child().click()
        except:
            pass
        time.sleep(1)
    return False

@app.route('/proxy', methods=['GET', 'POST'])
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return "Missing URL parameter", 400

    global page
    with browser_lock:
        try:
            p = get_page()
            
            # 1. 确保在主页
            if "69shuba" not in p.url:
                p.get("https://www.69shuba.com/")
            
            ensure_cf_pass(p)

            # === 处理搜索 (POST) ===
            if request.method == 'POST':
                keyword = request.form.get('searchkey') or request.args.get('searchkey')
                print(f"Searching for: {keyword}", flush=True)

                if keyword:
                    # 尝试寻找搜索框
                    search_input = p.ele('css:input[name="searchkey"]', timeout=5) or p.ele('css:input.search-text')
                    
                    if search_input:
                        # 1. 填值
                        p.run_js(f'arguments[0].value = "{keyword}";', search_input)
                        
                        # 2. 强行提交 (修复 name="submit" 冲突问题)
                        # 使用原型链方法直接调用 submit，避开按钮命名冲突
                        p.run_js('HTMLFormElement.prototype.submit.call(arguments[0].form);', search_input)
                        
                        # 等待结果
                        time.sleep(2) 
                        ensure_cf_pass(p)
                        print(f"Search Result Page Title: {p.title}", flush=True)
                    else:
                        print("Error: Search input not found", flush=True)
                        p.get(target_url)
                else:
                    p.get(target_url)

            # === 处理 GET ===
            else:
                p.get(target_url)

            ensure_cf_pass(p)
            html = p.html
            return Response(html, mimetype='text/html')

        except Exception as e:
            print(f"Error: {e}", flush=True)
            try:
                if page: page.quit()
            except: pass
            page = None
            return f"Proxy Error: {str(e)}", 500

# === 新增代码：捕获所有其他路径，自动重定向回 proxy ===
@app.route('/<path:subpath>', methods=['GET', 'POST'])
def catch_all(subpath):
    # 拼接原始目标网址，假设你是针对 69shuba 的
    target_url = f"https://www.69shuba.com/{subpath}"
    
    # 如果原本带有 URL 参数 (比如 ?page=2)，也补上
    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"
        
    # 重定向回 /proxy 接口处理
    return redirect(url_for('proxy', url=target_url))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
