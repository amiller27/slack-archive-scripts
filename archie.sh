#!/usr/bin/env bash
cd /home/ubuntu/slack-archiver/slack-archiver
echo "--------PYTHON SLACK ARCHIVER--------" >> ../archie.log
date >> ../archie.log
python slack-archiver.py &>> ../archie.log

cd ..
echo "---------FILE DOWNLOADER-------------" >> archie.log
date >> archie.log
python slack-downloader.py &>> archie.log

cd drive
echo "--------GRIVE UPDATE--------" >> ../archie.log
date >> ../archie.log
grive -s RAS/SlackArchive/ &>> ../archie.log
