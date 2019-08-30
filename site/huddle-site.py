from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

import pymongo

from bson.objectid import ObjectId
from bson.json_util import dumps

import os
from datetime import datetime, timedelta

app = Flask(__name__)


CONNECT_STRING = "mongodb://huddle:huddlepass1@ds139427.mlab.com:39427/huddle"
connection = pymongo.MongoClient(CONNECT_STRING)
db = connection.huddle
announcements = db.announcements
PRESENT = datetime.today()

def createAnnouncement(desc,author,expDate):
    expires = datetime.strptime(expDate, '%Y-%m-%d')

    announcement = {
        'author': author ,
        'description': desc , 
        'expires': expires,
        'deleted': False
    }

    return announcement

@app.route('/')
def index(announce=None):
    return render_template(
        "index.html",

        announce = list(announcements.find({
       'expires': {
            '$gte': PRESENT
        },

        "deleted": False ,
        
       }))
    )

@app.route('/edit-announcement/<string:id>', methods=['POST'])
def edit_announcement(id):
    description = request.form.get('description')
    author = request.form.get('author')
    expiry_date= request.form.get('expires')
   

    announcement = createAnnouncement(description,author,expiry_date)

    announcements.find_one_and_update(
        
        {'_id': ObjectId(id)},
        { '$set' : announcement}
        )

    return redirect("/")


@app.route('/delete-announcement/<string:id>/')
def delete_announcement(id):
    announcements.find_one_and_update(
        
        {'_id': ObjectId(id)},
        { '$set' : {'deleted': True}}
        )
    return redirect("/")


@app.route('/add-announcement/', methods=['POST'])
def add_announcement():
    description = request.form.get('description')
    author = request.form.get('author')
    expiry_date= request.form.get('expires')
    expires = datetime.strptime(expiry_date, '%Y-%m-%d')

    announcement = {
        'author': author ,
        'description': description , 
        'expires': expires,
        'deleted': False
    }

    announcements.insert_one(announcement)

    return redirect("/")

@app.route("/announcements/")
def get_announcements():
    return dumps(announcements.find({
       'expires': {
            '$gte': PRESENT
        },

        "deleted": False ,
        
       }))

if __name__ == "__main__":
   
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)