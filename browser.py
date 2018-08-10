from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import json
from urllib.parse import urlparse, parse_qs
import time
from selenium.common.exceptions import TimeoutException
class Browser:

    def __init__(self, chromedriverPath, browsermobPath, harfilePath, cookies=None):
        self.harfilePath = harfilePath
        self.server = Server(browsermobPath)
        self.server.start()
        self.proxy = self.server.create_proxy()

        os.environ["webdriver.chrome.driver"] = chromedriverPath
        url = urlparse (self.proxy.proxy).path
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--proxy-server={0}".format(url))
        
        self.driver = webdriver.Chrome(chromedriverPath,chrome_options =chrome_options)
        if cookies:
            print("Loading cookies from "+str(cookies))
            with open(cookies, 'r') as cookieFile:
                cookieJson = json.loads(cookieFile.read())
            for cookie in cookieJson:
                self.driver.add_cookie(cookie)

    def get(self, url, timeout=20):
        self.proxy.new_har(url, {"captureContent":True})
        try:
            self.driver.set_page_load_timeout(timeout)
            self.driver.get(url)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5);")
            time.sleep(2) #wait for the page to load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(2) #wait for the page to load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2) #wait for the page to load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2) #wait for the page to load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4) #wait for the page to load
        except TimeoutException:
            print("Timeout")
            self.driver.find_element_by_tag_name("body").send_keys(Keys.CONTROL+Keys.ESCAPE)

        try:
            source = self.driver.page_source
            result = json.dumps(self.proxy.har, ensure_ascii=False)
            with open(self.harfilePath+"/"+str(int(time.time()*1000.0))+".har", "w") as harfile:
                harfile.write(result)
            return source
        except TimeoutException:
            print("Retrying, with a timeout of "+str(timeout+5))
            return self.get(url, timeout=timeout+5)

    def close(self):
        try:
            self.server.stop()
        except Exception:
            print("Warning: Error stopping server")
            pass
        try:
            self.driver.quit()
        except Exception:
            print("Warning: Error stopping driver")
            pass