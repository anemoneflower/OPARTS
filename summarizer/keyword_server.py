from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Text
from urllib.parse import parse_qs
from IPython.display import display

import subprocess
import json
import requests

import sys
for line in sys.stdin:
    PORT = int(line)
print("PORT: ", PORT)

from khaiii.khaiii import KhaiiiExcept

### Keyword extraction ###
from krwordrank.word import summarize_with_keywords
import os
from khaiii import KhaiiiApi
import re, math


khaiiiWord = KhaiiiApi()

def preprocessing(text):
    sentences = text.replace("\n", " ").replace('?', '.').replace('!', '.').split('.')
    sentences = [x.strip() for x in sentences]
    sentences = list(filter(None, sentences))
    processed_text = ''
    try:
        for sentence in sentences:
            word_analysis = khaiiiWord.analyze(sentence)
            temp = []
            for word in word_analysis:
                for morph in word.morphs:
                    if morph.tag in ['NNP', 'NNG', 'SL', 'ZN'] and len(morph.lex) > 1:
                        temp.append(morph.lex)
            temp = ' '.join(temp)
            temp += '. '
            processed_text += temp
        return processed_text
    except KhaiiiExcept:
        print("형태소 분석에 실패했습니다.")
        return ""

def krwordrank_keywords(text):
    if text == "":
        print("RETURN EMPTY KEYWORD LIST", text)
        return []
    top5_keywords = []
    processed_text = preprocessing(text)
    sentences = processed_text.split('. ')
    try:
        keywords = summarize_with_keywords(sentences, min_count=1, max_length=15)
        for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:5]:
            top5_keywords.append(word)
        print("KEYWORDS", top5_keywords)
        return top5_keywords
    except ValueError:
        print("ValueError: No keywords were extracted.")
        return []

TF = {}
DF = {}
DOCS_NUM = 0
def line2nouns(line):
    korean = " ".join(re.compile('[ㄱ-ㅣ가-힣]+').findall(line))
    if korean.strip() == "":
        return [] 

    word_analysis = khaiiiWord.analyze(korean)
    temp = []
    for word in word_analysis:
        for morph in word.morphs:
            if morph.tag in ['NNP', 'NNG', 'SL', 'ZN'] and len(morph.lex) > 1:
                temp.append(morph.lex)
    return temp

def tfidf_keywords(line):
    global DF, DOCS_NUM
    word = line2nouns(line)
    wordset = list(set(word))

    tfs = []; dfs = []
    for w in wordset:
        tfs.append(word.count(w))
        if w not in DF:
            DF[w] = 1
        else:
            DF[w] += 1
        dfs.append(DF[w])
        DOCS_NUM += 1

    tfidfs = []
    for tf, df, word in zip(tfs, dfs, wordset):
        v = math.log(DOCS_NUM/(1+df)) * tf
        tfidfs.append((v, word))

    tfidfs.sort(key = lambda x : (x[0], DF[x[1]]), reverse=True)
    return [x[1] for x in tfidfs[:4]]

def ready_for_tfidf():
    global TF, DF, DOCS_NUM

    with open("./document.txt", "r") as f:
        lines = f.readlines()

    for line in lines:
        word = set(line2nouns(line))
        DOCS_NUM += 1
        for w in word:
            if w not in DF:
                DF[w] = 0
            DF[w] += 1

class echoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(self.client_address)
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len).decode('utf-8')
        fields = json.loads(post_body)
        
        print("REQUEST::::::KEYWORD")
        # user_name = fields["user"]    # Only for overall summary request
        text = fields["content"]
        # infoList = user_name.split("@@@")
        keywords = krwordrank_keywords(text)[:4]
        keywords_tfidf = tfidf_keywords(text)

        # Concatenate summaries, keywords, trending keywords
        keywordString = '@@@@@CD@@@@@AX@@@@@'.join(keywords)
        res = keywordString

        # Print results
        for keyword in keywords:
            print("#%s " % keyword, end="")
        print()

        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(res.encode())
        

def main():
    # PORT = int(input("!!! Input PORT to run summaerizer server :"))
    ready_for_tfidf()

    server = HTTPServer(('', PORT), echoHandler)
    print('Server running on port %s' % PORT)
    server.serve_forever()

if __name__ == '__main__':
    main()


