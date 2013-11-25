#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib,urllib2
from tspace import *;
import json



def translate(text,lin='en',lout='zh-CN',encoding='utf-8'):
    if type(text)==type(u''):
        text=text.encode('utf-8')
    
    values={'hl':'zh-CN','ie':'UTF-8','text':text,'langpair':"%s|%s" % (lin, lout)}

    url='http://translate.google.cn/translate_t'

    data = urllib.urlencode(values)   

    req = urllib2.Request(url, data)

    req.add_header('User-Agent', "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)")

    response = urllib2.urlopen(req)

    content=response.read()

    begin=content.find('<span id=result_box ')
    if begin>0:
        end_pos=content.find('</span>',begin)
        text=content[begin:end_pos]
        begin=text.rfind('">')
        text=text[begin+2:]
        if type(text)==type(u''):
            text=text.encode(encoding)
        elif encoding!='utf-8':
            text=unicode(text,'utf-8').encode(encoding,'ignore');
        
    return text


def translate_fast(text,lin='en',lout='zh-CN'):    
    
    values={'client':'t','otf':'2','pc':0,'ie':'UTF-8','text':text,'sl':lin,'tl':lout}

    url='http://translate.google.com/translate_a/t'

    data = urllib.urlencode(values)    
    print data
    req = urllib2.Request(url, data)

    req.add_header('User-Agent', "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)")

    response = urllib2.urlopen(req)

    content=response.read()
    #content=unicode(content,'utf-8').encode('gbk');
    content=json.loads(content)
    print content
    
    data=eval(content)
    data=data['sentences']    
    text=data[0]['trans']   
    #text=unicode(text,'utf-8').encode('gbk');       
    return text

def test():  
    #text=raw_input('input>>')
    text='start translate'
    output=translate(text)
    printf( output )
       
import time

def main():
    tb=TSpace(T_SPACE_SRV_ADDR)    
    tb.store('translate',[0,'key','关键词'])
    while True:
        try:            
            r=tb.take('translate',[0,'$en','$zh']);
            print 'new translate:',r
            if r[1]: #英语翻译
                text=translate(r[1])
                printf(text)                
                tb.store('translate',[1,r[1],text])
                
            elif r[2]: #中文翻译
                
                text=translate(r[2],'zh-CN','en')
                printf(text)     
                tb.store('translate',[1,text,r[2]])
            print 'wait'
        except urllib2.HTTPError,e:
            print e


if __name__ == "__main__":    
    test()
    main()
    print 'finish'
    



