#!/usr/bin/python
"""
Download photos from Flickr
"""

from csv import DictReader
from optparse import OptionParser
from pyflickr_utils import *
import flickrapi
import flickrapi.shorturl
import sys
import urllib
from xml.etree import ElementTree

def parse_command_line():

    parser = OptionParser(
        usage = '%prog [options] OUTPUT_DIR'
    )

    parser.add_option(
        '--max-count', dest='max_count', default=None,
        help='max number of photos to download',
        type='int',
    )

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_usage()
        sys.exit(1)

    return (options, args)

if __name__ == "__main__":

    (options, args) = parse_command_line()
    output_dir = args[0]

    print 'Authenticating ...'
    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET)
    flickr.authenticate_console(perms='delete')

    print 'Getting previously uploaded photos ...'
    uploaded_photos = get_uploaded_photos(flickr, options.max_count)

    total_count = len(uploaded_photos)
    print '\nFound %d uploaded photos\n' % (total_count,)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    count = 0

    for (photo_id, title) in uploaded_photos:
        # download info
        while True:
            try:
                rsp = flickr.photos.getInfo(photo_id=photo_id)
            except Exception as e:
                print '[Error] %s.  Retrying ...' % (e.message,)
                continue
            break

        open(os.path.join(output_dir, photo_id + '.info.xml'), 'w').write(ElementTree.tostring(rsp, encoding='utf8', method='xml'))

        # download sizes
        while True:
            try:
                rsp = flickr.photos.getSizes(photo_id=photo_id)
            except Exception as e:
                print '[Error] %s.  Retrying ...' % (e.message,)
                continue
            break

        open(os.path.join(output_dir, photo_id + '.sizes.xml'), 'w').write(ElementTree.tostring(rsp, encoding='utf8', method='xml'))

        largest_source = None
        largest_label = None
        largest_width = 0
        largest_height = 0
        for size in rsp.find('sizes').getchildren():
            label = size.get('label')
            width = int(size.get('width'))
            height = int(size.get('height'))
            source = size.get('source')
            #print 'found size: %s %dx%d %s' % (label, width, height, source)
            if (width * height) > (largest_width * largest_height):
                largest_width = width
                largest_height = height
                largest_source = source
                largest_label = label
        #print 'URL: %s' % (largest_source,)
        count += 1

        # download photo
        while True:
            try:
                download_url(largest_source, photo_id, output_dir, '[%d/%d] ' % (count, total_count))
            except Exception as e:
                print '[Error] %s.  Retrying ...' % (e.message,)
                continue
            break

    print '\nDone!'