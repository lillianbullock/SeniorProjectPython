
# "/Users/brookebullock/Movies/Ferngully.m4v"

# https://stackoverflow.com/questions/44621359/python-cant-serve-mp4-to-browser
# localhost:5000/Ferngully.m4v

import os
from flask import Flask, send_file, make_response, Response, request
import requests
import json
from pymongo import MongoClient
import datetime
import re

# TODO change from all access to whitelisting
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# https://towardsdatascience.com/how-to-hide-your-api-keys-in-python-fb2e1a61b0a0
# stored in ./etc/conda/activate.d/env_vars.sh and ./etc/conda/deactivate.d/env_vars.sh
f = open("keys/OMDB.txt","r")
OMDB_KEY = f.read()
f.close()

# login_manager = LoginManager()

MEDIA_PATH = '/Users/brookebullock/Movies'

@app.route('/')
def hello():
    return "hello world"

@app.route('/video/<vid_name>', methods=["GET"])
def serve_video(vid_name):
    vid_path = os.path.join(MEDIA_PATH, vid_name)
    resp = make_response(send_file(vid_path, 'video/mp4'))
    resp.headers['Content-Disposition'] = 'inline'
    return resp

@app.route('/search', methods=["GET"])
def search():
    title = request.args.get('title', None)
    year = request.args.get('year', None)
    imdbID  = request.args.get('id', None)

    print(OMDB_KEY)
    print()

    url = f"http://www.omdbapi.com/?apikey={OMDB_KEY}"

    err = None

    if imdbID != None:
        if valid_imdb_id(imdbID):
            url += f"&i={imdbID}"
        else:
            err = "Invalid IMDB id"
    elif title != None:
        url += f"&t={title}"

        if year != None:
            if year.isnumeric():
                url += f"&y={year}"
            else:
                err = "Year is not a number"
    else:
        err = "no arguments given"

    if err != None:
        #malformed arguments
        return Response(
            response=f"400: {err}",
            status=400
        ) 

    omdb_response = requests.get(url)
    
    obj = omdb_response.json()

    # print("Title:" , obj["Title"])
    # print("Rating:" , obj["Rated"])
    # print("Length:" , obj["Runtime"])
    # print("Summary:" , obj["Plot"])
    # print("Released:" , obj["Released"])
    # print("ID:" , obj["imdbID"])
    # print("Poster:", obj["Poster"])

    # print(json.dumps(obj))

    if omdb_response.status_code == 200:
        return Response(
            mimetype="application/json",
            response=json.dumps(obj),
            status=200
        )  
    else:
        return Response(
            response="404: not found",
            status=404
        ) 

@app.route('/write_json', methods=["POST"])
def write_to_mongo():

    obj = json.loads(request.data) #get the sent object

    #connect to the mongo client
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    db = client.senior_project

    #remove extraneous data from the obj
    cleaned_obj = {
        "imdbID" :      obj["imdbID"],
        "Title" :       obj["Title"],
        "SearchTitle" : search_string(obj["Title"]),
        "Year" :        obj["Year"],
        "Released" :    obj["Released"],
        "Runtime" :     obj["Runtime"],
        "Rated" :       obj["Rated"],
        "Plot" :        obj["Plot"],
        "Poster" :      obj["Poster"],
        "Type" :        obj["Type"],
        #"Path"  :        MEDIA_PATH + relative-path
        "Genre" :       obj["Genre"],
        "Production" :  obj["Production"],
        "Ratings" :     obj["Ratings"],
        "DateAdded" :   datetime.datetime.utcnow(),
        "LastChanged" : datetime.datetime.utcnow(), #allow for an update endpoint to exist
    }   

    if (db.movies.find_one({'imdbID': obj["imdbID"]})):
        db_response = db.movies.update_one({'imdbID': obj["imdbID"]}, {"$set": cleaned_obj })
    else:
        db_response = db.movies.insert_one(cleaned_obj)

    client.close()

    if db_response.acknowledged:
        response = Response(
            response='201: obj written',
            status=201
        )  
    else:
        response = Response(
            response="500: write failed",
            status=500
        ) 

    return response

@app.route('/browse')
def browse():

    title = request.args.get('title', None)
    year = request.args.get('year', None)
    imdb_id = request.args.get('id', None)
    rating = request.args.get('rating', None)

    find_key = []

    err = None #if problem with search terms change value

    # either imdb_id OR title is required, if title; rating and year can also be added
    if imdb_id != None:
        if valid_imdb_id(imdb_id):
            #https://regex101.com/r/ImE8BV/1/ - regex testing site
            find_key.append({'imdbID': imdb_id})
        else: 
            err = "Invalid imdb ID"
    elif title != None:
        find_key.append({'SearchTitle': { '$regex': title}})
        
        if year != None:
            if not year.isnumeric():
                err = "Year must be a valid number"
            find_key.append({'Year' : year})

        if rating != None: 
            find_key.append({'Rated' : rating.upper()})
    else: 
        find_key.append({}) # recently added 

    # If there is an error value, no query to DB, just exit here
    if err != None: 
        return Response(
            response=("500: " + err),
            status=404
        ) 

    # TODO add sorting/numResults possibilities?
    sort_field = "DateAdded"
    sort_dir = -1
    display_key = { "_id": 0, "DateAdded": 0, "LastChanged": 0 } #dates don't parse to JSON TODO figure this out?

    #connect to the mongo client
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    db = client.senior_project

    obj = db.movies.find({'$and':find_key}, display_key).sort(sort_field, sort_dir).limit(10) 

    client.close()

    if obj:
        retObj = []
        for x in obj:
            retObj.append(x)

        return Response(
            mimetype="application/json",
            response=json.dumps(retObj),
            status=200,
        )
    else:
        return Response(
            status=404,
        )

@app.route('/query_json/<imdbID>')
def read_from_mongo(imdbID):

    #connect to the mongo client
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    db = client.senior_project

    obj = db.movies.find_one({'imdbID': imdbID}, { "_id": 0, "DateAdded": 0, "LastChanged": 0 })

    client.close()

    if obj:
        return Response(
            mimetype="application/json",
            response=json.dumps(obj),
            status=200
        )
    else:
        return Response(
            status=404
        )



''' this function is to create a lowercase space-less version of the title for easier searching
Will also be used on the search terms to normalize them'''
def search_string(title):
    alphanum = ""

    for character in title:
        if character.isalnum():
            alphanum += character.lower()
    return alphanum

'''
Wrapper function around this operation, in case it needs to change in the future
https://regex101.com/r/ImE8BV/1/ - regex testing site
'''
def valid_imdb_id(id):
    return re.match('tt\d{7}', id)


if __name__ == '__main__':
    app.run()