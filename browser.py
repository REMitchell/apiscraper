from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import json
from urllib.parse import urlparse, parse_qs
import time

class Browser:

    def __init__(self, chromedriverPath, browsermobPath, harfilePath):
        self.harfilePath = harfilePath
        self.server = Server(browsermobPath)
        self.server.start()
        self.proxy = self.server.create_proxy()

        os.environ["webdriver.chrome.driver"] = chromedriverPath
        url = urlparse (self.proxy.proxy).path
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--proxy-server={0}".format(url))
        
        self.driver = webdriver.Chrome(chromedriverPath,chrome_options =chrome_options)

    def get(self, url):
        print(url)
        self.proxy.new_har(url, {"captureContent":True})
        try:
            self.driver.set_page_load_timeout(20)
            self.driver.get(url)
        except Exception:
            print("Timeout")
            self.driver.find_element_by_tag_name("body").send_keys(Keys.CONTROL+Keys.ESCAPE)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5);")
        time.sleep(.5) #wait for the page to load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
        time.sleep(.5) #wait for the page to load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(.5) #wait for the page to load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(.5) #wait for the page to load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4) #wait for the page to load
        
        result = json.dumps(self.proxy.har, ensure_ascii=False)
        with open(self.harfilePath+"/"+str(int(time.time()*1000.0))+".har", "w") as harfile:
            harfile.write(result)

        return self.driver.page_source

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