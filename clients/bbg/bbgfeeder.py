import time
import asyncio
import aiohttp
import datetime as dt

from argparse import ArgumentParser, RawTextHelpFormatter

#from blpapi_import_helper import blpapi

from util.SubscriptionOptions import \
    addSubscriptionOptions, \
    setSubscriptionSessionOptions
from util.ConnectionAndAuthOptions import \
    addConnectionAndAuthOptions, \
    createSessionOptions

from colorama import Fore, Back, Style, init as colorinit; colorinit()

from pprint import pprint

DEFAULT_QUEUE_SIZE = 10000
DEFAULT_SERVICE = "//blp/mktdata"
DEFAULT_TOPIC_PREFIX = "/ticker/"
DEFAULT_TOPIC = ["BTC Curncy", "ETH Curncy"]


def create_subscription_list(tickers, options):
    """dstreams take on creating a subscription list. Does not go via 
    the options object """
    subscriptions = blpapi.SubscriptionList()
    correls = {}
    for ticker in tickers:
        correlid = blpapi.CorrelationId(ticker)
        subscriptions.add(ticker, options.fields, options.options, correlid)
        correls[ticker] = correlid
    return subscriptions, correls


def create_unsubscription_list(correls, options):
    """ unsubscribe list including correlations """
    subscriptions = blpapi.SubscriptionList()
    for ticker, correlid in correls.items():
        subscriptions.add(ticker, options.fields, options.options, correlid)
    return subscriptions


def createSubscriptionList(options):
    """
    Creates a SubscriptionList from the following command line arguments:
    - topic names
    - service name
    - fields to subscribe to
    - subscription options
    - subscription interval
    """
    if not options.topics:
        options.topics = DEFAULT_TOPIC

    if options.interval:
        options.options.append(f"interval={options.interval}")

    subscriptions = blpapi.SubscriptionList()
    for topic in options.topics:
        correlid = blpapi.CorrelationId(topic)
        subscriptions.add(topic,
                          options.fields,
                          options.options,
                          blpapi.CorrelationId(topic))
    return subscriptions


class SubscriptionEventHandler(object):

    def __init__(self):
        self.yesprint = True

    def getTimeStamp(self):
        return time.strftime("%Y/%m/%d %X")

    def processSubscriptionStatus(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            topic = msg.correlationId().value()
            print(f"{timeStamp}: {topic}")
            print(msg)
            if msg.messageType() == blpapi.Names.SUBSCRIPTION_FAILURE:
                print(f"Subscription for {topic} failed")
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_TERMINATED:
                # Subscription can be terminated if the session identity
                # is revoked.
                print(f"Subscription for {topic} TERMINATED")

    def search_msg(self, msg, fields):
        for field in fields:
            if msg.hasElement(field):
                return (field, msg[field])
        return ()

    def processSubscriptionDataEvent(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            topic = msg.correlationId().value()
            if self.yesprint:
                print(f"{timeStamp}: {topic} {self.search_msg(msg, ['LAST_PRICE', 'PX_BID'])}")

    def processMiscEvents(self, event):
        for msg in event:
            if msg.messageType() == blpapi.Names.SLOW_CONSUMER_WARNING:
                print(f"{blpapi.Names.SLOW_CONSUMER_WARNING} - The event queue is " +
                      "beginning to approach its maximum capacity and " +
                      "the application is not processing the data fast " +
                      "enough. This could lead to ticks being dropped" +
                      " (DataLoss).\n")
            elif msg.messageType() == blpapi.Names.SLOW_CONSUMER_WARNING_CLEARED:
                print(f"{blpapi.Names.SLOW_CONSUMER_WARNING_CLEARED} - the event " +
                      "queue has shrunk enough that there is no " +
                      "longer any immediate danger of overflowing the " +
                      "queue. If any precautionary actions were taken " +
                      "when SlowConsumerWarning message was delivered, " +
                      "it is now safe to continue as normal.\n")
            elif msg.messageType() == blpapi.Names.DATA_LOSS:
                print(msg)
                topic = msg.correlationId().value()
                print(f"{blpapi.Names.DATA_LOSS} - The application is too slow to " +
                      "process events and the event queue is overflowing. " +
                      f"Data is lost for topic {topic}.\n")
            elif event.eventType() == blpapi.Event.SESSION_STATUS:
                # SESSION_STATUS events can happen at any time and
                # should be handled as the session can be terminated,
                # e.g. session identity can be revoked at a later
                # time, which terminates the session.
                if msg.messageType() == blpapi.Names.SESSION_TERMINATED:
                    print("Session terminated")
                    return

    def processEvent(self, event, _session):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                self.processSubscriptionDataEvent(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                self.processSubscriptionStatus(event)
            else:
                self.processMiscEvents(event)
        except blpapi.Exception as exception:
            print(f"Failed to process event {event}: {exception}")
        return False


def parseCmdLine():
    """Parse command line arguments"""

    parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                            description="Asynchronous subscription with event handler")
    addConnectionAndAuthOptions(parser)
    addSubscriptionOptions(parser)

    parser.add_argument(
        "-q",
        "--event-queue-size",
        dest="eventQueueSize",
        help="The maximum number of events that is buffered by the session (default: %(default)d)",
        type=int,
        metavar="eventQueueSize",
        default=DEFAULT_QUEUE_SIZE)

    options = parser.parse_args()

    return options


def bbg_main():
    options = parseCmdLine()
    sessionOptions = createSessionOptions(options)
    setSubscriptionSessionOptions(sessionOptions, options)
    sessionOptions.setMaxEventQueueSize(options.eventQueueSize)
    handler = SubscriptionEventHandler()
    session = blpapi.Session(sessionOptions, handler.processEvent)

    try:
        if not session.start():
            print("Failed to start session.")
            return

        if not session.openService(options.service):
            print("Failed to open service.")
            return

        subscriptions = createSubscriptionList(options)
        correls = [subscriptions.correlationIdAt(x) for x in range(subscriptions.size())]
        tickers = [subscriptions.topicStringAt(x) for x in range(subscriptions.size())]
        correlations = dict(zip(tickers, correls))
        session.subscribe(subscriptions)
        nowtime = dt.datetime.utcnow()
        unsubed = False
        unresubed = False
        while True:
            time.sleep(0.5)
            if (dt.datetime.utcnow() - nowtime).total_seconds() > 5:
                if not unsubed: 
                    handler.yesprint = False
                    unsub = {t: c for t, c in correlations.items() if t in ["ETH Curncy"]}
                    #TODO
                    print("---------------------------")
                    print(unsub)
                    #TODO: this unsub is returning tickers and fields in dict keys
                    #TODO: investigate if fields are independent of tickers when subscribing
                    #TODO: by subscribg separate to ticker1:field1 and ticker2:fielder2 

                    unsub = create_unsubscription_list(unsub, options)
                    session.unsubscribe(unsub)
                    unsubed = True
            if (dt.datetime.utcnow() - nowtime).total_seconds() > 10:
                if not unresubed:
                    print("---------------------------")
                    sub, correls = create_subscription_list(["ETH Curncy"], options)
                    session.subscribe(sub)
                    unresubed = True

    finally:
        session.stop()


# ------------- async ---------------

# TODO 
# argparse sub_max, poll_secs, url, id etc



class Poller(): 
    def __init__(self, 
            url = "http://suprabonds.com",     # server url
            poll_secs = 2,                     # poll every 
            sub_max = 100, 
            b_id = "bloomer1"):
        self.url = url
        self.poll_secs = poll_secs
        self.sub_max = sub_max
        self.b_id = b_id
        self.session = aiohttp.ClientSession()
        self.sub_list = []
        self.runner_task = asyncio.create_task(self.poll_runner())

    async def dispatch(self, command, parameters = None):
        """ dispatch commands to correct place """
        if command == "ping":
            print("ping", dt.datetime.utcnow())
            async with self.session.post(self.url + "/bbg", data = b"hello") as resp:
                print(Fore.GREEN, resp.text, Style.RESET_ALL)
        else:
            pass
        self.runner_task = asyncio.create_task(self.poll_runner())

    async def poll_runner(self):
        while True:
            await syncio.sleep(self.poll_secs)
            await self.dispatch("ping")



async def main():
    poller = Poller()
    input("Press Enter to end...")


if __name__ == "__main__":
    yes_async = True
    if yes_async:
        asyncio.run(main())
    else:
        try:
            bbg_main()
        except Exception as e:  # pylint: disable=broad-except
            print(e)


__copyright__ = """
Copyright 2021, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""
