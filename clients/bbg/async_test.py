import time
import asyncio
import aiohttp
import datetime as dt




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
            #async with self.session.post(self.url + "/bbg", json = {"ping": "hello"}) as resp:
            async with self.session.get(self.url + "/bbg", timeout = 3) as resp:
                print(Fore.GREEN, "----------------", Style.RESET_ALL)
                print(Fore.GREEN, resp.text, Style.RESET_ALL)
        else:
            pass

    async def poll_runner(self):
        while True:
            print("runner")
            await asyncio.sleep(self.poll_secs)
            await self.dispatch("ping")



async def main():
    poller = Poller()
    while True:
        await(asyncio.sleep(10))


if __name__ == "__main__":
    yes_async = True
    if yes_async:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
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
