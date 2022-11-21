from http.server import HTTPServer, BaseHTTPRequestHandler
from pydub import AudioSegment
from pydub.utils import make_chunks

import json

import sys
for line in sys.stdin:
    PORT = int(line)
print("PORT: ", PORT)

class echoHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    print(self.client_address)
    content_len = int(self.headers.get('Content-Length'))
    post_body = self.rfile.read(content_len).decode('utf-8')
    fields = json.loads(post_body)
    
    user_name = fields["speaker"]
    requestTimestamp = fields["requestTimestamp"]
    dirpath = "../moderator/webm/"+fields["dir"]+"/"+user_name+".wav"
    
    print("Get audio request from ", user_name)
    print("    Interval: ", requestTimestamp)
    
    audiodata = AudioSegment.from_wav(dirpath)
    
    chunk_length_ms = 1000 # pydub calculates in millisec
    chunks = make_chunks(audiodata, chunk_length_ms) #Make chunks of ten sec
    
    print("lenChunks:: ", len(chunks))
    
    res = str(requestTimestamp) + "@@" + str(len(chunks))

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
