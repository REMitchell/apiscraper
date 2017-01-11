from flask import Flask
from flask import request
from apiFinder import APIFinder
from apicall import APIWriter
app = Flask(__name__)

@app.route("/search")
def search():
    #(self, url=None, harDirectory=None, searchString=None, removeParams=False, count=1)
    searchStr = request.args.get('search')
    urlStr = request.args.get('url')
    finder = APIFinder(url=urlStr, searchString=searchStr)
    apiCalls = finder.start()
    writer = APIWriter(apiCalls)
    return writer.outputJSON()

@app.route("/crawl")
def crawl():
    return "Hello World!"


if __name__ == "__main__":
    app.run()