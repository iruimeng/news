#-*- coding:utf-8 -*-

import pymongo
import mysql.connector
import json
from datetime import datetime
from utils import parseDateStr, ImageProcessor
import sys

'''
create table articles (
  id int not NULL  auto_increment PRIMARY  key,
  task_id VARCHAR(32) not null,
  site_label varchar(50) not null default '',
  author varchar(50) not null default '',
  title VARCHAR(100) not null default '',
  article text,
  url VARCHAR(200) not null default '',
  comment_count int not null default 0,
  hot int not null default 0,
  UNIQUE KEY (task_id)
);

create table article_images (
  id int not null auto_increment PRIMARY  KEY ,
  article_id int not null default 0,
  seq SMALLINT not null default 0,
  image_path varchar(100) not null default '',
  type VARCHAR (10),
  create_time datetime,
  update_time datetime,
  UNIQUE  KEY (article_id, type)
);
'''

IMAGE_SIZES = {
    "large": (360,150),
    "middle": (328, 185),
    "small": (113, 80)
}

IMAGE_SAVE_DIR = "/Users/jiangqiurong/Desktop"

def saveToMysql(mysqlConn, data):
    get_sql = "select id from articles where task_id=%{task_id}s"
    article_id = None
    try:
        cursor = mysqlConn.cursor(dictionary=True)
        row = cursor.fetchone()
        if row:
            article_id = row["id"]
        cursor.close()
    except Exception, e:
        print "try to get article info by task: %s, error: %s" %(data["task_id"], str(e))

    sql = "insert into articles (task_id, site_label, author, title, article, url, comment_count, hot, publish_time, create_time, update_time) values(%(task_id)s, %(site_label)s, %(author)s, %(title)s, %(article)s, %(url)s, %(comment_count)s, %(hot)s, %(publish_time)s, %(create_time)s, %(update_time)s ) on duplicate key update task_id=values(task_id), site_label=values(site_label), author=values(author), title=values(title), article=values(article), url=values(url), comment_count=values(comment_count), hot=values(hot), publish_time=values(publish_time), update_time=values(update_time)"
    try:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["create_time"] = data["update_time"] = time_str
        cursor = mysqlConn.cursor()
        cursor.execute(sql, data)
        if cursor.lastrowid > 0:
            article_id = cursor.lastrowid
        cursor.close()
        mysqlConn.commit()
    except Exception, e:
        print "insert task:%s error:%s" % (data["task_id"], str(e))
    return article_id

def readCrawledArticles(mongoClient, mysqlConn):
    result_db = mongoClient.resultdb

    for collection_name in  result_db.collection_names():
        if collection_name == "test":
            continue
        img_processor = ImageProcessor(IMAGE_SAVE_DIR, collection_name, IMAGE_SIZES)
        print "process %s" % collection_name
        for doc in result_db[collection_name].find():
            result = json.loads(doc["result"])
            content_imgs = result.get("content_imgs", [])
            title = result["title"]
            dt = parseDateStr(result.get("date", ""))
            data = {
                "site_label":collection_name,
                "task_id": doc["taskid"],
                "url": doc["url"],
                "title": title,
                "author": result["author"],
                "article": json.dumps(result["article"]),
                "comment_count": 0 if result.get("comment_count", "") == "" else result["comment_count"],
                "hot": result.get("hot", 0),
                "publish_time": dt.strftime("%Y-%m-%d %H:%M:%S") if dt != None else None
            }
            article_id = saveToMysql(mysqlConn, data)
            print article_id
            if len(content_imgs) > 0 and article_id != None:
                saveArticleImages(mysqlConn, content_imgs, img_processor, article_id, doc["taskid"])

def saveArticleImages(mysqlConn, img_urls, img_processor, article_id, task_id):
    sql = "insert into article_images (article_id, seq, image_path, `type`, create_time, update_time) values (%(article_id)s, %(seq)s, %(image_path)s, %(type)s, %(create_time)s, %(update_time)s) on duplicate key update image_path=values(image_path), update_time=values(update_time)"

    for i in xrange(len(img_urls)):
        seq = i+1
        ret = img_processor.save(img_urls[i], "%s-%d" % (task_id, seq))
        for key, val in ret.iteritems():
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = {"article_id":article_id, "image_path":val, "type":key, "create_time":time_str, "update_time":time_str, "seq":seq}
            try:
                cursor = mysqlConn.cursor()
                cursor.execute(sql, data)
                cursor.close()
                mysqlConn.commit()
            except Exception, e:
                print "save image info %s, error:%s" % (json.dumps(data), str(e))



if __name__ == "__main__":
    mongoClient = pymongo.MongoClient("mongodb://47.88.194.127:27017/", connect=False)
    mysqlConn = mysql.connector.connect(user="root", password="root2my", host="47.88.194.127", database="news", charset="utf8")

    if mongoClient == None:
        print "connect to mongodb error"
        sys.exit(1)
    if mysqlConn == None:
        print "connect to mysql error"
        sys.exit(1)
    readCrawledArticles(mongoClient, mysqlConn)

    mysqlConn.close()
    mongoClient.close()

