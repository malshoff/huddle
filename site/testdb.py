from flask import Flask
from flask import render_template
from flask import request
import pymongo
from datetime import datetime, timedelta
from pprint import pprint
from bson.objectid import ObjectId


CONNECT_STRING = "mongodb://huddle:huddlepass1@ds139427.mlab.com:39427/huddle"
connection = pymongo.MongoClient(CONNECT_STRING)
db = connection.huddle
announcements = db.announcements
present = datetime.today()
presentDate = present.date()
#print(presentDate)
#all = announcements.find_one()
#pprint(all)
'''print("after all")
announce = announcements.find({
       'expires': {
            '$gte': present
        }
       })
print("after announce")
for i in announce:
    print(i)
#for a in announce:
 #       print(a)

'''
pprint(announcements.find_one({'_id': ObjectId('5d0931c8d9308ec63f132885')}))

#pprint(announcements.find_one())

#http://0.0.0.0:5000/delete-announcement/5d0931c8d9308ec63f132885