# API 
import requests
import json
#import pymongo
from pymongo import MongoClient

movie = "ferngully"
movie = input("Please enter the title: ")

response = requests.get(f"http://www.omdbapi.com/?apikey=1e93b34f&t={movie}")
print(response.status_code)
print()
#print(response.json())

obj = response.json()

#print("Title:" , obj["Title"])
#print("Rating:" , obj["Rated"])
#print("Length:" , obj["Runtime"])
#print("Summary:" , obj["Plot"])
#print("Released:" , obj["Released"])
#print("ID:" , obj["imdbID"])
#print("Poster:", obj["Poster"])

''' write to mongo '''

client = MongoClient()

client = MongoClient('localhost', 27017)
db = client.senior_project

if (db.movies.find_one({'imdbID': obj["imdbID"]})):
    print("found")
    result = db.movies.update_one({'imdbID': obj["imdbID"]}, {"$set": obj })
    print(result)
else:
    print("not_found")
    result = db.movies.insert_one(obj)
    print('One post: {0}'.format(result))

bills_post = db.movies.find_one({'imdbID': obj["imdbID"]})

print(bills_post)
