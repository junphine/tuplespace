#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib,urllib2
from tspace import *;
import json
import time

def translate(text,lin='en',lout='zh-CN',encoding='utf-8'):
    if type(text)==type(u''):
        text=text.encode('utf-8','ignore')
    
    values={'hl':'zh-CN','ie':'UTF-8','text':text,'langpair':"%s|%s" % (lin, lout)}

    url='http://translate.google.cn/translate_t'
    print values
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

def test():  
    #text=raw_input('input>>')
    text='start translate'
    output=translate(text)
    printf(output)
       
import random

def not_english(word):
    for i in range(0,len(word)):
        ch=word[i]
        if ord(ch)>127 or ord(ch)<0:  #含中文         
            return True
    return False

def main():
    tb=TSpace(T_SPACE_SRV_ADDR)
    print '中文'
    tb.store('message',[0,'key','关键词'])
    while True:
        try:
            record=tb.take('message',['','','','']);
            if record:
                #tb.store('translate',[rand,'关键',''])
                printf(('new translate:',record))
                r=record
                if not not_english(r[1]): #英语翻译
                    r[1]=translate(r[1])
                    printf(r[1])                
                    tb.store('message.reply',r)
                    
                elif r[1]: #中文翻译                    
                    r[1]=translate(r[1],'zh-CN','en')
                    printf(r[1])
                    tb.store('message.reply',r)
            #print 'wait'
        except urllib2.HTTPError,e:
            print e


if __name__ == "__main__":    
    test()
    main()
    print 'finish'
    



