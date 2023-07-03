import time
import pickle
import requests
from os import path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


IS_DEBUG = False
LOGIN_URL = 'https://login.taobao.com'
COOKIE_FILE = 'cookies.pkl'
COOKIE_EXPIRED_FILE = 'cookie_expired_time.pkl'

config = {
    'targetUrl': 'https://chaoshi.detail.tmall.com/item.htm?from_scene=B2C&id=20739895092&spm=a3204.17725404.9886497900.1.79ab5885wTr7fH&skuId=4227830352490',
    'targetTime': '2023-07-04 10:00:00',
    'maxRetry': 10,
    'leadTime': 50, #ms
}


def create_webdriver():
    options = webdriver.ChromeOptions()

    if not IS_DEBUG:
        options.add_experimental_option("detach", True)
    
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
    wd.implicitly_wait(10)
    wd.maximize_window()
    
    return wd


wd = create_webdriver()


def main():
    login()

    wd.get(config['targetUrl'])
    
    scheduler(config['targetTime'], buy)

    if IS_DEBUG:
        wd.quit()



def login():
    wd.get(LOGIN_URL)

    cookie_expired_time = pickle.load(open(COOKIE_EXPIRED_FILE, 'rb'))

    if path.exists(COOKIE_FILE) and datetime.now() < cookie_expired_time:
        login_by_cookies()
    else:
        login_by_manual()


def login_by_manual():
    while True:
        if wd.title == '我的淘宝':
            break
    
    pickle.dump(wd.get_cookies(), open(COOKIE_FILE, 'wb'))
    set_cookie_expired_time()


def login_by_cookies():
    for cookie in pickle.load(open(COOKIE_FILE, 'rb')):
        wd.add_cookie({
            'domain': cookie['domain'],
            'name': cookie['name'],
            'value': cookie['value'],
        })
        

def set_cookie_expired_time():
    expired_time = datetime.now() + timedelta(minutes=15)
    pickle.dump(expired_time, open(COOKIE_EXPIRED_FILE, 'wb'))


def buy(retry = config['maxRetry']):
    if retry <= 0:
        print('没有抢到，下次一定。')
        set_cookie_expired_time()
        return
    
    buy_btn = wd.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div[1]/div/div[2]/div[7]/div[1]/button')
    if 'Actions--disabled' in buy_btn.get_attribute('class'):
        print('没有抢到，再来一次。')
        wd.refresh()
        buy(retry - 1)
    else:
        buy_btn.click()
        if not IS_DEBUG:
            wd.find_element(By.CSS_SELECTOR, '.go-btn').click()
        print('抢到了，付钱吧。')
        set_cookie_expired_time()


def scheduler(time_str: str, fn):
    now = get_taobao_time()
    lead_time = timedelta(milliseconds=config['leadTime'])
    target_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S') - lead_time
    
    if now >= target_time:
        print('开始抢购...')
        fn()
    else:
        print('等待抢购...')
        time.sleep((target_time - now).total_seconds())
        print('开始抢购...')
        fn()



def get_taobao_time():
    taobao_time_url = 'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
    }
    taobao_time_stamp = requests.get(url=taobao_time_url, headers=headers).json()['data']['t']
    
    return datetime.fromtimestamp(int(taobao_time_stamp) / 1000)


if __name__ == '__main__':
    main()