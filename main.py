import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from os import path
import pickle

IS_DEBUG = True

config = {
    'cookieFile': 'cookies.pkl',
    'loginUrl': 'https://login.taobao.com/',
    'targetUrl': 'https://chaoshi.detail.tmall.com/item.htm?from_scene=B2C&id=20739895092&spm=a3204.17725404.9886497900.1.79ab5885wTr7fH&skuId=4227830352490',
    'targetTime': '2023-07-02 22:30:00',
    'maxRetry': 3,
}

def create_webdriver():
    options = webdriver.ChromeOptions()

    if not IS_DEBUG:
        options.add_experimental_option("detach", True)
    
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_argument('--disable-blink-features=AutomationControlled')
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

    buy()
    wd.quit()



def login():
    wd.get(config['loginUrl'])

    if path.exists(config['cookieFile']):
        login_by_cookies()
    else:
        login_by_manual()


def login_by_manual():
    while True:
        if wd.title == '我的淘宝':
            break
    
    pickle.dump(wd.get_cookies(), open(config['cookieFile'], 'wb'))


def login_by_cookies():
    for cookie in pickle.load(open(config['cookieFile'], 'rb')):
        wd.add_cookie({
            'domain': cookie['domain'],
            'name': cookie['name'],
            'value': cookie['value'],
        })


def buy(retry = config['maxRetry']):
    if retry == 0:
        print('购买失败')
        return
    
    btn = wd.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div[1]/div/div[2]/div[7]/div[1]/button')
    if 'Actions--disabled' in btn.get_attribute('class'):
        time.sleep(0.5)
        buy(retry - 1)
    else:
        btn.click()


if __name__ == '__main__':
    main()