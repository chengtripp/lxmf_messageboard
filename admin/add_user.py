import RNS.vendor.umsgpack as msgpack
import os, sys

#Setup Paths and Config Files
userdir = os.path.expanduser("~")

if os.path.isdir("/etc/nomadmb") and os.path.isfile("/etc/nomadmb/config"):
    configdir = "/etc/nomadmb"
elif os.path.isdir(userdir+"/.config/nomadmb") and os.path.isfile(userdir+"/.config/nomadmb/config"):
    configdir = userdir+"/.config/nomadmb"
else:
    configdir = userdir+"/.nomadmb"

storagepath  = configdir+"/storage"
if not os.path.isdir(storagepath):
    os.makedirs(storagepath)

allowedpath = configdir+"/storage/allowed"

allowed_list = []
if os.path.isfile(allowedpath):
    f = open(allowedpath, "rb")
    allowed_list = msgpack.unpack(f)
    f.close()
else:
    print('No file')

new_user = input('Add User: ')
allowed_list.append(new_user)

f = open(allowedpath, "wb")
msgpack.pack(allowed_list, f)
f.close()
