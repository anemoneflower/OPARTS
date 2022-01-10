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

################ BERT & BART ###########################################
# INITIALIZE [BERT&BART] 
from summarizer import Summarizer
bert_model = Summarizer()

INSTALL_MSG = """
Bart will be released through pip in v 3.0.0, until then use it by installing from source:

git clone git@github.com:huggingface/transformers.git
git checkout d6de6423
cd transformers
pip install -e ".[dev]"

"""
import torch
try:
    import transformers
    from transformers import BartTokenizer, BartForConditionalGeneration
except ImportError:
    raise ImportError(INSTALL_MSG)
torch_device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(torch_device)

tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')
model = model.to(torch_device)

def bart_summarizing_model(input_txt, max_len):
    article_input_ids = tokenizer.batch_encode_plus([input_txt], return_tensors='pt', max_length=1024)['input_ids'].to(torch_device)
    summary_ids = model.generate(article_input_ids,
                                num_beams=4,
                                length_penalty=2.0,
                                max_length=max_len,
                                min_length=56,
                                no_repeat_ngram_size=3)

    summary_text = tokenizer.decode(summary_ids.squeeze(), skip_special_tokens=True)
    return summary_text

# BERT
def bert_summarizing_model(input_txt, sent, ratio):
    if sent != 0:
        sum = bert_model(input_txt, num_sentences = sent)
    elif ratio != 0:
        sum = bert_model(input_txt, ratio = ratio)

    full = ''.join(sum)
    return full
################ BERT & BART ###########################################


# ################# Ko-BERT & Ko-BART ###########################################
# # INITIALIZE [Ko-BERT & Ko-BART] 
# import sys

# from khaiii.khaiii import KhaiiiExcept
# pwd = sys.path[0]
# kobert_path = pwd.split("ai-moderator")[0]+"ai-moderator/summarizer/KoBertSum"
# kobart_path = pwd.split("ai-moderator")[0]+"ai-moderator/summarizer/KoBART-summarization"
# sys.path.append(kobert_path); sys.path.append(kobart_path); 

# # Ko-BERT
# from src.test_summarize_string import KOBERT_SUMMARIZER
# kobert_model = KOBERT_SUMMARIZER()

# # Ko-BART
# import torch
# from kobart import get_kobart_tokenizer
# # from transformers.modeling_bart import BartForConditionalGeneration 
# from transformers.models.bart import BartForConditionalGeneration
# kobart_model = BartForConditionalGeneration.from_pretrained(kobart_path+'/kobart_summary')#, from_tf=True)
# kobart_tokenizer = get_kobart_tokenizer()

# def kobert_summarizing_model(input_txt):
#     try :
#         sent = 3
#         encode = kobert_model.encode(input_txt)
#         summaries = kobert_model.generate(encode, sent)
#         summary = " ".join(summaries)
#     except:
#         return ""

#     return summary

# def kobart_summarizing_model(input_txt):
#     try :
#         text = input_txt.replace('\n', '')
#         input_ids = kobart_tokenizer.encode(text)
#         input_ids = torch.tensor(input_ids)
#         input_ids = input_ids.unsqueeze(0)
#         summary = kobart_model.generate(input_ids, eos_token_id=1, max_length=64, num_beams=5, early_stopping=True)
#         summary = kobart_tokenizer.decode(summary[0], skip_special_tokens=True)

#         if len(summary) > len(input_txt)*0.9:
#             print("INVALID kobart:::", input_txt)
#             return ""
#     except:
#         return ""

#     return summary
# ################# Ko-BERT & Ko-BART ###########################################

# ################# Pororo ###########################################
# from pororo import Pororo
# summ_abstractive = Pororo(task="summarization", model="abstractive", lang="ko")
# summ_extractive = Pororo(task="summarization", model="extractive", lang="ko")

# def pororo_abstractive_model(input_txt):
#     try :
#         summary = summ_abstractive(input_txt)
#         if len(summary) > len(input_txt)*0.9:
#             print("INVALID proro_ab:::", input_txt)
#             return ""
#     except:
#         return ""
#     return summary

# def pororo_extractive_model(input_txt):
#     try: 
#         summary = summ_extractive(input_txt)
#     except:
#         return ""
#     return summary
# ################# Pororo ###########################################

### Keyword extraction ###
import RAKE

def extract_top5_keywords(text):
    if text == "":
        print("    * RETURN EMPTY KEYWORD LIST", text)
        return []
    top5_keywords = []
    try:
        rake_object=RAKE.Rake("SmartStoplist.txt")
        keywords = rake_object.run(text, maxWords = 3)
        for word, r in sorted(keywords, key=lambda x:x[1], reverse=True)[:5]:
            if len(word) > 50:
                print("    * SKIP Long Keyword: ", word)
                continue
            top5_keywords.append(word)
        print("    * KEYWORDS", top5_keywords)
        return top5_keywords
    except ValueError:
        print("    * ValueError: No keywords were extracted.")
        return []

def combined_keyword_extractor(text, abstractive, extractive):
    res_keywords = []
    keyword_list = {}
    klist = {}
    klist['original_key'] = extract_top5_keywords(text)
    klist['abs_key'] = extract_top5_keywords(abstractive)
    klist['ext_key'] = extract_top5_keywords(extractive)

    #### Weights (Total: 10) ###
    # abs (bert): 2.5 / 2.3 / 2.1 / 1.9 / 1.7
    # ext (bart): 2   / 1.8 / 1.6 / 1.4 / 1.2
    # original  : 1   / 0.8 / 0.6 / 0.4 / 0.2
    for key in klist:
        if key in ['abs_key']:
            w = 2.5
        elif key in ['ext_key']:
            w = 2
        else:
            w = 1
        for keyword in klist[key]:
            if keyword in keyword_list:
                keyword_list[keyword] += w
            else:
                keyword_list[keyword] = w
            w -= 0.2
    
    # Extract Top 5 keywords with large weights
    for keyword, w in sorted(keyword_list.items(), key=lambda x: x[1], reverse=True)[:5]:
        res_keywords.append(keyword)
    return res_keywords
### Keyword extraction ###


################# GET Confidence Sore ###########################################
from rouge import Rouge 
from numpy import inner, mean

## ROUGE
rouge = Rouge()
def get_rouge_score(summary1, summary2):
    # return average of (Rouge-1, 2, L 's F1-score)
    score_keys = ['rouge-1', 'rouge-2', 'rouge-l']
    rouge_score = rouge.get_scores(summary1, summary2)
    F1_rouge = [[score[key]['f'] for key in score_keys] for score in rouge_score]
    return mean(F1_rouge)

## GOOGLE ENCODER
# import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from absl import logging

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
config_tf = tf.ConfigProto()
config_tf.gpu_options.allow_growth = True

import sentencepiece as spm
import matplotlib.pyplot as plt
import pandas as pd
import re

hub_module = hub.Module("https://tfhub.dev/google/universal-sentence-encoder-lite/2")
input_placeholder = tf.sparse_placeholder(tf.int64, shape=[None, None])
encodings = hub_module(
    inputs=dict(
        values=input_placeholder.values,
        indices=input_placeholder.indices,
        dense_shape=input_placeholder.dense_shape))

with tf.Session(config=config_tf) as sess:
    spm_path = sess.run(hub_module(signature="spm_path"))

sp = spm.SentencePieceProcessor()
with tf.io.gfile.GFile(spm_path, mode="rb") as f:
    sp.LoadFromSerializedProto(f.read())

def process_to_IDs_in_sparse_format(sp, sentences):
    ids = [sp.EncodeAsIds(x) for x in sentences]
    max_len = max(len(x) for x in ids)
    dense_shape=(len(ids), max_len)
    values=[item for sublist in ids for item in sublist]
    indices=[[row,col] for row in range(len(ids)) for col in range(len(ids[row]))]
    return (values, indices, dense_shape)

def get_google_universal_score(summary1, summary2):
    messages = [summary1, summary2]
    with tf.Session(config=config_tf) as session:
        session.run(tf.global_variables_initializer())
        session.run(tf.tables_initializer())
        values, indices, dense_shape = process_to_IDs_in_sparse_format(sp,messages)

        message_embeddings = session.run(
            encodings,
            feed_dict={input_placeholder.values: values,
                        input_placeholder.indices: indices,
                        input_placeholder.dense_shape: dense_shape})
        # corr = np.inner(message_embeddings, message_embeddings)
        corr = inner(message_embeddings, message_embeddings)
    return corr[0][1]

## SCORE BY KEYWORD EXTRACTION
def get_keyword_score(summary, keywordList):
    if len(keywordList) == 0:
        return False, 0
    
    return True, len(list(filter(lambda x : x in summary, keywordList))) / len(keywordList) 


################# CONFIDENCE SCORE
def get_confidence_score_between_two(summary, compare_summary):
    rouge_score = get_rouge_score(summary, compare_summary)
    google_score = get_google_universal_score(summary, compare_summary)
    
    print("    * rouge_score", rouge_score, "/ google_score", google_score)

    score_list = [rouge_score, google_score]
    return mean(score_list)

def get_confidence_score(summary, compare_summarylist, keywordList, text):
    if summary == "":
        return 0
        
    if summary == text:
        return 1

    score_type_num_add, keyword_score = get_keyword_score(summary, keywordList)
    confidence_scores = [keyword_score] if score_type_num_add else []

    for compare_summary in compare_summarylist:
        if compare_summary == "":
            continue

        confidence_score = get_confidence_score_between_two(summary, compare_summary)
        confidence_scores.append(confidence_score)
    
    if len(confidence_scores) == 0:
        return 1

    return mean(confidence_scores)


################# GET Confidence Sore ###########################################

def select_rep_summary(abs_summary1, abs_summary2, ext_summary1, ext_summary2):
    # SELECT Representation summary for each extractive, abstractive summmary

    abs_summary, abs_compare_summary = abs_summary1, abs_summary2
    ext_summary, ext_compare_summary = ext_summary1, ext_summary2

    if abs_summary == "" and abs_compare_summary != "":
        abs_summary, abs_compare_summary  = abs_compare_summary, abs_summary
    if ext_summary == "" and ext_compare_summary != "":
        ext_summary, ext_compare_summary  = ext_compare_summary, ext_summary

    return abs_summary, abs_compare_summary, ext_summary, ext_compare_summary 

import re
def get_summaries(text):
    print("    * get_summaries for text: "+text)
    bert_res = bert_summarizing_model(text, 0, 0.2)
    bart_res = bart_summarizing_model(text, 200)
    return bert_res, bart_res

sentences_with_keyword = []
def get_overall_summaries(text, keyword):
    print("    * get_overall_summaries for keyword: " + keyword)

    # Only need extractive summary
    text_sentence_num = len(re.split("[.?!]", text))
    print("    * text_sentence_num, text: ", text_sentence_num, text)
    bert_res = "empty text"

    try:
        bert_res = bert_summarizing_model(text, 5, 0) if text_sentence_num > 3 else text
    except:
        sentences = re.split('[.?!]', text)
        sentences_with_keyword = []
        for sentence in sentences:
            if keyword in sentence:
                sentences_with_keyword.append(sentence)
        bert_res = '. '.join(sentences_with_keyword[-3:])

    return bert_res

class echoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(self.client_address)
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len).decode('utf-8')
        fields = json.loads(post_body)
        
        print("REQUEST::::::SUMMARY")
        user_name = fields["user"]    # Only for overall summary request
        text = fields["content"]
        infoList = user_name.split("@@@")

        # Check if request for an overall summary (fields["user"] == "OVERALL" + keyword)
        if (infoList[0] == "OVERALL"):
            ext_summary = get_overall_summaries(text, infoList[1])
            print("ext_summary: ", ext_summary)
            abs_summary = " "
            keywordList = [" "]
            keywordString = '@@@@@CD@@@@@AX@@@@@'.join(keywordList)
            
            res = '@@@@@AB@@@@@EX@@@@@'.join([abs_summary, ext_summary, keywordString])
            res += "@@@@@CF@@@@@0"
            
        else:
            bert_res, bart_res = get_summaries(text)
            print("    * bert_res:   ", bert_res, len(bert_res))
            print("    * bart_res:   ", bart_res, len(bart_res))
            
            if len(text) < len(bert_res):
                bert_res = text
            if len(text) < len(bart_res):
                bart_res = text       

            # Extract combined keywords
            keywordList = combined_keyword_extractor(text, bart_res, bert_res)
            # Extract Top 10 trending keywords
            # top10_trending = get_trending_keyword(keywordList)

            # Calculate confidence score
            abs_summary = bart_res
            ext_summary = bert_res
            
            ab_confidence_score = get_confidence_score_between_two(text, abs_summary)
            ex_confidence_score = get_confidence_score_between_two(text, ext_summary)
            print("    * ab_confidence_score: ", ab_confidence_score)
            print("    * ex_confidence_score: ", ex_confidence_score)
            
            abs_summary = text if ab_confidence_score == 1 else abs_summary
            ext_summary = text if ex_confidence_score == 1 else ext_summary
            print("    * abs_summary: ", abs_summary)
            print("    * ext_summary: ", ext_summary)
            

            # Concatenate summaries, keywords, trending keywords
            keywordString = '@@@@@CD@@@@@AX@@@@@'.join(keywordList[:4])
            # trendingString = '@@@@@CD@@@@@AX@@@@@'.join(top10_trending)
            # res = '@@@@@AB@@@@@EX@@@@@'.join([abs_summary, ext_summary, keywordString, trendingString])
            res = '@@@@@AB@@@@@EX@@@@@'.join([abs_summary, ext_summary, keywordString])
            res += "@@@@@CF@@@@@" + (', ').join([str(ab_confidence_score), str(ex_confidence_score)])

            # Print results
            print("    * CONFIDENCE_SCORE", ab_confidence_score)
            print("    * Abstractive:::\n%s" % abs_summary)
            print("    * Extractive:::\n%s" % ext_summary)
            print("    * Keywords:::")
            for keyword in keywordList:
                print("    * #%s " % keyword, end="")
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

