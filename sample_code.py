// https://stackoverflow.com/questions/44621359/python-cant-serve-mp4-to-browser

n="\\wamp\\www\\r.mp4"
print ("Last-Modified: Fri, 24 Apr 2015 22:09:52 GMT")
print ("Accept-Ranges: bytes")
print ("Content-Length:", os.path.getsize(n))
print ("Content-type: video/mp4\r\n\r\n")
sys.stdout.flush()

f=open(n, 'rb')
d=f.read()
sys.stdout.buffer.write(d)
f.close()

# API 
import requests

response = requests.get("http://api.open-notify.org/astros.json")
print(response.status_code)