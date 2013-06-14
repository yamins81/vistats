import os
import json
from collections import OrderedDict

import numpy as np
import tabular as tb

import yamutils.fast as fast
import urllib2
import Image

import skdata.larray as larray
from skdata.data_home import get_data_home

import vistats.flickr_utils as flickr_utils

BRAND_QUERIES = OrderedDict([('chanel bag', {'label': 'chanel', 'text': 'chanel bag'}),
                             ('ford F150', {'label': 'ford', 'text': 'ford F150'}),
                             ('taco bell logo', {})
                             ])
                        

"""
chanel bag:
    jennydegroot
    shoppingdiva 44864232@N00
    ivysheng
    7950499@N05 (anjana Cawdell)
    nawalalkherejy
    marilym25
    midnightangel
    mikalovechanel
    
chanel logo
    79222200@N08 (zeusthegreatest)
    dolled_up_cupcakes
    0rangeya
    7516459@N04 (junkgarden)
    27339847@N06
    misswang 26857568@N04
    38675039@N02
    
chanel no 5
    67089783@N07 (Atelier 2A)
    37359607@N00 (Slimfit)
    nobleandroyal 87487791@N03
    srq2009 (Alex English)
    candiceelizabeth
    
    
Ford f150
    hartog
    travismphoto
    ilfirephotos
    chorwedel
    
ford escape
    harry_nl
    beryllium
    27816471@N06 (moon kebab)
    60020813@N05 (anthonywv)
    mixtiomedia
    juanelo242a
    writingfroggie
    andrewkim101

ford expedition
    talktrucks
    fordmx
    triborough
    69868413@N08
    cmarentes
    anthsrandomz
    78352455@N03
    stoicescu
    
taco bell
    paxtonholley
    abbsworth
    captinshmit

for each tag:
    get some image sfor that tag labelled as the tag
    get some images for each user for that tag, labelled as the tag
    get images for that user not for the tag, labelled as not-the-tag


"""

class FlickrTagUserDataset(object):
    def __init__(self):
        self.name = self.__class__.__name__
        self.flickr = flickr_utils.flickrapi.FlickrAPI(flickr_utils.API_KEY, 
                                                       flickr_utils.SECRET)

    @property
    def tag_images(self):
        if not hasattr(self, '_tag_images'):
            self.fetch()
            self._tag_images = self._get_tag_images()
        return self._tag_images
    
    def _get_tag_images(self):
        T = []
        if self.tags:
            t1 = flickr_utils.get_photo_data(tags=self.tags,
                   user_id=None,
                   limit=self.image_limit,
                   start=0, tag_mode='all', sort='relevance')
            t1 = t1.addcols([[self.tags]*len(t1)], names=['source'])
            T.append(t1)
        for _t in self.text.split(','):
            t = flickr_utils.get_photo_data(text=_t,
                   user_id=None,
                   limit=self.image_limit,
                   start=0, tag_mode='all', sort='relevance')
            t = t.addcols([[_t]*len(t)], names=['source'])
            T.append(t)
        return tb.tab_rowstack(T)

    @property
    def tag_users(self):
        if not hasattr(self, '_tag_users'):
            self.fetch()
            self._tag_users = self._get_tag_users()
        return self._tag_users
    
    def _get_tag_users(self):
        tag_images = self.tag_images
        atags = tag_images[['user_id', 'url', 'source']].aggregate(On=['user_id'], AggFuncDict={'url': len, 'source': lambda x : x[0]})
        atags.sort(order=['url'])
        num_users = self.num_users
        users = atags[['user_id', 'source']]
        if hasattr(self, 'bad_users'):
            good_inds = np.array([_i for _i in range(len(users)) if users[_i]['user_id'] not in self.bad_users])
            users = users[good_inds]
        users = users[-num_users:]
        return users
    
    @property
    def tag_users_images(self):
        if not hasattr(self, '_tag_users_images'):
            self.fetch()
            self._tag_users_images = self._get_tag_users_images()
        return self._tag_users_images

    def _get_tag_users_images(self):
        users = self.tag_users
        Ds = []
        flickr = self.flickr
        for u in users:
            d1 = flickr_utils.get_photo_data(tags=None, text=None,
                   user_id=u['user_id'],
                   limit=self.user_limit,
                   start=0, tag_mode='all', sort='relevance')
            d2 = flickr_utils.get_photo_data(tags=None, text=self.tag_in_text,
                   user_id=u['user_id'],
                   limit=self.user_limit,
                   start=0, tag_mode='all', sort='relevance')
   
            usets = json.loads(flickr.photosets_getList(user_id=u['user_id'], format='json'))['photosets']['photoset']
            titles = [_s['title']['_content'] for _s in usets]
            usetids = [_s['id'] for _s in usets]
            descriptions =  [_s['description']['_content'] for _s in usets]
            relevant = [_i for _i in range(len(usets)) if (self.tag_in_text in descriptions[_i].lower()  or self.tag_in_text in titles[_i].lower())]
            if relevant:
                d3s = []
                for _i in relevant:
                    print('getting set %s for user %s' % (titles[_i], u))
                    _d3 = flickr_utils.get_photo_data(photoset_id=usetids[_i], owner=u, limit=None, start=0, tag_mode='all', sort='relevance')
                    d3s.append(_d3)
                d3 = tb.tab_rowstack(d3s)
                d3 = d3.addcols([np.array([1]*len(d3)).astype(np.int)], names=['Tag'])                            
                d1 = d1[np.invert(fast.isin(d1['id'], d2['id'])) & np.invert(fast.isin(d1['id'], d3['id']))]
                d1 = d1.addcols([np.array([0]*len(d1)).astype(np.int)], names=['Tag'])
                d2 = d2.addcols([np.array([1]*len(d2)).astype(np.int)], names=['Tag'])   
                if self.add_tagtext_images:
                    d = tb.tab_rowstack([d1, d2, d3])
                else:
                    d = d1
            else:
                d1 = d1[np.invert(fast.isin(d1['id'], d2['id']))]
                d1 = d1.addcols([np.array([0]*len(d1)).astype(np.int)], names=['Tag'])
                d2 = d2.addcols([np.array([1]*len(d2)).astype(np.int)], names=['Tag'])
                if self.add_tagtext_images:
                    d = tb.tab_rowstack([d1, d2])
                else:
                    d = d1
            d = d.addcols([[u['source']]*len(d)], names=['source'])
            Ds.append(d)
            
        return tb.tab_rowstack(Ds)

    def fetch(self):
        pass
        
    def home(self, *suffix_paths):
        return os.path.join(get_data_home(), 'Flickr', self.name, *suffix_paths)
    
    @property
    def metapath(self):
        return self.home('metadata.tsv')
        
    def _get_meta(self):
        metapath = self.metapath
        metadir = os.path.dirname(metapath)
        if not os.path.isdir(metadir):
            os.makedirs(metadir)
        if not os.path.isfile(metapath):
            tag_images = self.tag_images
            users = self.tag_users
            m1 = self.tag_users_images
            m1['Tag'] = m1['Tag'] | fast.isin(m1['id'], tag_images['id'])                                       
            m2 = tag_images[np.invert(fast.isin(tag_images['id'], m1['id']))]
            #m2 = m2[fast.isin(m2['user_id'], users['user_id'])]
            m2 = m2.addcols([[1]*len(m2)], names=['Tag'])
            meta = tb.tab_rowstack([m1, m2])            
            if hasattr(self, 'bad_users'):
                good_inds = np.array([_i for _i in range(len(meta)) if meta[_i]['user_id'] not in self.bad_users])
                meta = meta[good_inds]
            resource_home = self.home('resources')
            filenames = [self.home('resources', ('Tag_' if t else 'NoTag_') + uid + '_' + u.split('/')[-1]) for t, u, uid in zip(meta['Tag'], meta['url'], meta['user_id'])]
            meta = meta.addcols([filenames], names=['filename'])
            meta = meta.aggregate(On=['url'], AggFunc=lambda x: x[0])
            meta.saveSV(metapath, metadata=True)
        meta = tb.tabarray(SVfile=metapath)
        return meta
        
    @property
    def meta(self):
        if not hasattr(self, '_meta'):
            self.fetch()
            self._meta = self._get_meta()
        return self._meta
        
    def get_images(self, preproc):
        dtype = preproc['dtype']
        mode = preproc['mode']
        size = tuple(preproc['size'])
        normalize = preproc['normalize']

        return larray.lmap(FlickrImgDownloaderResizer(
                                            shape=size,
                                            dtype=dtype,
                                            normalize=normalize,
                                            mode=mode),
                                self.meta[['url', 'filename']])
     
    def download_images(self, inds=None):
        if inds is None:
            inds = range(len(self.meta))
        for rec in self.meta[inds]:        
            lpath = rec['filename']
            url = rec['url']
            dirname = os.path.dirname(lpath)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            if not os.path.isfile(lpath):
                a = 0
                attempts = 10
                while True:
                    try:
                        with open(lpath, 'w') as _f:
                            fp = urllib2.urlopen(url)
                            print(url, lpath)
                            _f.write(fp.read())
                    except:
                        a += 1
                        print('attempt', a)
                    else:
                        break
                    if a >= attempts:
                        break
                    
                
        
        
#########################
##########Tests##########
#########################

class FlickrTagUserDatasetChanel(FlickrTagUserDataset):
    tags=''
    text = 'chanel flap bag, chanel tote, chanel shoes, chanel handbags, chanel jumbo bag, chanel no 5, chanel bag, chanel logo, chanel tote, chanel bags'
    num_users = 30
    user_limit = 3000
    image_limit = 3000
    

class FlickrTagUserDatasetChanelTest(FlickrTagUserDatasetChanel):
    num_users = 2
    user_limit = 200
    image_limit = 200


class FlickrTagUserDatasetMcDonaldsTestOld(FlickrTagUserDataset):
    tags=''
    text = "McDonald's burger,mcdonald's milkshake,mcdonald's arches,big mac burger"
    num_users = 2
    user_limit = 200
    image_limit = 200


class FlickrTagUserDatasetCocaColaTest(FlickrTagUserDataset):
    tags=''
    text = "coke can,coke bottle,classic coca cola drink,coke zero can,cherry coke can"
    num_users = 2
    user_limit = 200
    image_limit = 200



##########################
##########Chanel##########
##########################

class FlickrTagUserDatasetChanelMakeupTest(FlickrTagUserDataset):
    tags='chanel foundation,chanel hydramax'
    text = 'chanel sublimage,chanel hydramax,chanel nail polish,chanel le vernis,chanel lipstick,chanel levres scintillantes,chanel eyeshadow,chanel faoundation'
    num_users = 10
    user_limit = 200
    image_limit = 200
    tag_in_text='chanel'
    bad_users = ['67158843@N00']
    add_tagtext_images = False


class FlickrTagUserDatasetChanelFragrance(FlickrTagUserDataset):
    tags=''
    text = 'chanel "No. 5","chanel No 5","chanel fragrance","chanel perfume","chanel chance","chanel allure","bleu de chanel" fragrance'
    num_users = 50
    user_limit = 1000
    image_limit = 15000
    tag_in_text='chanel'
    bad_users = ['40795211@N00','43102195@N08','14605079@N04','23049244@N04','31300603@N06']
    add_tagtext_images = False
    
    
class FlickrTagUserDatasetChanelShoes(FlickrTagUserDataset):
    tags=''
    text = '"chanel shoe","chanel flat",chanel espadrille,"chanel clog","chanel heels","chanel pump","chanel high heel","chanel boot","chanel sandal",chanel "ballet flat","chanel loafer"'
    num_users = 50
    user_limit = 1000
    image_limit = 15000
    tag_in_text='chanel'
    bad_users = ['27826934@N05','32083515@N04','36619928@N08','28510667@N07','34401099@N06']
    add_tagtext_images = False


class FlickrTagUserDatasetChanelJewelry(FlickrTagUserDataset):
    tags=''
    text = '"chanel necklace","chanel earring","chanel camelia","chanel watch","chanel bracelet"'
    num_users = 50
    user_limit = 1000
    image_limit = 15000
    tag_in_text='chanel'
    bad_users = []
    add_tagtext_images = False


class FlickrTagUserDatasetChanelBag(FlickrTagUserDataset):
    tags=''
    text = '"chanel logo","chanel flap","flap bag" chanel,"chanel tote","chanel handbag","chanel jumbo","chanel bag","chanel purse","chanel clutch","coco cocoon",chanel "key case","chanel wallet",chanel "cc logo"'
    num_users = 50
    user_limit = 1000
    image_limit = 15000
    tag_in_text='chanel'
    bad_users = ['74635508@N04', '61276641@N07','67158843@N00', '57952699@N08','26814259@N04','88701127@N00','43102195@N08','39366895@N02','26814259@N04','40149686@N03','39681628@N02', '93762672@N02','47063161@N08', '10192717@N03', '16446436@N00','20383131@N00', '38462806@N04', '30911898@N04','40745917@N02', '42293676@N08','63917432@N07']
    add_tagtext_images = False


class FlickrTagUserDatasetChanelOverall(FlickrTagUserDataset):
    tags = ''
    text = ','.join([FlickrTagUserDatasetChanelBag.text, 
                     FlickrTagUserDatasetChanelFragrance.text,
                     FlickrTagUserDatasetChanelJewelry.text,
                     FlickrTagUserDatasetChanelShoes.text])
    num_users = 50
    user_limit = 1000
    image_limit = 15000
    tag_in_text = 'chanel'
    bad_users = FlickrTagUserDatasetChanelBag.bad_users + \
                FlickrTagUserDatasetChanelFragrance.bad_users + \
                FlickrTagUserDatasetChanelJewelry.bad_users + \
                FlickrTagUserDatasetChanelShoes.bad_users + ['38386646@N07','38462806@N04', '60024371@N08','62912952@N07','75678112@N07']
    add_tagtext_images = False


class FlickrTagUserDatasetChanelPurseTest0(FlickrTagUserDataset):
    tags=''
    text = 'chanel purse'
    num_users = 50
    user_limit = 1000
    image_limit = 1500
    tag_in_text='chanel'
    bad_users = ['74635508@N04', '61276641@N07','67158843@N00', '57952699@N08','26814259@N04','88701127@N00','43102195@N08','39366895@N02','26814259@N04','40149686@N03','39681628@N02', '93762672@N02','47063161@N08', '10192717@N03', '16446436@N00','20383131@N00', '38462806@N04']
    add_tagtext_images = False


class FlickrTagUserDatasetChanelPurseTest1(FlickrTagUserDataset):
    tags=''
    text = '"chanel purse"'
    num_users = 50
    user_limit = 1000
    image_limit = 1500
    tag_in_text='chanel'
    bad_users = ['74635508@N04', '61276641@N07','67158843@N00', '57952699@N08','26814259@N04','88701127@N00','43102195@N08','39366895@N02','26814259@N04','40149686@N03','39681628@N02', '93762672@N02','47063161@N08', '10192717@N03', '16446436@N00','20383131@N00', '38462806@N04']
    add_tagtext_images = False



############mcdonalds

class FlickrTagUserDatasetMcDonaldsOverall(FlickrTagUserDataset):
    tags=''
    text = 'mcdonalds,"big mac",mcdonalds salad,mcdonalds fries,mcdonalds mcwrap,mcdonalds "chicken nuggets",mcdonalds mcnuggets,"egg mcmuffin",mcflurry,"mcdonalds milkshake",mccafe,mcdonalds coffee,"mcdonalds storefront","mcdonalds bags",mcdonalds trash,mcdonalds "golden arches",mcdonalds garbage,mcdonalds wifi,"ronald mcdonald",mcdonalds "ice cream",mcdonalds china,mcdonalds japan,mcdonalds paris,"mcdonalds breakfast","mcdonalds logo"'
    num_users = 50
    user_limit = 1000
    image_limit = 10000
    tag_in_text="mcdonald"
    bad_users = []
    add_tagtext_images = False
    

    
#########################
##########Utils##########
#########################

class FlickrImgDownloaderResizer(object):
    """
    """
    def __init__(self,
                 shape=None,
                 ndim=None,
                 dtype='float32',
                 normalize=True,
                 mode='L'
                 ):
        shape = tuple(shape)
        self._shape = shape
        if ndim is None:
            self._ndim = None if (shape is None) else len(shape)
        else:
            self._ndim = ndim
        self._dtype = dtype
        self.normalize = normalize
        self.mode = mode

    def rval_getattr(self, attr, objs):
        if attr == 'shape' and self._shape is not None:
            return self._shape
        if attr == 'ndim' and self._ndim is not None:
            return self._ndim
        if attr == 'dtype':
            return self._dtype
        raise AttributeError(attr)

    def __call__(self, rec):
        lpath = rec['filename']
        url = rec['url']
        dirname = os.path.dirname(lpath)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        if not os.path.isfile(lpath):
            with open(lpath, 'w') as _f:
                fp = urllib2.urlopen(url)
                print(url, lpath)
                _f.write(fp.read())
        im = Image.open(lpath)
        if im.mode != self.mode:
            im = im.convert(self.mode)
        if im.size != self._shape[0]:
            m0 = self._shape[0]/float(im.size[0])
            m1 = self._shape[1]/float(im.size[1])
            new_shape = (int(round(im.size[0]*m0)), int(round(im.size[1]*m1)))
            im = im.resize(new_shape, Image.ANTIALIAS)
        rval = np.asarray(im, self._dtype).swapaxes(0, 1)
        if self.normalize:
            rval -= rval.mean()
            rval /= max(rval.std(), 1e-3)
        else:
            if 'float' in str(self._dtype):
                rval /= 255.0
        assert rval.shape == self._shape, (rval.shape, self._shape)
        return rval
