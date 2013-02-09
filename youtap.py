#!/usr/bin/python
#
# Copyright [2011] Sundar Srinivasan
# Copyright [2013] Giloux
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Original Author: Sundar Srinivasan (krishna.sun@gmail.com) Twitter: @krishnasun
# Forked by: Giloux

__author__ = ('Giloux')

from sys import stdout
import re
import sys
import urllib2
import urlparse
import argparse
import os.path

#Define the priorities of the formats
DEFT_PREFERED_FORMAT = [
'mp4/hd720',
'webm/hd720',
'mp4/large',
'x-flv/large',
'webm/large',
'mp4/medium',
'x-flv/medium',
'webm/medium',
'mp4/small',
'3gpp/small',
'x-flv/small',
]

def getVideoUrls(content):
    "Retrieve the dowload links of the media"
    
    swfdata = re.search('var swf = "(.*)"', content).group(1)
    flashvars = unicode(
        re.search(r' flashvars=\\"(.*?)\\" ', swfdata).group(1)).decode(
            'string-escape').split(";")

    fv = dict([v.split('=') for v in flashvars])
    
    medialist = {}
    for mediadesc in urllib2.unquote(fv["url_encoded_fmt_stream_map"]).split(','):
        fsm = urlparse.parse_qs(mediadesc)

        url = fsm['url'][0]
        sig = fsm['sig'][0]
        vtype = fsm['type'][0].split(';')[0].split('/')[1]
        qual = fsm['quality'][0]

        meta = "%s/%s" % (vtype, qual)
        url = "%s&signature=%s" % (url, sig)
        medialist[meta]=url
        
    return medialist

def getTitle(content):
    "Provide a title that can be used as filename"
    title = content.split('</title>', 1)[0].split('<title>')[1]
    return sanitizeTitle(title)

def sanitizeTitle(rawtitle):
    rawtitle = urllib2.unquote(rawtitle)
    lines = rawtitle.split('\n')
    title = ''
    for line in lines:
        san = unicode(re.sub('[^\w\s-]', '', line).strip())
        san = re.sub('[-\s]+', '_', san)
        title = title + san
    ffr = title[:4]
    title = title[5:].split(ffr, 1)[0]
    return title

def downloadVideo(f, resp):
    "Download the media, print the progress"
    totalSize = int(resp.info().getheader('Content-Length').strip())
    currentSize = 0
    CHUNK_SIZE = 32768

    while True:
        data = resp.read(CHUNK_SIZE)

        if not data:
            break
        currentSize += len(data)
        f.write(data)

        stdout.write('\r> ' + \
                  str(round(float(currentSize*100)/totalSize, 2)) + \
                  '% of ' + str(totalSize) + ' bytes          ')
        if currentSize >= totalSize:
            break
    return

def getVideoFromUrl(urlname, outdir):
    """High level function that : 
         1.find the available media from a youtube page
         2.select the media to download (using the priorities list)
         3.download it
    """
    
    ## Download the youtube page
    print('Processing youtube page : ' + urlname)
    try:
        resp = urllib2.urlopen(urlname)
    except urllib2.HTTPError:
        print('Error occurred when connecting to URL')
        exit(1)
    content = resp.read()

    ## Extract urls and find the prefered one
    video_urls = getVideoUrls(content)
    prefered = filter(lambda x : x[1] is not None, [(meta,video_urls.get(meta)) for meta in DEFT_PREFERED_FORMAT])
    if len(prefered) == 0 :
        print "bad formats"
        exit(-1)
    
    meta,videoUrl = prefered[0]
    
    if not videoUrl:
        print('Video URL cannot be found')
        exit(1)
    
    ## Determine filename
    title = getTitle(content)
    filename = title + '.' + meta.split('/')[0]
    filepath = os.path.join(outdir,filename)
    print('Creating file: ' + filepath)
    f = open(filename, 'wb')
    print('Download begins...')

    ## Download video
    video = urllib2.urlopen(videoUrl)
    downloadVideo(f, video)
    f.flush()
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("Url")
    parser.add_argument("--outdir", default="./")
    args = parser.parse_args()
    urlname = args.Url.split('&', 1)[0]
    getVideoFromUrl(urlname,args.outdir)
    
