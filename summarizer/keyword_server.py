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


### Keyword extraction ###
import RAKE


def extract_top5_keywords(text):
    if text == "":
        print("RETURN EMPTY KEYWORD LIST", text)
        return []
    top5_keywords = []
    try:
        rake_object=RAKE.Rake("SmartStoplist.txt")
        keywords = rake_object.run(text, maxWords = 3)
        for word, r in sorted(keywords, key=lambda x:x[1], reverse=True)[:5]:
            if len(word) > 50:
                print('SKIP Long Keyword: ', word)
                continue
            top5_keywords.append(word)
        print("KEYWORDS", top5_keywords)
        return top5_keywords
    except ValueError:
        print("ValueError: No keywords were extracted.")
        return []

class echoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(self.client_address)
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len).decode('utf-8')
        fields = json.loads(post_body)
        
        print("REQUEST::::::KEYWORD")
        user_name = fields["user"]    # Only for overall summary request
        text = fields["content"]
        infoList = user_name.split("@@@")
        keywords = extract_top5_keywords(text)[:4]

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
    server = HTTPServer(('', PORT), echoHandler)
    print('Server running on port %s' % PORT)
    server.serve_forever()

if __name__ == '__main__':
    main()


