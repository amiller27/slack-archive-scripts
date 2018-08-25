#!/usr/bin/env python3

# 
# slack-downloader
# Author: Enrico Cambiaso
# Email: enrico.cambiaso[at]gmail.com
# GitHub project URL: https://github.com/auino/slack-downloader
# 

import requests
import json
import argparse
import calendar
import errno
import sys
import os
import time
from datetime import datetime, timedelta
from pprint import pprint # for debugging purposes

# --- --- --- --- ---
# CONFIGURATION BEGIN
# --- --- --- --- ---

# API Token: see https://api.slack.com/web
TOKEN = "xoxp-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# output main directory, without slashes
#OUTPUTDIR = "drive/RAS/SlackArchive/files"
OUTPUTDIR = "<OUTPUT DIR HERE>"

# enable debug?
DEBUG = True

# enable extremely verbose debug?
EXTREME_DEBUG = False

# --- --- --- --- ---
#  CONFIGURATION END
# --- --- --- --- ---

# constants

# Slack base API url
API = 'https://slack.com/api'

# program directory
MAINDIR = os.path.dirname(os.path.realpath(__file__))+'/'

# useful to avoid duplicate downloads
TIMESTAMPFILE = MAINDIR+"offset.txt"

# format a response in json format
def response_to_json(response):
    try:
        res = response.json
        foo = res['ok']
        return res
    except: # different version of python-requests
        return response.json()

# file renaming function
def get_local_filename(basedir, date, filename, user):
    # converting date from epoch time to readable format
    date = time.strftime('%Y%m%d_%H%M%S', time.localtime(float(date)))
    # splitting filename to file extension
    filename, file_extension = os.path.splitext(filename)
    # retrieving full filename with path and returning it
    return basedir+'/'+str(date)+'-'+filename+'_by_'+user+file_extension

# save the timestamp of the last download (+1), in order to avoid duplicate downloads
def set_timestamp(ts):
    with open(TIMESTAMPFILE,"w") as out_file:
        out_file.write(str(ts))

# get saved timestamp of last download
def get_timestamp():
    with open(TIMESTAMPFILE,"r") as in_file:
        text = in_file.read()
        return int(text)

# download a file to a specific location
def download_file(url, local_filename, basedir):
    try:
        os.stat(basedir)
    except:
        os.mkdir(basedir)
    print "Saving to", local_filename
    headers = {'Authorization': 'Bearer '+TOKEN}
    r = requests.get(url, headers=headers)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: f.write(chunk)

# get channel name from identifier
def get_channel_name(id):
    url = API+'/channels.info'
    data = {'token': TOKEN, 'channel': id }
    response = requests.post(url, data=data)
    if DEBUG and EXTREME_DEBUG: pprint(response_to_json(response))
    return response_to_json(response)['channel']['name']

# get user name from identifier
def get_user_name(id):
    url = API+'/users.info'
    data = {'token': TOKEN, 'user': id }
    response = requests.post(url, data=data)
    if DEBUG and EXTREME_DEBUG: pprint(response_to_json(response))
    return response_to_json(response)['user']['name']

# request files
def make_requester():
    list_url = API+'/files.list'

    def all_requester(page):
        print('Requesting all files')
        data = {'token': TOKEN, 'page': page}
        ts = get_timestamp()
        if ts != None: data['ts_from'] = ts
        response = requests.post(list_url, data=data)
        if response.status_code != requests.codes.ok:
            print('Error fetching file list')
            sys.exit(1)
        return response_to_json(response)

    return all_requester

# main function
if __name__ == '__main__':
    # retrieving absolute output directory
    OUTPUTDIR = MAINDIR+OUTPUTDIR
    # creating main output directory, if needed
    try:
        os.stat(OUTPUTDIR)
    except:
        os.mkdir(OUTPUTDIR)
    page = 1
    users = dict()
    file_requester = make_requester()
    ts = None
    while True:
        json = file_requester(page)
        if not json['ok']: print('Error', json['error'])
        fileCount = len(json['files'])
        print 'Found', fileCount, 'files in total'
        if fileCount == 0: break
        for f in json["files"]:
            try:
                if DEBUG and EXTREME_DEBUG: pprint(f) # extreme debug
                if f['is_external']: continue
                filename = f['name'].encode('ascii', 'replace')
                date = str(f['timestamp'])
                user = users.get(f['user'], get_user_name(f['user']))
                file_url = f["url_private_download"]

                if f['channels']:
                    basedir = OUTPUTDIR+'/'+get_channel_name(f['channels'][0])
                else:
                    basedir = OUTPUTDIR+'/no_channel'

                local_filename = get_local_filename(basedir, date, filename, user)
                print "Downloading file '"+str(file_url)+"'"
                download_file(file_url, local_filename, basedir)
                if ts == None or float(date) > float(ts): ts = date
            except Exception:
                if DEBUG:
                    print f
                    import traceback
                    traceback.print_exc()
                pass
        page = page + 1
    if ts != None: set_timestamp(int(ts)+1)
    print('Finished.')
