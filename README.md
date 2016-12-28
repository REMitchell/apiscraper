The API Scraper is a Python 3.x tool designed to find "hidden" API calls powering a website.


<h2>Installation</h2>

To use, you must have Selenium intalled with Firefox and Firebug. 
<ul>
<li><a href="http://selenium-python.readthedocs.io/">Selenium</a></li>
<li><a href="http://www.mozilla.org/firefox">Firefox</a></li>
<li><a href="https://addons.mozilla.org/en-US/firefox/addon/firebug/">Firebug</a></li>
</ul>

<h2>Usage</h2>
The script can be run from the command line using:
<code>$python3 apiFinder.py [commands]</code>
<p>
If you get confused about which commands to use, use the -h flag. 
<code>
hse-nyc-lt-999:apiscraper rmitchell$ python3 apiFinder.py -h 
usage: apiFinder.py [-h] [-u [U]] [-d [D]] [-s [S]] [-o O [O ...]]

optional arguments:
  -h, --help    show this help message and exit
  -u [U]        Target URL
  -d [D]        Target directory
  -s [S]        Search term
  -o O [O ...]  Optional (removeParams, crawlApis)
  </code>

