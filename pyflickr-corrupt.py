#!/usr/bin/python
"""
Search Flickr for corrupted uploads
"""

from csv import DictReader
from fnmatch import fnmatch
from optparse import OptionParser
from pyflickr_utils import *
from selenium import webdriver
import sys
import time
import urllib2

def parse_command_line():

    parser = OptionParser(
        usage = '%prog [options] uploaded.csv USERNAME PASSWORD'
    )

    parser.add_option(
        '-n', '--dry-run', dest='is_dry_run', default=False,
        help='perform a dry run (don\'t search anything)',
        action='store_true',
    )

    parser.add_option(
        '--unattend', dest='is_unattend', default=False,
        help='run without prompting',
        action='store_true',
    )

    parser.add_option(
        '--max-count', dest='max_count', default=None,
        help='search at most N photos',
        type='int',
    )

    parser.add_option(
        '-o', '--output', dest='output_path', default='corrupt.csv',
        help='path to output csv of corrupt photos',
    )

    (options, args) = parser.parse_args()

    if len(args) < 3:
        parser.print_usage()
        sys.exit(1)

    return (options, args)

def fetch(url):
    return urllib2.urlopen(url, data=None, timeout=10)

if __name__ == "__main__":

    (options, args) = parse_command_line()
    input_path = args[0]
    username = args[1]
    password = args[2]

    # build list of patterns
    patterns = MOVIE_PATTERNS

    # build list of photos to search
    print 'Reading input ...'
    photos = []
    with open(input_path, 'rb') as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            for pat in patterns:
                if fnmatch(row['relpath'], pat):
                    photos.append(row)

    # limit max count
    if options.max_count:
        photos = photos[:options.max_count]

    # confirm
    print ''
    print 'Will now check %d photos on Flickr for signs of corruption.' % (len(photos),)
    if not options.is_unattend:
        choice = None
        while not choice or not (choice == 'y' or choice == 'n'):
            choice = raw_input('Continue? (y/n): ').lower()
        if not choice == 'y':
            sys.exit(2)
    print ''

    # open the web browser
    print 'Launching web browser ...'
    browser = webdriver.Chrome()

    # sign in to flickr
    print 'Logging into Flickr ...'
    browser.get('https://www.flickr.com/signin/')
    time.sleep(1)
    elem = browser.find_element_by_id('username')
    elem.send_keys(username)
    time.sleep(1)
    elem = browser.find_element_by_id('passwd')
    elem.send_keys(password)
    time.sleep(1)
    elem.submit()
    time.sleep(5)

    # browse to each photo and check for corruption

    def find_element_by_css_selector(browser, selector):
        exc = None
        for i in range(5):
            try:
                return browser.find_element_by_css_selector(selector)
            except Exception, e:
                time.sleep(1)
                exc = e
        raise exc

    def check_photo(url):
        # navigate to photo page on flickr
        browser.get(row['url'])

        # check the image URL
        elem = find_element_by_css_selector(browser, "meta[name='og:image']")
        image_url = elem.get_attribute('content')
        print '  image url: %s' % (image_url,)
        if 'video_failed' in image_url:
            return False

        # check the poster url
        elem = find_element_by_css_selector(browser, "img.yui3-videoplayer-startscreen-image")
        poster_url = elem.get_attribute('src')
        print '  poster url: %s' % (poster_url,)
        real_poster_url = fetch(poster_url).geturl()
        print '  real poster url: %s' % (real_poster_url,)
        if 'photo_unavailable' in real_poster_url:
            return False
        return True
    
    with open(options.output_path, 'wb') as csvfile:
        writer = make_csv_writer(csvfile)
        writer.writeheader()

        for row in photos:
            print 'Checking %s ...' % (row['relpath'],)
            if not check_photo(row['url']):
                print '  *** Corruption Detected! ***'
                writer.writerow(row)
                csvfile.flush()
