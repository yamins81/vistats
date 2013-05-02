import flickrapi
import os
import tabular as tb

#app name:	Training Stimuli
#Key: 2e1c0d5d80a5e15cb5a0fb67b9dfbb83
#Secret: cd56eb479b42a154

API_KEY = u'2e1c0d5d80a5e15cb5a0fb67b9dfbb83'
SECRET = u'cd56eb479b42a154' 

def get_photos(limit=100, tags=None, text=None, user_id=None, start=0):
    dirname = (tags or text).replace(' ', '_')
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    flickr = flickrapi.FlickrAPI(API_KEY, SECRET)
    start_page = start / 100
    if limit is not None:
        end_page = (start + limit) / 100
    else:
        end_page = None
    photos = flickr.walk(text=text, tags=tags, user_id=user_id, 
                start_page=start_page, end_page=end_page)
    for p in photos:
        url = 'http://farm%s.staticflickr.com/%s/%s_%s.jpg' % (p.attrib['farm'], p.attrib['server'], p.attrib['id'], p.attrib['secret'])
        print url
        os.system('wget %s -P %s' % (url, dirname))

        
def get_photo_data(limit=100, tags=None, text=None, user_id=None, start=0):
    flickr = flickrapi.FlickrAPI(API_KEY, SECRET)
    per_page_limit = 500
    start_page = start / per_page_limit
    if limit is not None:
        end_page = (start + limit) / per_page_limit
    else:
        end_page = None
    photos = flickr.walk(text=text, per_page=per_page_limit, tags=tags, user_id=user_id, 
                start_page=start_page, end_page=end_page)
    urls = []
    users = []
    ids = []
    for p in photos:
        urls.append('http://farm%s.staticflickr.com/%s/%s_%s.jpg' % (p.attrib['farm'], p.attrib['server'], p.attrib['id'], p.attrib['secret']))
        print(p.attrib['id'])
        ids.append(p.attrib['id'])
        users.append(p.attrib['owner'])
    return tb.tabarray(columns = [urls, users, ids], names=['url', 'user_id', 'id'])
        
