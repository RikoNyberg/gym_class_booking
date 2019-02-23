import random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
# import os
# path = os.getcwd()


class Crawler(object):

    def __init__(self):
        self.open_new_driver()
        self.min_sleep = 1.231
        self.max_sleep = 2.458

    def open_new_driver(self):
        try:
            self.driver.close()  # Closing the previous driver
        except AttributeError:
            pass                # Passing if opening the first driver

        self.driver = webdriver.Remote(
            "http://127.0.0.1:4444/wd/hub", DesiredCapabilities.CHROME)
        # "host.docker.internal:4444/wd/hub", DesiredCapabilities.CHROME)

        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--incognito')
        # chrome_options.add_argument('--disable-browser-side-navigation')
        # chrome_path = '/{}/old/chromedriver'.format(path)
        # self.driver = webdriver.Chrome(
        #     chrome_path, chrome_options=chrome_options)

    def open_new_website(self, url):
        whaiting_time = 40
        self.driver.set_page_load_timeout(whaiting_time)
        try:
            self.driver.get(url)
            # Let the user actually see something!
            time.sleep(random.uniform(self.min_sleep, self.max_sleep))
        except TimeoutException:
            print('--------------')
            print("Website didn't load in {} sek.\nURL: {}".format(
                whaiting_time, url))
            print('Opening new WebDriver and reopening the website...')
            print('--------------')
            self.open_new_driver()
            self.open_new_website(url)

        return self.driver

    def quit_driver(self, website):
        self.driver.quit()
