import time
import pickle
import requests
from os import path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains



IS_DEBUG = False
LOGIN_URL = 'https://login.taobao.com'
COOKIE_FILE = 'cookies.pkl'
COOKIE_EXPIRED_FILE = 'cookie_expired_time.pkl'

config = {
    'targetUrl': 'https://cart.taobao.com/cart.htm?from=btop', # 购物车地址
    'targetTime': '2023-07-17 20:00:00', # 抢购时间
    'maxRetry': 5, # 没抢到时的最大重试次数
    'leadTime': 1000, # 提前多少毫秒开始抢购
}

def get_taobao_timediff():
    taobao_time_url = 'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
    }
    local_time = datetime.now()
    taobao_time_stamp = requests.get(url=taobao_time_url, headers=headers).json()['data']['t']
    
    return local_time - datetime.fromtimestamp(int(taobao_time_stamp) / 1000)

taobao_timediff = get_taobao_timediff()

def log(msg):
    print(f'[{datetime.now() - taobao_timediff}] {msg}')


def find(by, value,timeout=10, poll_frequency=0.5):
    return WebDriverWait(wd, timeout=timeout, poll_frequency=poll_frequency).until(EC.presence_of_element_located((by, value)))


def create_webdriver():
    options = webdriver.ChromeOptions()

    if not IS_DEBUG:
        options.add_experimental_option("detach", True)
    
    # 更换等待策略为不等待浏览器加载完全就进行下一步操作
    options.page_load_strategy = 'eager' 

    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-images")
    options.add_argument("--disable-background-timer-throttling")
    options.add_experimental_option(
        'prefs',
        {
            'credientials_enable_service': False,
            'profile.password_manager_enabled': False
        }
    )

    wd = webdriver.Chrome(options=options)
    stealth = open('stealth.min.js', encoding='utf-8').read()
    wd.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                       'source': stealth})
    wd.maximize_window()
    
    return wd


def main():
    global wd

    wd = create_webdriver()

    login()

    wd.get(config['targetUrl'])
    
    scheduler()

    if IS_DEBUG:
        wd.quit()



def login():
    wd.get(LOGIN_URL)

    if path.exists(COOKIE_EXPIRED_FILE):
        cookie_expired_time = pickle.load(open(COOKIE_EXPIRED_FILE, 'rb'))

    if path.exists(COOKIE_FILE) and cookie_expired_time and datetime.now() < cookie_expired_time:
        login_by_cookies()
    else:
        login_by_manual()
    log('登录成功...')


def login_by_manual():
    find(By.CSS_SELECTOR, '.icon-qrcode').click()
    log('请手动登录...')
    while True:
        if not LOGIN_URL in wd.current_url:
            break
    
    pickle.dump(wd.get_cookies(), open(COOKIE_FILE, 'wb'))
    set_cookie_expired_time()


def login_by_cookies():
    log('正在使用缓存登录...')
    for cookie in pickle.load(open(COOKIE_FILE, 'rb')):
        wd.add_cookie({
            'domain': cookie['domain'],
            'name': cookie['name'],
            'value': cookie['value'],
        })
    set_cookie_expired_time()
        

def set_cookie_expired_time():
    expired_time = datetime.now() + timedelta(minutes=15)
    pickle.dump(expired_time, open(COOKIE_EXPIRED_FILE, 'wb'))


def check_all_goods():
    try:
        check_all = find(By.XPATH, '//*[@id="J_SelectAll1"]')
    except NoSuchElementException:
        log('购物车空空如也，请添加商品后重新运行脚本...')
        wd.quit()
        return
    else:
        check_all.click()
        time.sleep(0.1)
        if 'selected' in check_all.get_attribute('class'):
            log('已勾选所有商品...')
        else:
            check_all_goods()
        
    
def pass_verify_silder():
    silder_box = find(By.CSS_SELECTOR, '#nc_1__scale_text')
    box_w = silder_box.rect['width']
    silder = find(By.CSS_SELECTOR, '#nc_1_n1z')
    silder_w = silder.rect['width']
    gap = box_w - silder_w
    maxTry = 5

    def _drop():
        nonlocal maxTry
        if maxTry == 0:
            log('请手动通过滑块校验...')
            while True:
                if not '拦截' in wd.title:
                    return
        
        silder = find(By.CSS_SELECTOR, '#nc_1_n1z')
        ActionChains(wd).click_and_hold(silder).perform()
        ActionChains(wd).move_by_offset(silder, gap - 50, 0).perform()
        time.sleep(0.1)
        ActionChains(wd).drag_and_drop_by_offset(silder, gap, 0).perform()
        
        try:
            err_box = find(By.CSS_SELECTOR, '.errloading')
        except (NoSuchElementException, TimeoutException):
            return
        else:
            err_box.click()
            maxTry -= 1
            _drop()
    
    _drop()

    


def settle():
    find(By.XPATH, '//a[@class="submit-btn"]').click()
    while True:
        if '拦截' in wd.title:
            pass_verify_silder()
            break
        
        elif 'confirm_order' in wd.current_url:
            log('进入订单确认页面...')
            break


def buy(max_retry=config['maxRetry']):
    if max_retry == 0:
        log('超过最大重试次数，抢购失败')
        return
    
    if '拦截' in wd.title:
        pass_verify_silder()
    
    try:
        sub_btn =  find(By.CSS_SELECTOR, '.go-btn', timeout=2, poll_frequency=0.1)
    except (NoSuchElementException, TimeoutException):
        time.sleep(0.1)
        log('未找到提交订单按钮，刷新重试...')
        wd.refresh()
        buy(max_retry - 1)
    else:
        log('提交订单...')
        if IS_DEBUG:
            return
        
        sub_btn.click()
        while True:
            if '支付宝' in wd.title:
                log('抢购成功，请及时支付订单...')
                break

            # 进到小二很忙
            if 'wait_pc' in wd.current_url:
                wd.back()
                buy()
                break

            # 已经没货了
            if 'OrderError' in wd.current_url:
                log('晚了一步，没有货啦...')
                break
    

def scheduler():
    target_time = datetime.strptime(config['targetTime'], '%Y-%m-%d %H:%M:%S') - taobao_timediff - timedelta(milliseconds=config['leadTime'])
    
    now = datetime.now()
    if now >= target_time:
        log('抢购时间已过，脚本退出...')
        return
    
    wake_up_time = 60 * 10
    diff = (target_time - now).total_seconds()
    log(f'距离抢购时间还有 {diff} 秒')
    
    if diff > wake_up_time:
        time.sleep(wake_up_time)
        wd.refresh()
        scheduler()
        set_cookie_expired_time()
        return
    
    check_all_goods()
    settle()
    log('等待抢购...')
    while True:
        if datetime.now() >= target_time:
            log('到抢购时间...')
            break
    wd.refresh()
    buy()
    set_cookie_expired_time()


if __name__ == '__main__':
    main()