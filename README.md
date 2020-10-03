# TUCAN Grade Crawler

This tool searches at intervals for the latest grades from the TU Darmstadt campus management website and stores them locally in a database. If desired, an e-mail address can be added to the execution in order to get notified by e-mail for each updated grade.

## Setup

Docker Images:
* python:3-slim-buster

Python:
* Crawling & Notification Script

## Getting Started

### Run Dockerized

#### Prerequisites

* An installation of [Docker](https://www.docker.com/) and [docker-compose](https://docs.docker.com/compose/) is required in order to run the project.

* Update arguments in [Dockerfile](Dockerfile)

#### Setup docker container:

By running the following command from the root directory of the project all needed docker images should be downloaded and containers started in the correct order:

```bash
docker-compose up
```

In order to run the setup daemonized, execute the following command:

```bash
docker-compose up -d
```

To stop a daemonized start, execute the following command:

```bash
docker-compose down
```

Rebuild the docker after updating script/dockerfile:

```bash
docker-compose build
```

### Run from scratch

> sudo apt-get install python3 python3-virtualenv <br>
> python3 -m venv venv <br>
> source venv/bin/activate <br>
> pip3 install -r requirements.txt


## Usage

```none
usage: tucan_grade_notifier.py [-h] [-v] [-q] [-l LOG_PATH] -u USERNAME -p PASSWORD [--database DATA_PATH] [-m MAILADDRESS] -i INTERVAL

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           Do not log unless it is critical
  -l LOG_PATH, --log LOG_PATH
                        write log to file
  -u USERNAME, --username USERNAME
                        Login username
  -p PASSWORD, --password PASSWORD
                        Password
  --database DATA_PATH  Path to where to store the database
  -m MAILADDRESS, --mailaddress MAILADDRESS
                        Path to where to store the database
  -i INTERVAL, --interval INTERVAL
                        The interval time to fetch new grades

```

### Example

> ./tucan_grade_notifier.py -l debug.log --username uniquetuid --password strongpassword! --interval 60 --mailaddress me@webmail.com
