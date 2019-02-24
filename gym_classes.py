# -*- coding: utf-8 -*-
import time
import datetime
from pytz import timezone
import random
from crawler import Crawler
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import schedule
from credentials import MONGO_URL, USERNAME, PASSWORD
from pymongo import MongoClient, errors
import logging
logging.basicConfig(format='%(message)s', level=logging.WARNING)


class GymClasses():
    def __init__(self, username, password):
        self.tz = timezone('Europe/Helsinki')
        self.username = username
        self.password = password
        self.website = 'Fitness24seven'
        logging.warning('{} crawler started.'.format(self.website))
        self.crawler = Crawler()

        self.gym_classes_collection = MongoClient(
            MONGO_URL).gym.reservations
        self.classes_to_register = self.get_classes_to_register()
        self.registered_classes_count = 0
        self.new_classes_count = 0
        self.updated_classes_count = 0
        self.all_classes_count = 0

        self.sign_in()
        self.driver = self.open_gym_classes_website()

    def update_and_register_classes(self):
        gym_days = self.get_day_elements()
        for i in range(len(gym_days)):
            gym_day = self.get_day_elements()[i]  # website might be reloaded
            gym_day.click()
            self.rand_sleep()

            gym_classes = self.get_gym_class_elements()
            for j in range(len(gym_classes)):
                gym_class = self.get_gym_class(j)
                self.insert_one_gym_class_to_mongo(gym_class)
                self.register_to_class(gym_class, j)
                self.all_classes_count += 1
        self.quit_process()
        pass

    def get_classes_to_register(self):
        gym_classes_to_register = self.gym_classes_collection.find({
            'register_to_class': True,
            'registering_done': {
                '$ne': True
            },
            'start_time': {
                '$lte': (datetime.datetime.now(self.tz) + datetime.timedelta(days=2))
            }})
        return list(gym_classes_to_register)

    def get_gym_class(self, j):
        base_xpath = "//*[@class='schedule']/tbody/tr[starts-with(@class,'row')]/td[@class='{item}']"
        class_name = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListProduct '))[j].text
        instructor = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListPersonal'))[j].text
        capacity = self.driver.find_elements_by_xpath(base_xpath.format(
            item='groupActivityListNumberOfParticipants'))[j].text
        capacity_free = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListAvailable'))[j].text
        queue = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListWaitingListSize'))[j].text
        start_time = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListTime'))[j].text[:5]
        end_time = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListTime'))[j].text[-5:]

        date = self.get_the_date()
        start_time = datetime.datetime.strptime('{date} {time}'.format(
            date=date, time=start_time), '%d.%m.%Y %H:%M')
        end_time = datetime.datetime.strptime('{date} {time}'.format(
            date=date, time=end_time), '%d.%m.%Y %H:%M')

        gym_class = {
            '_id': '{} {}'.format(class_name, start_time),
            'class_name': class_name,
            'instructor': instructor,
            'capacity': capacity,
            'capacity_free': capacity_free,
            'queue': queue,
            'start_time': start_time,
            'end_time': end_time,
        }
        return gym_class

    def rand_sleep(self):
        min_sleep = 1.231
        max_sleep = 2.458
        time.sleep(random.uniform(min_sleep, max_sleep))

    def sign_in(self):
        driver = self.crawler.open_new_website(
            'https://boka.fitness24seven.com/brp/mesh/index.action?businessUnit=6381')
        self.rand_sleep()

        username_elem = driver.find_element_by_xpath(
            '''//*[@class='wwFormTable']/tbody/tr/td/input[@type='text']''')
        username_elem.send_keys(self.username)
        self.rand_sleep()

        password_elem = driver.find_element_by_xpath(
            '''//*[@class='wwFormTable']/tbody/tr/td/input[@type='password']''')
        password_elem.send_keys(self.password)
        self.rand_sleep()

        password_elem.send_keys(Keys.ENTER)
        self.rand_sleep()

    def open_gym_classes_website(self):
        driver = self.crawler.open_new_website(
            'https://boka.fitness24seven.com/brp/mesh/showGroupActivities.action')
        self.rand_sleep()
        return driver

    def get_day_elements(self):
        days = self.driver.find_elements_by_xpath(
            '''//*[@class='wwFormTable']/tbody/tr/td/a''')
        return days

    def get_the_date(self):
        date = self.driver.find_element_by_xpath(
            '''//*[@class='schedule']/tbody/tr[starts-with(@class,"date")]''').text[-10:]
        return date

    def get_gym_class_elements(self):
        gym_classes = self.driver.find_elements_by_xpath(
            '''//*[@class='schedule']/tbody/tr[starts-with(@class,"row")]''')
        return gym_classes

    def insert_one_gym_class_to_mongo(self, gym_class):
        try:
            self.gym_classes_collection.insert_one(gym_class)
            self.new_classes_count += 1
        except errors.DuplicateKeyError:
            same_info_in_class = self.gym_classes_collection.find({
                '_id': gym_class['_id'],
                'capacity_free': gym_class['capacity_free'],
                'queue': gym_class['queue'],
            })
            if not list(same_info_in_class):
                logging.warning
                self.gym_classes_collection.update(
                    {'_id': gym_class['_id']},
                    {'$set': {
                        'capacity_free': gym_class['capacity_free'],
                        'queue': gym_class['queue'],
                    }}
                )
                self.updated_classes_count += 1

    def register_to_class(self, gym_class, j):
        for class_to_register in self.classes_to_register:
            if class_to_register['_id'] == gym_class['_id']:
                book_class_buttons = self.driver.find_elements_by_xpath(
                    "//*[@class='schedule']/tbody/tr[starts-with(@class,'row')]/td[@class='{item}']/a".format(item='groupActivityListAction'))[j]
                if book_class_buttons:
                    if book_class_buttons[0].text[:7] != 'Peruuta':
                        book_class_buttons[0].click()
                        self.gym_classes_collection.update(
                            {'_id': class_to_register['_id']},
                            {'$set': {
                                'capacity_free': gym_class['capacity_free'],
                                'queue': gym_class['queue'],
                                'registering_done': True,
                            }}
                        )
                        self.registered_classes_count += 1
                        logging.warning(
                            'Registered to: {}'.format(gym_class['_id']))
                        break

    def quit_process(self):
        self.crawler.quit_driver(self.website)
        logging.warning('\n------ {} ------'.format(self.website))
        logging.warning('Registered classes: {}'.format(
            self.registered_classes_count))
        logging.warning('New classes: {}'.format(self.new_classes_count))
        logging.warning('Updated classes: {}'.format(
            self.updated_classes_count))
        logging.warning('All classes: {}'.format(self.all_classes_count))
        logging.warning('Timestamp: {}'.format(
            datetime.datetime.now(self.tz).strftime("%Y-%m-%d at %H:%M")))
        logging.warning('------------')


def register_to_classes(username, password):
    gym_classes_collection = MongoClient(MONGO_URL).gym.reservations
    gym_classes_to_register = gym_classes_collection.find({
        'register_to_class': True,
        'registering_done': {
            '$ne': True
        },
        'start_time': {
            '$lte': (datetime.datetime.now(timezone('Europe/Helsinki')) + datetime.timedelta(days=2))
        }})
    if list(gym_classes_to_register):
        gym_classes = GymClasses(username, password)
        gym_classes.update_and_register_classes()


def update_classes(username, password):
    gym_classes = GymClasses(username, password)
    gym_classes.update_and_register_classes()


for hour in range(7, 22):
    hour = hour - 2  # Because Finland is UTF-2
    hour = '0{}'.format(hour)[-2:]
    for minute in range(0, 60, 5):
        minute = '0{}'.format(minute)[-2:]
        time_format = "{}:{}".format(hour, minute)
        schedule.every().day.at(time_format).do(
            register_to_classes, USERNAME, PASSWORD)

schedule.every().day.at("05:00").do(update_classes, USERNAME, PASSWORD)

while True:
    schedule.run_pending()
    time.sleep(120)
