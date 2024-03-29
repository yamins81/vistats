import os
import time
import flickrapi
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

        
def get_photo_data(**kwargs):
    attempts = 50
    wait_time = 60
    a = 0
    while a < attempts:
        try:
            data = get_photo_data_core(**kwargs)
        except flickrapi.FlickrError:
            time.sleep(wait_time)
            print('attempt', a)
            a += 1
        else:
            break
    return data
    
    
def get_photo_data_core(limit=500, tags=None, text=None, user_id=None, start=0, 
                   sort='relevance', tag_mode='all', get_other_tags=False, photoset_id=None, owner=None):
    flickr = flickrapi.FlickrAPI(API_KEY, SECRET)
    per_page_limit = 500
    start_page = start / per_page_limit
    if limit is not None:
        end_page = (start + limit) / per_page_limit
    else:
        end_page = None
    if get_other_tags:
        extras = 'tags,owner_name'
    else:
        extras = 'owner_name'
    if photoset_id is None:
        photos = flickr.walk(text=text, per_page=per_page_limit, tags=tags, user_id=user_id, 
                    start_page=start_page, end_page=end_page, tag_mode=tag_mode,
                    sort=sort, 
                    extras=extras
                   )
    else:
        photos = flickr.walk_set(photoset_id, per_page=per_page_limit, extras=extras)
    urls = []
    users = []
    ids = []
    tgs = []
    onames = []
    for p in photos:
        urls.append('http://farm%s.staticflickr.com/%s/%s_%s.jpg' % (p.attrib['farm'], p.attrib['server'], p.attrib['id'], p.attrib['secret']))
        print(p.attrib['id'])
        ids.append(p.attrib['id'])
        if owner is None:
            users.append(p.attrib['owner'])
        else:
            users.append(owner)
        if get_other_tags:
            tgs.append(p.attrib['tags'])
        onames.append(p.attrib['ownername'])
    if get_other_tags:
        return tb.tabarray(columns = [urls, users, ids, tgs, onames], names=['url', 'user_id', 'id', 'tags', 'owner_name'])
    else:
        return tb.tabarray(columns = [urls, users, ids, onames], names=['url', 'user_id', 'id','owner_name']) 
        
