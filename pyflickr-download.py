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

def parse_command_line():

    parser = OptionParser(
        usage = '%prog [options] OUTPUT_DIR'
    )

    """
    parser.add_option(
        '-n', '--dry-run', dest='is_dry_run', default=False,
        help='perform a dry run (don\'t delete anything)',
        action='store_true',
    )

    parser.add_option(
        '--unattend', dest='is_unattend', default=False,
        help='run without prompting',
        action='store_true',
    )
    """

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

    photos = dict()
    dupe_count = 0

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
        download_url(largest_source, photo_id, output_dir, '[%d/%d] ' % (count, total_count))

    """

    print '%d duplicate photos found (of %d total).' % (dupe_count, len(uploaded_photos))

    # confirm
    if not options.is_unattend:
        choice = None
        print ''
        while not choice or not (choice == 'y' or choice == 'n'):
            choice = raw_input('Would you like to delete them? (y/n): ').lower()
        print ''
        if not choice == 'y':
            sys.exit(2)

    for title in photos.keys():
        if len(photos[title]) <= 1:
            del photos[title]
    
    with open(input_path, 'rb') as csvfile:
        reader = DictReader(csvfile)
        for row in reader:
            title = row['title']
            if title in photos:
                photo_ids = photos[title]
                print '%s has %d duplicates.' % (row['relpath'], len(photo_ids) - 1)
                primary_id = row['photo_id']
                if not primary_id:
                    print '  No primary id found.  Skipping ...'
                    continue
                shorturl = flickrapi.shorturl.url(primary_id)
                print '  Primary photo is %s [ %s ]' % (primary_id, shorturl)
                for photo_id in photo_ids:
                    if photo_id == primary_id:
                        continue
                    shorturl = flickrapi.shorturl.url(photo_id)
                    print '  Deleting photo %s [ %s ] ...' % (photo_id, shorturl)
                    if options.is_dry_run:
                        continue

                    # delete the photo!
                    flickr.photos_delete(photo_id=photo_id)

                del photos[title]

    if len(photos) > 0:
        print '\nCould not find primary photo for %d groups:' % (len(photos),)
        for title in sorted(photos.keys()):
            print '  %s (%d duplicates)' % (title, len(photos[title]) - 1)
    """

    print '\nDone!'