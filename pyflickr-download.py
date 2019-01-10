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
from datetime import datetime
import hashlib

def parse_command_line():

    parser = OptionParser(
        usage = '%prog [options] OUTPUT_DIR'
    )

    parser.add_option(
        '--max-count', dest='max_count', default=None,
        help='max number of photos to download',
        type='int',
    )

    parser.add_option(
        '--output-csv', dest='csv_output_path', default='downloaded.csv',
        help='path to output CSV file',
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

    append = os.path.exists(options.csv_output_path)

    with open(options.csv_output_path, 'ab') as csvfile:
        writer = make_csv_writer(csvfile)

        if not append:
            writer.writeheader()
        
        def write_csv(row):
            writer.writerow(row)
            csvfile.flush()

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

            photo_info = rsp.find('photo')
            media = photo_info.get('media')
            original_format = photo_info.get('originalformat')
            url = photo_info.find('urls').find('url').text
            server = photo_info.get('server')
            title = photo_info.get('title')
            description = photo_info.find('description').text
            if description is not None:
                description = description.strip()
            date_taken = photo_info.find('dates').get('taken')
            shorturl = flickrapi.shorturl.url(photo_id)

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
                    relpath, abspath, filesize = download_url(largest_source, photo_id, output_dir, '[%d/%d] ' % (count, total_count))
                except Exception as e:
                    print '[Error] %s.  Retrying ...' % (e.message,)
                    continue
                break
            
            filehash = None
            with open(abspath, 'rb') as f:
                filehash = str(hashlib.md5(f.read()).hexdigest())

            row = locals()
            write_csv(row)

    print '\nDone!'