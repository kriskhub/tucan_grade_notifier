#!/usr/bin/env python3

import argparse
import datetime
import fcntl
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
import lxml
from pathlib import Path
import mechanize
import pandas as pd
import schedule
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query, where


class GRADE_CRAWLER:

    log = None
    url = "https://www.tucan.tu-darmstadt.de/scripts/mgrqispi.dll?APPNAME=CampusNet&PRGNAME=EXTERNALPAGES&ARGUMENTS=-N000000000000001,-N000344,-Awelcome"

    def __init__(self, args: object) -> object:
        self.log = logging.getLogger('grade_crawler')
        self.log.setLevel(logging.INFO)

        # console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        default_formatter = logging.Formatter('[%(asctime)s] %(message)s')
        handler.setFormatter(default_formatter)
        self.log.addHandler(handler)

        if args.verbose:
            self.log.setLevel(logging.DEBUG)
            debug_formatter = logging.Formatter('[%(asctime)s%(msecs)03d] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
            handler.setFormatter(debug_formatter)
        elif args.quiet:
            self.log.setLevel(logging.WARN)

        if args.log_path:
            file_formatter = logging.Formatter('[%(asctime)s%(msecs)03d] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
            fh = logging.FileHandler(args.log_path)
            fh.setFormatter(file_formatter)
            fh.setLevel(logging.DEBUG)
            self.log.addHandler(fh)

        self.log.info("########################################")
        self.log.info("#         TUCAN Grade Crawler          #")
        self.log.info("#          & E-Mail Notifier           #")
        self.log.info("########################################")


        self.start = datetime.datetime.now()
        self.dateformat = "%Y-%m-%d-%H%M%S"
        self.base_path = Path(args.data_path)
        self.log.debug("Database path: %s", self.base_path.absolute())
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.base_path.resolve()
        self.db = TinyDB(str(self.db_path) + '/db.json')

        lockfd = os.open(self.base_path.absolute(), os.O_RDONLY)
        fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        self.username = args.username
        self.password = args.password
        self.mailaddress = args.mailaddress

        self.log.debug("Setting up schedule: One request every" + str(args.interval) + "minute")
        schedule.every(args.interval).minutes.do(self.check_grades)

        self.log.debug("Starting scheduler")
        while True:
            schedule.run_pending()
            time.sleep(1)

    def check_grades(self):
        '''
        Check if the grades are already in database and update respectively
        '''

        grades = self.get_grades()
        json_grades = grades.to_json(orient="records")
        parsed_grades = json.loads(json_grades)
        results = self.db.all()
        if len(results) == 0:
            self.log.info("[*] Insert very first grades")
            self.db.insert_multiple(parsed_grades)
        else:
            for course in parsed_grades:
                c = self.db.search(Query()['No.'] == course['No.'])[0]
                if len(c) > 0 and c["Hash"] != course["Hash"]:
                    self.db.update(course, where('No.') == course['No.'])
                    self.log.info("[!] New Grade!")
                    self.notify(course)

    def get_grades(self):
        ''' Crawling job which is run every couple of minutes and gets set of grades of latest semester. '''
        roundstart = datetime.datetime.now()
        self.log.info("[*] Start crawling")

        br = mechanize.Browser()
        br.open(self.url)
        br.select_form(nr=0)
        br.form["usrname"] = self.username
        br.form["pass"] = self.password
        br.submit()
        br.follow_link(text_regex=u"(?i)Examinations$|(?i)Prüfungen$")
        br.follow_link(text_regex=u"(?i)Semester Results$|(?i)Semesterergebnisse$")
        br.follow_link(text_regex=u"(?i)Module Results$|(?i)Modulergebnisse$")

        response = br.response().read()
        soup = BeautifulSoup(response, 'lxml')

        table = soup.find("table", {"class": "nb list"})
        table_rows = table.find_all('tr')
        grades = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.strip() for tr in td if tr.text.strip()]
            if row:
                row[4] = hashlib.md5(repr(row[:3]).encode('utf-8')).hexdigest()
                grades.append(row[:5])

        df_columns = ["No.", "Course Name", "Final grade", "Credits", "Hash"]
        df = pd.DataFrame(grades[1:], columns=df_columns)
        self.log.info("[*] Finished crawl")
        return df

    def notify(self, grade):
        ''' If a mailaddress is provided the user will get a notification sent to the specific address'''

        if self.mailaddress:
            self.log.info("[*] Notify User by email")
            fromaddr = self.mailaddress
            toaddr = self.mailaddress
            subject = '"[TUCAN] - New Grade Received"'
            body = json.dumps(grade)
            cmd = 'echo ' + body + ' | mail -s ' + subject + ' ' + fromaddr + ' ' + toaddr
            subprocess.call(cmd, shell=True)
            self.log.info("[*] Email sent")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",
                        action="store_true", dest="verbose",
                        help="increase output verbosity")
    parser.add_argument('-q', '--quiet',
                        action='store_true', dest="quiet",
                        help="Do not log unless it is critical")
    parser.add_argument("-l", "--log", type=str,
                        action="store", dest="log_path",
                        help="write log to file")
    parser.add_argument("-u", "--username", type=str,
                        action="store", required=True,
                        default=".",
                        help="Login username")
    parser.add_argument("-p", "--password", type=str,
                        action="store", required=True,
                        default=".",
                        help="Password")
    parser.add_argument("--database", type=str,
                        action="store", dest="data_path",
                        required=False, default="data",
                        help="Path to where to store the database")
    parser.add_argument("-m", "--mailaddress", type=str,
                        action="store", dest="mailaddress",
                        required=False,
                        help="Path to where to store the database")
    parser.add_argument("-i", "--interval", type=int,
                        action="store", dest="interval",
                        required=True,
                        help="The interval time to fetch new grades")

    args = parser.parse_args()

    def signal_handler(sig, frame):
        print('Exiting')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    GRADE_CRAWLER(args)
