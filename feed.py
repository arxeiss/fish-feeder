# import RPi.GPIO as GPIO
import time
import datetime
import requests
import logging
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def feed():
    time.sleep(0.15)

def doRequest(action = "", data = None):
    slug = os.environ.get("HEALTHCHECK_SLUG")
    if slug == "" or slug == None:
        logging.warning("No HealthCheck slug")
        return

    try:
        s = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        if action != "":
            action = "/"+action
        res = s.post('https://hc-ping.com/'+slug+'/feeding'+action, data=data)
        if res.status_code < 200 or res.status_code > 299:
            logging.warning("Failed to execute request: "+str(res.status_code))
    except Exception as e:
        logging.warning("Failed to execute request: "+repr(e))

def run():
    now = datetime.datetime.now()
    tomorrowRun = (now + datetime.timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

    with open('/var/feeder/next.run', 'a+') as f:
        f.seek(0)
        line = f.readline().strip()
        if line == "":
            logging.debug("No next.run file, creating: "+tomorrowRun)
            f.write(tomorrowRun)
            return

        nextRun = datetime.datetime.strptime(line, "%Y-%m-%d %H:%M:%S")
        if nextRun > now:
            logging.debug("Still in future, skipping")
            return

        logging.debug("Writing new time: "+tomorrowRun)
        f.truncate(0)
        f.write(tomorrowRun)

    logging.debug("Start feeding")

    doRequest('start')
    feed()
    doRequest()

    logging.debug("Feeding completed")

if __name__ == "__main__":
    logging.basicConfig(
        filename='feed.log', level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logging.getLogger("requests").setLevel(logging.WARNING)

    try:
        logging.debug("Script starting")
        run()
        logging.debug("Script finished")
        print("Done, bye")
    except Exception as e:
        doRequest('fail', repr(e))
        logging.error("Fail: "+ repr(e))
        print("Failed, bye")
