#!/usr/bin/env python
#
#  Selenium Web/HTTP Profiler
#  Copyright (c) 2009-2011 Corey Goldberg (corey@goldb.org)
#  License: GNU GPLv3



import json
import socket
import sys
import time
import urlparse
import xml.etree.ElementTree as etree
from datetime import datetime

from selenium import selenium



def main():
    if len(sys.argv) < 2:
        print 'usage:'
        print '  %s <url> [browser_launcher]' % __file__
        print 'examples:'
        print '  $ python %s www.google.com' % __file__
        print '  $ python %s http://www.google.com/ *firefox\n' % __file__
        sys.exit(1)
    else:
        url = sys.argv[1]
        if not url.startswith('http'):
            url = 'http://' + url
        parsed_url = urlparse.urlparse(url)
        site = parsed_url.scheme + '://' + parsed_url.netloc
        path = parsed_url.path
        if path == '':
            path = '/'
        browser = '*firefox'
    
    if len(sys.argv) == 3:
        browser = sys.argv[2]
        
    run(site, path, browser)


        
def run(site, path, browser):  
    sel = selenium('127.0.0.1', 4444, browser, site)
    
    try:
        sel.start('captureNetworkTraffic=true')
    except socket.error:
        print 'ERROR - can not start the selenium-rc driver. is your selenium server running?'
        sys.exit(1)
        
    sel.open(path)
    sel.wait_for_page_to_load(60000)   
    end_loading = datetime.now()
    
    raw_xml = sel.captureNetworkTraffic('xml')
                
    sel.stop()
    
    traffic_xml = raw_xml.replace('&', '&amp;').replace('=""GET""', '="GET"').replace('=""POST""', '="POST"') # workaround selenium bugs
    
    nc = NetworkCapture(traffic_xml)
    
    #json_results = nc.get_json()
    
    num_requests = nc.get_num_requests()
    total_size = nc.get_content_size()
    status_map = nc.get_http_status_codes()
    file_extension_map = nc.get_file_extension_stats()
    http_details = nc.get_http_details()
    start_first_request, end_first_request, end_last_request = nc.get_network_times()
    
    end_load_elapsed = get_elapsed_secs(start_first_request, end_loading)
    end_last_request_elapsed = get_elapsed_secs(start_first_request, end_last_request)
    end_first_request_elapsed = get_elapsed_secs(start_first_request, end_first_request)
    
    print '--------------------------------'
    print 'results for %s' % site
    
    print '\ncontent size: %s kb' % total_size
    
    print '\nhttp requests: %s' % num_requests
    for k,v in sorted(status_map.items()):
        print 'status %s: %s' % (k, v)
    
    print '\nprofiler timing:'
    print '%.3f secs (page load)' % end_load_elapsed
    print '%.3f secs (network: end last request)' % end_last_request_elapsed
    print '%.3f secs (network: end first request)' % end_first_request_elapsed
    
    print '\nfile extensions: (count, size)'
    for k,v in sorted(file_extension_map.items()):
        print '%s: %i, %.3f kb' % (k, v[0], v[1])
        
    print '\nhttp timing detail: (status, method, doc, size, time)'
    for details in http_details:
        print '%i, %s, %s, %i, %i ms' % (details[0], details[1], details[2], details[3], details[4])

  
  
def get_elapsed_secs(dt_start, dt_end):
    return float('%.3f' % ((dt_end - dt_start).seconds + 
        ((dt_end - dt_start).microseconds / 1000000.0)))
 
 
 
class NetworkCapture(object): 
    def __init__(self, xml_blob):
        self.xml_blob = xml_blob
        self.dom = etree.ElementTree(etree.fromstring(xml_blob))
        
    
    def get_json(self):
        results = []
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                url = child.attrib.get('url')
                start_time = child.attrib.get('start')
                time_in_millis = child.attrib.get('timeInMillis')
                results.append((url, start_time, time_in_millis))
        return json.dumps(results)               
                
        
    def get_content_size(self):  # total kb passed through the proxy  
        byte_sizes = []
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                byte_sizes.append(child.attrib.get('bytes'))
        total_size = sum([int(bytes) for bytes in byte_sizes]) / 1000.0
        return total_size
    
    
    def get_num_requests(self):
        num_requests = 0
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                num_requests += 1
        return num_requests
    
    
    def get_http_status_codes(self):       
        status_map = {}
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                try:
                    status_map[child.attrib.get('statusCode')] += 1
                except KeyError:
                    status_map[child.attrib.get('statusCode')] = 1
        return status_map
    
    
    def get_http_details(self):
        http_details = []
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                url = child.attrib.get('url') + '?'
                url_stem = url.split('?')[0]
                doc = '/' + url_stem.split('/')[-1]
                status = int(child.attrib.get('statusCode'))
                method = child.attrib.get('method').replace("'", '')
                size = int(child.attrib.get('bytes'))
                time = int(child.attrib.get('timeInMillis'))
                http_details.append((status, method, doc, size, time))
        http_details.sort(cmp=lambda x,y: cmp(x[3], y[3])) # sort by size
        return http_details
        
        
    def get_file_extension_stats(self):
        file_extension_map = {}  # k=extension v=(count,size) 
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                size = float(child.attrib.get('bytes')) / 1000.0
                url = child.attrib.get('url') + '?'
                url_stem = url.split('?')[0]
                doc = url_stem.split('/')[-1]
                if '.' in doc:
                    file_extension = doc.split('.')[-1]
                else:
                    file_extension = 'unknown'
                try:
                    file_extension_map[file_extension][0] += 1
                    file_extension_map[file_extension][1] += size
                except KeyError:
                    file_extension_map[file_extension] = [1, size]
        return file_extension_map
        
        
    def get_network_times(self):
        timings = []
        start_times = []
        end_times = []
        for child in self.dom.getiterator():
            if child.tag == 'entry':
                timings.append(child.attrib.get('timeInMillis'))
                start_times.append(child.attrib.get('start')) 
                end_times.append(child.attrib.get('end'))
        start_times.sort()
        end_times.sort()
        start_first_request = self.convert_time(start_times[0])
        end_first_request = self.convert_time(end_times[0])
        end_last_request = self.convert_time(end_times[-1])
        return (start_first_request, end_first_request, end_last_request)
        
        
    def convert_time(self, date_string):
        if '-' in date_string: split_char = '-'
        else: split_char = '+'
        dt = datetime.strptime(''.join(date_string.split(split_char)[:-1]), '%Y%m%dT%H:%M:%S.%f')    
        return dt
        
      
      
if __name__ == '__main__':
    main()
    
