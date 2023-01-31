import RNS
import LXMF
import os
import redis
import shortuuid
import time

display_name = "SolarExpress Message Board"
configdir = "~/retic/"
identitypath = configdir+"storage/identity"

r = redis.Redis(db=2, decode_responses=True)

def setup_lxmf():

    if os.path.isfile(identitypath):
        identity = RNS.Identity.from_file(identitypath)
        RNS.log('Loaded identity from file', RNS.LOG_INFO)
    else:
        RNS.log('No Primary Identity file found, creating new...', RNS.LOG_INFO)
        identity = RNS.Identity()
        identity.to_file(identitypath)

    return identity

def lxmf_delivery(message):
    # Do something here with a received message
    RNS.log("A message was received: "+str(message.content.decode('utf-8')))

    message_content = message.content.decode('utf-8')

    source_hash_text = RNS.hexrep(message.source_hash, delimit=False)

    if r.exists(source_hash_text):
        uuid_user = r.get(source_hash_text)
    else:
        RNS.log('Generate new username', RNS.LOG_INFO)
        uuid_user = shortuuid.ShortUUID().random(length=12)
        r.set(source_hash_text, uuid_user)

        message_id = '{}_{}'.format(source_hash_text, time.time())
        r.set(message_id, 'Hi, your unique username is {}, this is linked to your nomad address'.format(uuid_user))
        r.lpush('message_queue', message_id)

    RNS.log('UUID: {}'.format(uuid_user), RNS.LOG_INFO)

    time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(message.timestamp))
    new_message = '{} {}: {}'.format(time_string, uuid_user, message_content)
    r.lpush('message_board_general', new_message)

    message_id = '{}_{}'.format(source_hash_text, time.time())
    r.set(message_id, 'Your message has been added to the messageboard')
    r.lpush('message_queue', message_id)

def announce_now(lxmf_destination):
    lxmf_destination.announce()

def send_message(destination_hash, message_content):
  try:
    # Make a binary destination hash from a hexadecimal string
    destination_hash = bytes.fromhex(destination_hash)

  except Exception as e:
    RNS.log("Invalid destination hash", RNS.LOG_ERROR)
    return

  # Check that size is correct
  if not len(destination_hash) == RNS.Reticulum.TRUNCATED_HASHLENGTH//8:
    RNS.log("Invalid destination hash length", RNS.LOG_ERROR)

  else:
    # Length of address was correct, let's try to recall the
    # corresponding Identity
    destination_identity = RNS.Identity.recall(destination_hash)

    if destination_identity == None:
      # No path/identity known, we'll have to abort or request one
      RNS.log("Could not recall an Identity for the requested address. You have probably never received an announce from it. Try requesting a path from the network first. In fact, let's do this now :)", RNS.LOG_ERROR)
      RNS.Transport.request_path(destination_hash)
      RNS.log("OK, a path was requested. If the network knows a path, you will receive an announce with the Identity data shortly.", RNS.LOG_INFO)

    else:
      # We know the identity for the destination hash, let's
      # reconstruct a destination object.
      lxmf_destination = RNS.Destination(destination_identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")

      # Create a new message object
      lxm = LXMF.LXMessage(lxmf_destination, local_lxmf_destination, message_content, title="Reply", desired_method=LXMF.LXMessage.DIRECT)

      # You can optionally tell LXMF to try to send the message
      # as a propagated message if a direct link fails
      lxm.try_propagation_on_fail = True

      # Send it
      message_router.handle_outbound(lxm)



# Start Reticulum and print out all the debug messages
reticulum = RNS.Reticulum(loglevel=RNS.LOG_EXTREME)

# Create a Identity.
current_identity = setup_lxmf()

# Init the LXMF router
message_router = LXMF.LXMRouter(identity = current_identity, storagepath = configdir)

# Register a delivery destination (for yourself)
# In this example we use the same Identity as we used
# to instantiate the LXMF router. It could be a different one,
# but it can also just be the same, depending on what you want.
local_lxmf_destination = message_router.register_delivery_identity(current_identity, display_name=display_name)

# Set a callback for when a message is received
message_router.register_delivery_callback(lxmf_delivery)

# Announce node properties

RNS.log('LXMF Router ready to receive on: {}'.format(RNS.prettyhexrep(local_lxmf_destination.hash)), RNS.LOG_INFO)

if r.exists('announce'):
    RNS.log('Recent announcement', RNS.LOG_INFO)
else:
    r.set('announce', 1)
    r.expire('announce', 1800)
    announce_now(local_lxmf_destination)
    RNS.log('Announcement sent, expr set 1800 seconds', RNS.LOG_INFO)

while True:

    for i in range(0, r.llen('message_queue')):
        message_id = r.lpop('message_queue')
        message = r.get(message_id)
        r.delete(message_id)
        destination_hash = message_id.split('_')[0]
        RNS.log('{} {}'.format(destination_hash, message), RNS.LOG_INFO)
        send_message(destination_hash, message)
    time.sleep(10)
