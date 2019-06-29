# bot

This repo contains the bot subsystem of the Human-firewall project.
The code was written using Python3 and makes extensive use of the [python-telegram-bot library](https://github.com/python-telegram-bot/python-telegram-bot) and of the [Eclipse Paho MQTT client](https://www.eclipse.org/paho/).

## Features

This bot provides the following feature using the Telegram's APIs:
- Management of user's intercoms (add, delete)
- Notify users of the identity of the subject that rings their doorbell
- Retrieval of the user feedback about subject's identity

The bot also takes care of notifying the "slaves" systems of the user feedback through the use of a MQTT queue.

## How to use 

```
# Initialization
bot = Bot("your_telegram_token","mqtt_broker_ip")
bot.start() # start bot and its threads - non-blocking call

# Notify users
bot.send_notification(board_id, encoding, feedback, photo, has_face=True) # send notification to the house-owners

# Restart
bot.token = "different_telegram_token"
bot.ip_broker = "different_mqtt_broker"
bot.restart() # you can use this to apply changes to finalize the changes to the bot's configuration

# Kill it
bot.stop()

```

I highly suggest you to check the [master system repo](https://github.com/humanfirewall-iot19/master) to see how the bot subsystem was used in conjuction with the other modules of our project.

## Dependencies

For the full list of dependencies refer to the [requirements file](requirements.txt)
