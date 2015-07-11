import os
import os.path as osp
import boto3

local_dir = '/usr/src/app/blog/html'
local_data = {}


# ugh, "good enough"
def get_content_type(fname):
    if fname.endswith('.html'):
        return 'text/html'
    elif fname.endswith('.css'):
        return 'text/css'
    elif fname.endswith('.js'):
        return 'application/javascript'
    elif fname.endswith('.jpg'):
        return 'image/jpeg'
    elif fname.endswith('.png'):
        return 'image/png'
    elif fname.endswith('.gif'):
        return 'image/gif'
    elif fname.endswith('.bmp'):
        return 'image/bmp'
    else:
        return 'binary/octet-stream'


for root, dirs, files in os.walk(local_dir):
    for f in files:
        fname = osp.join(root, f)
        key = osp.relpath(fname, local_dir)
        local_data[key] = open(fname, 'rb')

print '%s files to upload...' % len(local_data)

s3 = boto3.resource('s3')
bucket = s3.Bucket('psftw.com')
objects = bucket.objects.all()

# delete leftover content
for o in objects:
    if o.key not in local_data:
        print 'removing %s' % o.key
        o.delete()
    else:
        o.put(ACL='public-read', Body=local_data[o.key].read(),
              ContentType=get_content_type(o.key))
        del local_data[o.key]

for key in local_data:
    bucket.put_object(Key=key, Body=local_data[key].read(),
                      ContentType=get_content_type(key))

print 'upload complete!'
