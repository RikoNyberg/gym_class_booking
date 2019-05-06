###
# Script for inserting or pre-scheduling gym class reservations
###

from credentials import MONGO_URL
from pymongo import MongoClient
import datetime


dates = [
	'2019-03-27',
	'2019-04-03',
	'2019-04-10',
	'2019-04-17',
	'2019-04-24',
	'2019-05-01',
	'2019-05-08',
	'2019-05-15',
	]


classes = []
for date in dates:
	classes.append({
		"_id" : "Power Jooga {} 20:35:00".format(date),
		"class_name" : "Power Jooga",
		"instructor" : "Kirsi K.",
		"capacity" : "28",
		"capacity_free" : "21",
		"queue" : "0",
		"start_time" : datetime.datetime.strptime("{}T20:35:00Z".format(date), "%Y-%m-%dT%H:%M:%SZ"),
		"end_time" : datetime.datetime.strptime("{}T21:30:00Z".format(date), "%Y-%m-%dT%H:%M:%SZ"),
		"register_members" : [
			"300961218",
			"300230180"
		],
	})

print(classes)


MongoClient(MONGO_URL).gym.reservations.insert_many(classes)