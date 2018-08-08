The API Scraper is a Python 3.x tool designed to find "hidden" API calls powering a website.


<h2>Installation</h2>
The following Python libraries should be installed (with pip, or the package manager of your choice):
<ul>
<li>Selenium</li>
<li>Requests</li>
</ul>
Download the latest Chrome webdriver and the BrowserMob Proxy bin. Put them into the apiscraper root directory. 
See line 35 in apiFinder.py to modify the directory names and locations of these binary files:

`self.browser = Browser("chromedriver/chromedriver", "browsermob-proxy-2.1.4/bin/browsermob-proxy", self.harDirectory)`

<ul>
<li><a href="https://sites.google.com/a/chromium.org/chromedriver/downloads">Chrome Driver</a></li>
<li><a href="https://bmp.lightbody.net/">BrowserMob Proxy</a></li>
</ul>



<h2>Usage</h2>
The script can be run from the command line using:
<code>$python3 consoleservice.py [commands]</code>
<p>
If you get confused about which commands to use, use the -h flag. 

<code>
$ python3 consoleservice.py -h <p>
usage: consoleService.py [-h] [-u [U]] [-d [D]] [-s [S]] [-c [C]] [--p]
<p>
optional arguments:<br>

  -h, --help  show this help message and exit<br>

  -u [U]      Target URL. If not provided, target directory will be scanned
              for har files.<br>

  -d [D]      Target directory (default is "hars"). If URL is provided,
              directory will store har files. If URL is not provided,
              directory will be scanned.<br>

  -s [S]      Search term<br>

  -c [C]      Count of pages to crawl (with target URL only)<br>
  
  --p         Flag, remove unnecessary parameters (may dramatically increase
              run time)<br>
  </code>

<h2>Running the API</h2>
Hey, I heard you like APIs so I'm writing an API to find you APIs so you can API while you API. 
<p>
Kicking this off over HTTP is absolutely not necessary at all, however, I am including a Flask wrapper around the API Finder, so it might as well be documented!
<p>
Install <a href="http://flask.pocoo.org/">Flask</a>
<p>
export FLASK_APP=webservice.py<br>
flask run
