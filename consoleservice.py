from apicall import APIWriter
from apiFinder import APIFinder

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", help="Target URL. If not provided, target directory will be scanned for har files.", nargs='?')
parser.add_argument("-d", help="Target directory (default is \"hars\"). If URL is provided, directory will store har files. If URL is not provided, directory will be scanned. ", nargs='?')
parser.add_argument("-s", help="Search term", nargs='?')
parser.add_argument("-c", help="Count of pages to crawl (with target URL only)", nargs='?')
parser.add_argument('--p', help="Flag, remove unnecessary parameters (may dramatically increase run time)", action='store_true')
args = parser.parse_args()

if not (args.u or args.d):
	print("Need to provide either a URL or directory or both. Use -h for help")
	sys.exit(1)

if args.d is None:
	args.d = "hars"
count = 1

finder = APIFinder(url=args.u, harDirectory=args.d, searchString=args.s, removeParams=args.p, count=count)
#Clean up any existing har files
finder.setup()
apiCalls = finder.start()
apiWriter = APIWriter(apiCalls)
apiWriter.outputAPIs()