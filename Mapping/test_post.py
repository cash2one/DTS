# -*- coding: UTF-8 -*-
import sys
reload(sys)
import urllib, urllib2, json, csv, md5
sys.setdefaultencoding("utf-8")

def get_md5(strdata):
    m = md5.new()
    m.update(strdata)
    return m.hexdigest()

def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    res = response.read()
    return (json.loads(res), res)

def login():
    print 'login'
    uname="jf"
    passwd="123123"
    apicode="333666"
    #uname="dts_zzy"
    #passwd="dts_zzy"
    #apicode="110038"
    #uname="demo1"
    #passwd="123123"
    #apicode="888888"
    res, raw = post("https://api.100credit.cn/bankServer2/user/login.action", {"userName":uname, "password":passwd, "apiCode":apicode})
    #res, raw = post("https://api.100credit.cn/bankServer/user/login.action", {"userName":uname, "password":passwd, "apiCode":apicode})
    #print >>sys.stderr, raw
    print res
    return res["tokenid"], get_md5(apicode + res["tokenid"])

tid, tmd5 = login()
#print >>sys.stderr, tid, tmd5

fatal_error=set(['1000013', '1000012','1000015'])

def getone(addr="", cell="", tel="", id="", mail="", name="", gid='-1', extraData=""):
    print 'getone'
    global tid, tmd5, fatal_error
    oreq = {"gid":gid, 'tel':tel, "id":id,"mail":[mail],"cell":[cell]}
    cc = len(oreq)
    if not id:
        del oreq['id']
        cc -=1
    if not mail:
        del oreq['mail']
        cc -=1
    if not cell:
        del oreq['cell']
        cc -=1
    if not tel:
        del oreq['tel']
        cc -=1
    if cc == 1 and gid == -1:
        print >>sys.stderr, "no data for query"
        return 0
    data = json.dumps(oreq)
    while True:
        #fig, raw = post("https://api.100credit.cn/bankServer/data/bankData.action", {"tokenid":tid, "interCommand":"1000", "apiCode":"888888", "jsonData":data, "checkCode":get_md5(data+tmd5)})
        fig, raw = post("https://api.100credit.cn/bankServer2/data/bankData.action", {"tokenid":tid, "interCommand":"1000", "apiCode":"333666", "jsonData":data, "checkCode":get_md5(data+tmd5)})
        if fig['code']=='00':
            if extraData:
                print '%s\t%s\t%s'%(extraData, cell, raw)
            else:
                print '%s\t%s\t%s'%(cell, mail, raw)
            return 1
        elif fig['code'] == '100005':
            print >>sys.stderr, "relogin ", raw, tid, tmd5
            tid, tmd5 = login()
        elif fig['code'] == '1000011':
            print >>sys.stderr, "not match for ", data
            return 0
        elif fig['code'] in fatal_error:
            print >>sys.stderr, "critical error ", data, raw
            sys.exit(0)
        else:
            print 'other error', fig['code']
            return 0

if __name__ == '__main__':
    #getone(mail='439620511@qq.com')
    #getone(gid='132236910ff75c7935cc1f2d8789df8')
    getone(cell='+13127631729')
    #getone(mail='402182229@qq.com')
    #for line in sys.stdin:
        #try:
            #print 'aaa'
            #print line[:-1]
            #print >>sys.stderr, "aaaaaii"
            #getone(cell=line[:-1])
        #except:
            #sys.stderr.write("error:"+line)
