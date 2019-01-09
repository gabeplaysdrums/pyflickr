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
        #print 'getting source URL for photo id=%s' % (photo_id,)
        rsp = flickr.photos.getSizes(photo_id=photo_id)
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

        # download metadata
        open(os.path.join(output_dir, photo_id + '.info.xml'), 'w').write(ElementTree.tostring(flickr.photos.getInfo(photo_id=photo_id), encoding='utf8', method='xml'))
        
        # download photo
        download_url(largest_source, photo_id, output_dir, '[%d/%d] ' % (count, total_count))

    print '\nDone!'