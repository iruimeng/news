#-*- coding:utf-8 -*-
# author: zhaozhi
from datetime import datetime
import requests, re
import os
from urlparse import urlparse
from PIL import Image
import cStringIO
from dateutil.parser import parse as parseDateString
from config import logger
#
def parseDateStr(dateStr):
    ret = None
    if dateStr != "":
        fmts = [
            "%B %d, %Y",  #vice, infowars, mic, spin
            "%m/%d/%y %H:%M%p", #kotaku, lifehacker, deadspin, gawker
            "%b %d, %Y %H:%M%p", #elitedaily
            "%Y-%m-%d", #eonline, etonline
            "%Y%m%d%H", #hollywoodreporter
            "%B %d, %Y | %H:%M%p", #pagesix
            "%d %b %Y at %H:%M", #rawstory
            "%m.%d.%y %H:%M %p", #thedailybeast
            "%b %d, %Y %H:%M %p", #townhall
            "%B %d, %Y @ %H:%M %p", #usmagazine
        ]

        for fmt in fmts:
            try:
                ret = datetime.strptime(dateStr, fmt)
                break
            except ValueError, e:
                logger.warn( u"parse `%s` error: %s", dateStr,e)
        if ret == None:
            #最后求助dateutil
            try:
                ret = parseDateString(dateStr, fuzzy=True)
            except Exception, e:
                logger.warn( u"parse `%s` error:%s", dateStr, e)
    return ret


class ImageProcessor(object):

    def __init__(self, target_dir, relative_path="", target_sizes=None):
        '''
        :param target_dir: 图片存储的系统目录
        :param relative_path: target_dir下的相对路径, 没有/开头会自动加上,用于返回结果
        :param target_sizes: 要裁剪的图片尺寸
        '''
        self.target_dir = os.path.join(target_dir, relative_path.lstrip("/") )
        self.relative_path = relative_path if relative_path.find("/") == 0 else "/" + relative_path
        self.target_sizes = target_sizes
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

    def save(self, url, fname_prefix=""):
        resp = None
        ret = {}
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36"}
            resp = requests.get(url, headers=headers)
        except Exception, e:
            logger.error( "read image from %s, error: %s", url, str(e))
            return ret
        if resp.status_code == 200:
            img = None
            try:
                img = Image.open(cStringIO.StringIO(resp.content))
            except Exception, e:
                logger.error( "open image from `%s` error: %s", url, e)
                return ret
            #获取扩展名
            urlobj = urlparse(url)
            fname, ext = os.path.splitext(urlobj.path)
            if ext == "":
                ext = img.format.lower()
            else:
                ext = ext.lstrip(".")
            if fname_prefix != "":
                fname_prefix += "-"
            if self.target_sizes != None:
                #截图
                for sz_name, size in self.target_sizes.iteritems():
                    if sz_name =="middle":
                        sub_img = self.resizeImage(img.copy(), size[0])
                    else:
                        sub_img = self.cropImage(img.copy(), size[0], size[1])
                    fname = "%s%s.%s"%(fname_prefix, sz_name, ext)
                    fpath = os.path.join(self.target_dir, fname)
                    try:
                        sub_img.save(fpath)
                        ret[sz_name] = os.path.join(self.relative_path, fname)
                    except Exception, e:
                        logger.error("save %s error: %s", fpath, str(e))
            fname = "%s.%s" % (fname_prefix.rstrip("-"), ext)
            fpath = os.path.join(self.target_dir, fname )
            try:
                img.save( fpath )
                ret["origin"] = os.path.join(self.relative_path, fname)
            except Exception, e:
                logger.error( "save %s error: %s", fpath, str(e))
        else:
            logger.error( "get image '%s' failed, status code:%d", url, resp.status_code)
        return ret

    def cropImage(self, imageObj, target_width, target_height ):
        origin_width, origin_height = imageObj.size

        resize_width, resize_height = origin_width, origin_height
        target_ratio = target_width * 1.0 / target_height
        origin_ratio = origin_width * 1.0 / origin_height
        if origin_ratio > target_ratio:
            #原图比较宽
            resize_width = int(1.0 * resize_height * target_width / target_height)
        elif origin_ratio < target_ratio:
            #原图比较高
            resize_height = int(round(1.0 * resize_width * target_height / target_width, 0))

        left = max( (origin_width - resize_width) / 2, 0)
        top = max( (origin_height - resize_height) / 2, 0)
        right = left + resize_width
        bottom = top + resize_height
        #按比例裁剪
        imageObj = imageObj.crop((left, top, right, bottom))
        #缩放
        sub = imageObj.resize((target_width, target_height), Image.LANCZOS)
        return  sub

    def resizeImage(self, imageObj, target_width):
        origin_width, origin_height = imageObj.size

        if origin_width<target_width:
            return imageObj
        else:
            target_height = origin_height * target_width / origin_width

        #
        sub = imageObj.resize((target_width, target_height), Image.LANCZOS)
        return  sub

if __name__ == "__main__":
    IMAGE_SIZES = {
        "large": (680, 382),
        "middle": (720, 0),
        "small": (113*2, 75*2),
    }
    img_processor = ImageProcessor("./", target_sizes=IMAGE_SIZES)
    img_processor.save("http://2d0yaz2jiom3c6vy7e7e5svk.wpengine.netdna-cdn.com/wp-content/uploads/2016/08/Freeport-Bakery-trans-Ken-cake-KTXL-TV-800x430.jpg", fname_prefix="test")
    img_processor.save("http://static2.businessinsider.com/image/57b3efdddb5ce94f008b724f-1500/gettyimages-590520338_a.jpg", fname_prefix="trump")
