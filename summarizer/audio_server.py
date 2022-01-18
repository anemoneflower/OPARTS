from http.server import HTTPServer, BaseHTTPRequestHandler
from pydub import AudioSegment, silence
from pydub.utils import make_chunks

import json

class echoHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    print(self.client_address)
    content_len = int(self.headers.get('Content-Length'))
    post_body = self.rfile.read(content_len).decode('utf-8')
    fields = json.loads(post_body)
    
    user_name = fields["speaker"]
    timestamp = fields["timestamp"]
    requestTimestamp = fields["requestTimestamp"]
    dirpath = "../moderator/webm/"+fields["dir"]+"/"+user_name+"_"+str(timestamp)+".webm"
    
    print("Get audio request from ", user_name, timestamp)
    print("    Interval: ", requestTimestamp)
    
    audiodata = AudioSegment.from_file(dirpath)
    dBFS=audiodata.dBFS
    
    chunk_length_ms = 10000 # pydub calculates in millisec
    chunks = make_chunks(audiodata, chunk_length_ms) #Make chunks of ten sec
    
    print("lenChunks:: ", len(chunks))
    
    silences = silence.detect_silence(chunks[-1], min_silence_len = 1000, silence_thresh=dBFS-16)

    silences = [((start/1000),(stop/1000)) for start,stop in silences] #in sec
    print("===", silences)
    
    silence_cnt = [stop - start for start,stop in silences]
    print("===", silence_cnt)
    
    res = str(timestamp) + "@@"
    # is_silence = True if True in [start > 0.05 and stop - start > 5 for start, stop in silences ] else False
    is_silence = True if True in [stop - start > 4.5 for start, stop in silences ] else False
    if is_silence:
      print("SILENCE DETECTED!!!!!")
      res += "true"
    else:
      res += "false"
      

    self.send_response(200)
    self.send_header('content-type', 'text/html')
    self.end_headers()
    self.wfile.write(res.encode())
      


def main():
    # PORT = int(input("!!! Input PORT to run summaerizer server :"))
    server = HTTPServer(('', 3334), echoHandler)
    print('Server running on port %s' % '3334')
    server.serve_forever()

if __name__ == '__main__':
    main()
