#!/bin/python3
import time
import redis
r = redis.Redis(db=2, decode_responses=True)

print('`!`F222`Bddd`cSolarExpress Message Board')

print('-')
print('`a`b`f')
print("")
print("To add a message to the board just converse with the SolarExpress Message Board at <ad713cd3fedf36cc190f0cb89c4be1ff>, peers are assigned a unique username")
print("Built with Python and Redis")
time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
print("Last Updated: {}".format(time_string))
print("")
print('>Messages')
print("  Date       Time    Username     Message")
for i in range(0, r.llen('message_board_general')):
    message_content = r.lindex('message_board_general', i)
    print("`a{}".format(message_content))
    print("")
