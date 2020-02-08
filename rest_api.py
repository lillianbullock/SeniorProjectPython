
# "/Users/brookebullock/Movies/Ferngully.m4v"

# https://stackoverflow.com/questions/44621359/python-cant-serve-mp4-to-browser
# localhost:5000/Ferngully.m4v

import os
from flask import Flask, send_file, make_response, Response, request
import requests
import json
from pymongo import MongoClient
import datetime

# TODO change from all access to whitelisting
from flask import Flask
from flask_cors import CORS

APP = Flask(__name__)
CORS(APP)

MEDIA_PATH = '/Users/brookebullock/Movies'

@APP.route('/')
def hello():
    return "hello world"

@APP.route('/video/<vid_name>', methods=["GET"])
def serve_video(vid_name):
    vid_path = os.path.join(MEDIA_PATH, vid_name)
    resp = make_response(send_file(vid_path, 'video/mp4'))
    resp.headers['Content-Disposition'] = 'inline'
    return resp

@APP.route('/search', methods=["GET"])
def search():
    title = request.args.get('title', None)
    year = request.args.get('year', None)
    imdbID  = request.args.get('id', None)

    print(f"{title}  {year}  {imdbID}")

    url = "http://www.omdbapi.com/?apikey=1e93b34f"

    if imdbID != None:
        # TODO check form of ID (regular expression??)
        url += f"&i={imdbID}"
    elif title != None:
        url += f"&t={title}"
        if imdbID != None:
            # TODO check this is number
            url += f"&y={year}"
    else:
        # they didn't give us the data, so they get nothing back
        return Response(
            response="400: no arguments given",
            status=400
        ) 

    omdb_response = requests.get(url)
    print(omdb_response.status_code)
    print()

    obj = omdb_response.json()

    print("Title:" , obj["Title"])
    #print("Rating:" , obj["Rated"])
    #print("Length:" , obj["Runtime"])
    #print("Summary:" , obj["Plot"])
    #print("Released:" , obj["Released"])
    print("ID:" , obj["imdbID"])
    #print("Poster:", obj["Poster"])

    print(json.dumps(obj))

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

@APP.route('/write_json', methods=["POST"])
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
        "LastChanged" :   datetime.datetime.utcnow(), #allow for an update endpoint to exist
    }   

    if (db.movies.find_one({'imdbID': obj["imdbID"]})):
        print("found")
        db_response = db.movies.update_one({'imdbID': obj["imdbID"]}, {"$set": cleaned_obj })
    else:
        print("not_found")
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

@APP.route('/browse')
def browse():

    title = "Fern" #request.args.get('title', None)
    year = request.args.get('year', None)
    imdbID = request.args.get('id', None)
    rating = request.args.get('rating', None)

    find_key = { }


    if title != None:
        # TODO check form of ID (regular expression??)
        t_regex = f'(.*){title}(.*)' #match anything before or after string
    # elif title != None:
    #     url += f"&t={title}"
    #     if imdbID != None:
    #         # TODO check this is number
    #         url += f"&y={year}"
    # else:
    #     # they didn't give us the data, so they get nothing back
    #     return Response(
    #         response="400: no arguments given",
    #         status=400
    #     ) 

    #connect to the mongo client
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    db = client.senior_project

    obj = db.movies.find().sort("name", -1)

    find_key = {'Title': { '$regex': t_regex}}

    sort_field = "DateAdded"
    sort_dir = -1
    # find_key = { }
    display_key = { "_id": 0, "DateAdded": 0, "LastChanged": 0 } #dates don't parse to JSON well TODO figure this out?

    obj = db.movies.find(find_key, display_key).sort(sort_field, sort_dir).limit(2)

    retObj = []

    for x in obj:
        print(x["Title"])
        retObj.append(x)


    # https://stackoverflow.com/questions/11961952/objectid-object-has-no-attribute-gettimestamp
    # print("Time of creation", obj['_id'].generation_time)

    client.close()

    if obj:
        return Response(
            mimetype="application/json",
            response=json.dumps(retObj),
            status=200,
        )
    else:
        return Response(
            status=404,
        )

@APP.route('/query_json/<imdbID>')
def read_from_mongo(imdbID):

    #connect to the mongo client
    client = MongoClient()
    client = MongoClient('localhost', 27017)
    db = client.senior_project

    obj = db.movies.find_one({'imdbID': imdbID}, {'_id': False})
    # print("Print\n", obj["Title"])

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

if __name__ == '__main__':
    APP.run()