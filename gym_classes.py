# -*- coding: utf-8 -*-
import time
import datetime
# from pytz import timezone
import random
from crawler import Crawler
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import schedule
from google_calendar import GoogleCal
from credentials import credentials
from pymongo import MongoClient, errors
import logging
logging.basicConfig(format='%(message)s', level=logging.WARNING)

gym_users_collection = MongoClient(credentials.MONGO_URL).gym.users
gym_classes_collection = MongoClient(credentials.MONGO_URL).gym.reservations


def get_classes_to_register(membership_id=None):
    gym_classes = gym_classes_collection.find({
        'start_time': {
            '$gte': datetime.datetime.now(),
            '$lte': (datetime.datetime.now() + datetime.timedelta(days=2) + datetime.timedelta(hours=2))
        }
    })

    gym_classes_to_register = []
    gym_classes_to_unregister = []
    membership_ids = set()
    for gym_class in list(gym_classes):
        register_members_done = set(gym_class.get('register_members_done', []))
        register_members = set(gym_class.get('register_members', []))
        if register_members != register_members_done:
            membership_ids.update(
                register_members_done.symmetric_difference(register_members))
            if not membership_id:
                if register_members_done.issubset(register_members):
                    gym_classes_to_register.append(gym_class)
                elif register_members.issubset(register_members_done):
                    gym_classes_to_unregister.append(gym_class)
            else:
                if membership_id in register_members_done.symmetric_difference(register_members):
                    if register_members_done.issubset(register_members):
                        gym_classes_to_register.append(gym_class)
                    elif register_members.issubset(register_members_done):
                        gym_classes_to_unregister.append(gym_class)
    return gym_classes_to_register, gym_classes_to_unregister, membership_ids


class GymClasses():
    def __init__(self, username, password, email, name='Gym class update'):
        # self.tz = timezone('Europe/Helsinki')
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        self.website = 'Fitness24seven'
        logging.warning('\n{} crawler started.'.format(self.website))
        self.crawler = Crawler(logging)
        self.calendar = GoogleCal()

        self.gym_classes_collection = gym_classes_collection
        self.classes_to_register, self.classes_to_unregister, _ = get_classes_to_register(
            membership_id=self.username)
        self.registered_classes_count = 0
        self.unregistered_classes_count = 0
        self.new_classes_count = 0
        self.updated_classes_count = 0
        self.all_classes_count = 0

        self.sign_in()
        self.driver = self.open_gym_classes_website()

    def update_and_register_classes(self):
        if self.make_sure_that_username_and_password_are_correct():
            gym_days = self.get_day_elements()
            for i in range(len(gym_days)):
                gym_day = self.get_day_elements()[i]
                gym_day.click()
                self.rand_sleep()

                self.gym_classes_count = len(self.get_gym_class_elements())
                self.get_class_elems()
                for j in range(self.gym_classes_count):
                    gym_class = self.get_gym_class(j)
                    self.insert_one_gym_class_to_mongo(gym_class)
                    self.register_to_class(gym_class, j)
                    self.unregister_to_class(gym_class, j)
                    self.all_classes_count += 1
        self.quit_process()

    def make_sure_that_username_and_password_are_correct(self):
        logout_elem = self.driver.find_elements_by_xpath(
            '''//*[@id='logout']''')
        if not logout_elem:
            logging.error('User {} has wrong password.'.format(self.username))
            return False
        return True

    def get_class_elems(self):
        base_xpath = "//*[@class='schedule']/tbody/tr[starts-with(@class,'row')]/td[starts-with(@class, '{item}')]"
        self.class_names = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListProduct'))
        self.instructors = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListPersonal'))
        self.capacitys = self.driver.find_elements_by_xpath(base_xpath.format(
            item='groupActivityListNumberOfParticipants'))
        self.free_capacitys = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListAvailable'))
        self.queues = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListWaitingListSize'))
        self.clock_times = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListTime'))
        self.booking_buttons = self.driver.find_elements_by_xpath(
            base_xpath.format(item='groupActivityListAction'))

        self.check_that_element_counts_match(self.class_names, 'class_names')
        self.check_that_element_counts_match(self.instructors, 'instructors')
        self.check_that_element_counts_match(self.capacitys, 'capacitys')
        self.check_that_element_counts_match(
            self.free_capacitys, 'free_capacitys')
        self.check_that_element_counts_match(self.queues, 'queues')
        self.check_that_element_counts_match(self.clock_times, 'clock_times')
        self.check_that_element_counts_match(
            self.booking_buttons, 'booking_buttons')

    def check_that_element_counts_match(self, elem, elem_name):
        if len(elem) != self.gym_classes_count:
            logging.error(
                'ERROR: {} element count do not match with Gym Class count'.format(elem_name))

    def get_gym_class(self, j):
        class_name = self.class_names[j].text
        instructor = self.instructors[j].text
        capacity = self.capacitys[j].text
        free_capacity = self.free_capacitys[j].text
        queue = self.queues[j].text
        start_clock_time = self.clock_times[j].text[:5]
        end_clock_time = self.clock_times[j].text[-5:]

        date = self.get_the_date()
        start_time = datetime.datetime.strptime('{date} {time}'.format(
            date=date, time=start_clock_time), '%d.%m.%Y %H:%M')
        end_time = datetime.datetime.strptime('{date} {time}'.format(
            date=date, time=end_clock_time), '%d.%m.%Y %H:%M')

        gym_class = {
            '_id': '{} {}'.format(class_name, start_time),
            'class_name': class_name,
            'instructor': instructor,
            'capacity': capacity,
            'capacity_free': free_capacity,
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
                book_class_button_list = self.booking_buttons[j].find_elements_by_xpath('.//a')
                if len(book_class_button_list):
                    book_class_button = book_class_button_list[0]
                    if book_class_button.text[:7] == 'Peruuta':
                        logging.warning('#### Class already registered: {} ####'.format(
                            class_to_register['_id']))
                        pass
                    else:
                        logging.warning(
                            'Registering to class: {}'.format(gym_class['_id']))
                        book_class_button.click()
                        self.get_class_elems()  # Getting elems again because the page is refreshed
                    class_to_update = self.gym_classes_collection.find_one(
                        {'_id': class_to_register['_id']})
                    register_members_done_list = class_to_update.get(
                        'register_members_done', [])
                    register_members_done_list.append(self.username)
                    ### Google calendar ####
                    google_cal_event_id = class_to_update.get(
                        'google_cal_event_id', '')
                    if not google_cal_event_id:
                        class_name = class_to_update['class_name']
                        start_time = class_to_update['start_time']
                        end_time = class_to_update['end_time']
                        google_cal_event_id = self.calendar.add_event(class_name, start_time, end_time, email=self.email, accepted_attendee=True)
                    else:
                        self.calendar.add_attendee(google_cal_event_id, self.email, accepted_attendee=True)
                    ########################
                    self.gym_classes_collection.update(
                        {'_id': class_to_register['_id']},
                        {'$set': {
                            'capacity_free': gym_class['capacity_free'],
                            'queue': gym_class['queue'],
                            'register_members_done': register_members_done_list,
                            'google_cal_event_id': google_cal_event_id,
                        }})
                    self.registered_classes_count += 1
                else:
                    continue # Reservation is not possible yet since the book_class_button does not exit

    def unregister_to_class(self, gym_class, j):
        for class_to_unregister in self.classes_to_unregister:
            if class_to_unregister['_id'] == gym_class['_id']:
                book_class_button_list = self.booking_buttons[j].find_elements_by_xpath('.//a')
                if len(book_class_button_list):
                    book_class_button = book_class_button_list[0]
                    if book_class_button.text[:7] != 'Peruuta':
                        logging.warning('#### Class already un-registered: {} ####'.format(
                            class_to_unregister['_id']))
                        pass
                    else:
                        logging.warning(
                            'Un-registering to class: {}'.format(gym_class['_id']))
                        book_class_button.click()
                        alert = self.driver.switch_to.alert
                        alert.accept()
                        self.get_class_elems()  # Getting elems again because the page is refreshed
                    class_to_update = self.gym_classes_collection.find_one(
                        {'_id': class_to_unregister['_id']})
                    register_members_done_list = class_to_update.get(
                        'register_members_done', [])
                    register_members_done_list.remove(self.username)
                    ### Google calendar ####
                    google_cal_event_id = class_to_update.get(
                        'google_cal_event_id', '')
                    if google_cal_event_id:
                        self.calendar.remove_attendee(google_cal_event_id, self.email)
                    ########################
                    self.gym_classes_collection.update(
                        {'_id': class_to_unregister['_id']},
                        {'$set': {
                            'capacity_free': gym_class['capacity_free'],
                            'queue': gym_class['queue'],
                            'register_members_done': register_members_done_list,
                        }})
                    
                    self.unregistered_classes_count += 1
                else:
                    continue # Reservation is not possible yet since the book_class_button does not exit

    def quit_process(self):
        self.crawler.quit_driver(self.website)
        logging.warning('\n------ {} ------'.format(self.name))
        logging.warning('Registered classes: {}'.format(
            self.registered_classes_count))
        logging.warning('Un-registered classes: {}'.format(
            self.unregistered_classes_count))
        logging.warning('New classes: {}'.format(self.new_classes_count))
        logging.warning('Updated classes: {}'.format(
            self.updated_classes_count))
        logging.warning('All classes: {}'.format(self.all_classes_count))
        logging.warning('Timestamp: {}'.format(
            datetime.datetime.now().strftime("%Y-%m-%d at %H:%M")))
        logging.warning('------------')


def register_to_classes():
    r, u, membership_ids = get_classes_to_register()
    logging.warning('\n---- Registering to classes ----\n{}\n'.format(r))
    logging.warning('---- Un-registering to classes ----\n{}\n'.format(u))
    for membership_id in membership_ids:
        user = gym_users_collection.find_one({'_id': membership_id})
        if user:
            username = user['_id']
            password = user['password']
            email = user['email']
            name = user['name']
            gym_classes = GymClasses(
                username, password, email, name=name)
            gym_classes.update_and_register_classes()
            continue
        logging.warning(
            'Trying to book classes to member {} who is not a registered user'.format(membership_id))

def update_classes():
    user = gym_users_collection.find_one()
    username = user['_id']
    password = user['password']
    email = user['email']
    name = user['name']
    gym_classes = GymClasses(username, password, email, name='Gym class update + {}'.format(name))
    gym_classes.update_and_register_classes()


schedule.every().day.at("05:00").do(update_classes)
# schedule.every(1).seconds.do(register_to_classes)
schedule.every(5).minutes.do(register_to_classes)

while True:
    schedule.run_pending()
    time.sleep(120)
