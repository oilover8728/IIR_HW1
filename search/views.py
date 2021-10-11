from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UploadDocumentForm

import os
# /search folder location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import json

import xml.sax

# Count Sentence / words / charater / find
import nltk
from nltk.tokenize import sent_tokenize

file_type = ""
json_data = []
xml_data = []

# 讀取XML檔案並存到xml_data中 xml_data [[article,content],[article,content],.....]
class XMLHandler(xml.sax.ContentHandler):
    global xml_data
    def __init__(self):
        self.xml_data = []
        self.xml_content = ""
        self.CurrentData = ""
        self.ArticleTitle = ""
        self.AbstractText = ""
        self.PublicationStatus = ""

    # 元素開始呼叫
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "Article":
            title = attributes["PubModel"]
    # 元素結束呼叫
    def endElement(self, tag):
        if self.CurrentData == "ArticleTitle":
            self.xml_data.append('<span style="font-size:30px; color:rgb(0, 183, 255);">'+self.ArticleTitle+'</span>')
            # print("Title:", self.ArticleTitle)
        elif self.CurrentData == "AbstractText":
            self.xml_content = self.xml_content + " " + self.AbstractText
        elif self.CurrentData == "PublicationStatus":
            self.xml_data.append(self.xml_content)
            xml_data.append(self.xml_data)
            self.xml_data = []
            self.xml_content=""

    # 讀取字元時呼叫
    def characters(self, content):
        if self.CurrentData == "ArticleTitle":
            self.ArticleTitle = content
        elif self.CurrentData == "AbstractText":
            self.AbstractText = content
        elif self.CurrentData == "PublicationStatus":
            self.PublicationStatus = content

# 判斷要拿的資料是xml還是json，不清空session內的值，希望保留先前的結果
def home(request):
    form = UploadDocumentForm()
    if('json_output' in request.session):
        json_output = request.session['json_output']

    if('xml_output' in request.session):
        xml_output = request.session['xml_output']

    if('sentences_count' in request.session):
        sentences_count = request.session['sentences_count']

    if('words_count' in request.session):
        words_count = request.session['words_count']

    if('chars_count' in request.session):
        chars_count = request.session['chars_count']

    if('find_count' in request.session):
        find_count = request.session['find_count']

    return render(request, 'html/home.html', locals())

# 處理上傳檔案，且xml/json要用不同的暫存器儲存
def upload_file(request):
    global file_type
    global json_data
    global xml_data

    form = UploadDocumentForm()

    if request.method == 'POST':
        form = UploadDocumentForm(request.POST, request.FILES)  # Do not forget to add: request.FILES
        if form.is_valid():
            filename = str(request.FILES['file'])
            # ===== IF NOT XML OR JSON =====
            if filename.endswith('.xml')!= True and filename.endswith('.json')!=True:
                error = ("error with filename")
                return render(request, 'html/home.html', locals())

            # 列出指定路徑底下所有檔案(包含資料夾)
            yourPath = BASE_DIR+'/search/media'
            # allFileList = os.listdir(yourPath)
            # for file in allFileList:
            #     print(file)

            # Save file to media folder
            handle_uploaded_file(request.FILES['file'])

            # del the old and initial file count
            if('json_output' in request.session):
                del request.session['json_output']
            if('xml_output' in request.session):
                del request.session['xml_output']
            if('sentences_count' in request.session):
                del request.session['sentences_count']
            if('words_count' in request.session):
                del request.session['words_count']
            if('chars_count' in request.session):
                del request.session['chars_count']
            words_count=0
            chars_count=0
            sentences_count=0

            # Make the output become [each page[each detail]] type
            if filename.endswith('.json'):
                file_type = "json"
                json_output = []
                with open(yourPath+'/'+filename,encoding="utf-8") as f:
                    json_data = json.load(f)

                for post in json_data:
                    user_data=[]
                    user_data.append('<span style="font-size:30px; color:rgb(0, 183, 255);">'+ post['username'] +'</span>')
                    username = post['username']

                    user_data.append(post['tweet_text'])
                    content = post['tweet_text']

                    json_output.append(user_data)

                    # Count detail
                    sentences_count += len(sent_tokenize(content))
                    chars_count += len(username)
                    words_count += len(post['username'].split())
                    chars_count += len(content)
                    words_count += len(post['tweet_text'].split())
                    
                request.session['json_output']=json_output
                request.session['sentences_count']=sentences_count
                request.session['words_count']=words_count
                request.session['chars_count']=chars_count
            
            elif filename.endswith('.xml'):
                file_type = "xml"
                xml_data=[]

                # 建立一個 XMLReader
                parser = xml.sax.make_parser()
                # 關閉名稱空間
                parser.setFeature(xml.sax.handler.feature_namespaces, 0)
                # 重寫 ContextHandler
                Handler = XMLHandler()
                parser.setContentHandler(Handler)
                parser.parse(yourPath+'/'+filename)

                request.session['xml_output']=xml_data

                # Count detail
                for article in xml_data:
                    title=article[0]
                    content=article[1]
                    sentences_count += len(sent_tokenize(content))
                    chars_count += len(title)
                    words_count += len(title.split())
                    chars_count += len(content)
                    words_count += len(content.split())

                request.session['sentences_count']=sentences_count
                request.session['words_count']=words_count
                request.session['chars_count']=chars_count

    return redirect('/search/home#sec')

# 儲存上傳的檔案到media資料夾
def handle_uploaded_file(f):
    save_path = os.path.join(BASE_DIR,'search','media',f.name)
    with open(save_path, 'wb+') as fp:
        for chunk in f.chunks():
            fp.write(chunk)

# 判斷是xml/json並處理資料，找到相對應的token用replace<span>的方法mark
def search(request):
    global file_type
    global json_data
    global xml_data
    if 'search_token' in request.POST:
        find_count=0
        target = request.POST['search_token']
        if file_type=="json":
            json_output = []
            for line in json_data:
                user_data=[]
                user_data.append('<span style="font-size:30px; color:rgb(0, 183, 255);">'+line['username'].replace(target,'<span style="background:yellow; color:black;">'+target+'</span>')+'</span>')
                user_data.append(line['tweet_text'].replace(target,'<span style="background:yellow; color:black;">'+target+'</span>'))
                json_output.append(user_data)
                # find Count
                find_count += line['username'].count(target)
                find_count += line['tweet_text'].count(target)
            request.session['find_count']=find_count
            request.session['json_output']=json_output
        elif file_type == "xml":
            xml_output_temp=[]
            for article in xml_data:
                xml_data_temp=[]
                xml_data_temp.append('<span style="font-size:30px; color:rgb(0, 183, 255);">'+article[0].replace(target,'<span style="background:yellow; color:black;">'+target+'</span>')+'</span>')
                xml_data_temp.append(article[1].replace(target,'<span style="background:yellow; color:black;">'+target+'</span>'))
                xml_output_temp.append(xml_data_temp)
                # find Count
                find_count += article[0].count(target)
                find_count += article[1].count(target)
            request.session['find_count']=find_count
            request.session['xml_output']=xml_output_temp

    return redirect('/search/home#sec')

# 將檔案全部清空，並跳到輸入欄位
def clear(request):
    global file_type
    global json_data
    global xml_data
    file_type=""
    json_data=[]
    xml_data=[]
    if('json_output' in request.session):
        del request.session['json_output']
    if('xml_output' in request.session):
        del request.session['xml_output']
    if('sentences_count' in request.session):
        del request.session['sentences_count']
    if('words_count' in request.session):
        del request.session['words_count']
    if('chars_count' in request.session):
        del request.session['chars_count']
    if('find_count' in request.session):
        del request.session['find_count']
    return redirect('/search/home#sec')
