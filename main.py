import pickle
from os import path
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains



IS_DEBUG = True

config = {
    'cookieFile': 'cookies.pkl',
    'loginUrl': 'https://login.taobao.com/',
    'targetUrl': 'https://chaoshi.detail.tmall.com/item.htm?from_scene=B2C&id=20739895092&spm=a3204.17725404.9886497900.1.79ab5885wTr7fH&skuId=4227830352490',
    'targetTime': '2023-07-03 22:30:00',
    'maxRetry': 3,
    'leadTime': 50, #ms
}


# def create_webdriver():
#     options = webdriver.ChromeOptions()

#     if not IS_DEBUG:
#         options.add_experimental_option("detach", True)
    
#     options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
#     options.add_argument('--disable-blink-features=AutomationControlled')
#     options.add_experimental_option(
#         'prefs',
#         {
#             'credientials_enable_service': False,
#             'profile.password_manager_enabled': False
#         }
#     )

#     wd = webdriver.Chrome(options=options)
#     stealth = open('stealth.min.js', encoding='utf-8').read()
#     wd.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
#                        'source': stealth})
#     wd.implicitly_wait(10)
#     wd.maximize_window()
    
#     return wd


# wd = create_webdriver()


# def main():
#     login()
#     wd.get(config['targetUrl'])
#     scheduler(config['targetTime'])

#     buy()

#     if IS_DEBUG:
#         wd.quit()



# def login():
#     wd.get(config['loginUrl'])

#     if path.exists(config['cookieFile']):
#         login_by_cookies()
#     else:
#         login_by_manual()


# def login_by_manual():
#     while True:
#         if wd.title == '我的淘宝':
#             break
    
#     pickle.dump(wd.get_cookies(), open(config['cookieFile'], 'wb'))


# def login_by_cookies():
#     for cookie in pickle.load(open(config['cookieFile'], 'rb')):
#         wd.add_cookie({
#             'domain': cookie['domain'],
#             'name': cookie['name'],
#             'value': cookie['value'],
#         })


# def buy(retry = config['maxRetry']):
#     if retry <= 0:
#         print('没有抢到，下次一定。')
#         return
    
#     buy_btn = wd.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div[1]/div/div[2]/div[7]/div[1]/button')
#     if 'Actions--disabled' in buy_btn.get_attribute('class'):
#         wd.refresh()
#         buy(retry - 1)
#     else:
#         buy_btn.click()
#         if not IS_DEBUG:
#             wd.find_element(By.CSS_SELECTOR, '.go-btn').click()
#         print('抢到了，付钱吧。')


def scheduler(time_str: str):
    now = datetime.now()
    target_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    wake_time = timedelta(minutes=0.8)
    
    if now >= target_time:
        print('开始抢购...')
    else:
        diff_time = target_time - now
        if diff_time > wake_time:
            print('还没到时间，等待中...')
            time.sleep((wake_time).total_seconds())





if __name__ == '__main__':
    # main()
    scheduler('2023-07-03 16:59:00')