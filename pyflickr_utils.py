"""
PyFlickr utilies module
"""

import json
from csv import DictWriter
import os
from datetime import datetime
import sys

API_KEY = 'f5b40cdc2dfac381aefcfd48687ddaba'
API_SECRET = '30bce1a79b59ea4a'
PYFLICKR_TAG = 'PyFlickr'
FLICKR_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
PYFLICKR_FILEMETA_TOKEN = '[!PyFlickr.filemeta]'

def photo_description(filemeta):
    return '\n'.join([
        PYFLICKR_FILEMETA_TOKEN,
        json.dumps(filemeta),
        PYFLICKR_FILEMETA_TOKEN
    ])

def make_csv_writer(csvfile):
    return DictWriter(csvfile, extrasaction='ignore', fieldnames=(
        'photo_id',
        'title',
        'relpath',
        'abspath',
        'filehash',
        'created',
        'modified',
        'filesize',
        'exif_original_date',
        'mov_created_date',
        'upload_start',
        'upload_end',
        'date_taken',
        'shorturl',
        'url',
        'media',
        'original_format',
        'server',
    ))

# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=50):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = u'\u2588' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def get_uploaded_photos(flickr, max_count=None):
    photos = set()
    num_pages = 0
    total = 0
    count = 0
    def fetch(page, num_pages, total, photos, count, max_count):
        if max_count is not None and count >= max_count:
            return num_pages, total, photos, count
        rsp = flickr.photos_search(user_id='me', per_page=500, page=page)
        if page == 1:
            num_pages = int(rsp.find('photos').get('pages'))
            total = int(rsp.find('photos').get('total'))
        print_progress(page, num_pages)
        for photo in rsp.find('photos').getchildren():
            title = photo.get('title')
            photo_id = photo.get('id')
            photos.add((photo_id, title))
            count += 1
            if max_count is not None and count >= max_count:
                break
        return num_pages, total, photos, count
    (num_pages, total, photos, count) = fetch(1, num_pages, total, photos, count, max_count)
    for page in range(2, num_pages + 1):
        (num_pages, total, photos, count) = fetch(page, num_pages, total, photos, count, max_count)

    if max_count is None:
        # for some reason, flickr seems to under-report the total
        print 'photos found:', count, 'vs. total reported by flickr api:', total
        assert count >= total
    else:
        sys.stdout.write('\n')
    
    return photos

import urllib2

def download_url(url, filename_prefix, directory, progress_prefix=''):
    
    req = urllib2.urlopen(url)

    filename_ext = None

    if req.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        filename = req.info()['Content-Disposition'].split('filename=')[1]
        if filename[0] == '"' or filename[0] == "'":
            filename = filename[1:-1]
        filename_ext = os.path.splitext(filename)[-1]
    else:
        filename_ext = '.' + url.split('.')[-1]

    filename = filename_prefix + filename_ext

    f = open(os.path.join(directory, filename), 'wb')

    total_bytes = int(req.info()['Content-Length'])
    print '%sDownloading: %s Bytes: %s' % (progress_prefix, filename, total_bytes)

    downloaded_bytes = 0
    block_size = 8192
    while True:
        buffer = req.read(block_size)
        if not buffer:
            break

        downloaded_bytes += len(buffer)
        f.write(buffer)
        print_progress(downloaded_bytes, total_bytes);

    f.close()

import exifread

def get_exif_original_date(path):
    if os.path.splitext(path)[1].lower() == '.jpg':
        with open(path, 'rb') as f:
            exif = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
            return datetime.strptime(str(exif['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
    return None


import hachoir_core.cmd_line
import hachoir_parser
import hachoir_metadata
import re

def get_mov_created_date(path):
    if os.path.splitext(path)[1].lower() == '.mov':
        filename, realname = hachoir_core.cmd_line.unicodeFilename(path), path
        parser = hachoir_parser.createParser(filename, realname)
        metadata = hachoir_metadata.extractMetadata(parser)
        text = metadata.exportPlaintext()
        for line in text:
            m = re.search(r'Creation date:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', line, re.I)
            if m:
                return datetime.strptime(str(m.group(1)) + ' ' + str(m.group(2)), '%Y-%m-%d %H:%M:%S')
    return None

def get_photo_dates(path):
    date_created = datetime.fromtimestamp(os.path.getctime(path))
    date_modified = datetime.fromtimestamp(os.path.getmtime(path))
    exif_date = get_exif_original_date(path)
    mov_date = get_mov_created_date(path)

    # compute the date taken
    date_taken = None
    if exif_date:
        date_taken = exif_date
    elif mov_date:
        date_taken = mov_date
    else:
        date_taken = min(date_created, date_modified)

    return (
        date_created,
        date_modified,
        exif_date,
        mov_date,
        date_taken
    )

def get_photo_meta(path, relpath, filehash, filesize):
    date_created, date_modified, exif_date, mov_date, date_taken = \
        get_photo_dates(path)
    filemeta = {
        'relpath': relpath,
        'abspath': os.path.abspath(path),
        'created': date_created.strftime(FLICKR_DATE_FORMAT),
        'modified': date_modified.strftime(FLICKR_DATE_FORMAT),
        'filehash': filehash,
        'filesize': filesize,
        'exif_original_date': exif_date.strftime(FLICKR_DATE_FORMAT) if exif_date else None,
        'mov_created_date': mov_date.strftime(FLICKR_DATE_FORMAT) if mov_date else None,
    }
    title = '%s__%s' % (os.path.basename(path), filehash)
    description = photo_description(filemeta)
    return (
        filemeta, 
        title,
        description,
        date_taken
    )


from fnmatch import fnmatch

PHOTO_PATTERNS = ('*.jpg', '*.jpeg', '*.png', '*.bmp')
MOVIE_PATTERNS = ('*.mov', '*.mp4', '*.mpg', '*.mpeg', '*.avi')

PHOTO_PATTERNS += tuple(x.upper() for x in PHOTO_PATTERNS)
MOVIE_PATTERNS += tuple(x.upper() for x in MOVIE_PATTERNS)

def is_picture(filename):
    for pat in PHOTO_PATTERNS:
        if fnmatch(filename, pat):
            return True
    return False

def is_movie(filename):
    for pat in MOVIE_PATTERNS:
        if fnmatch(filename, pat):
            return True
    return False
