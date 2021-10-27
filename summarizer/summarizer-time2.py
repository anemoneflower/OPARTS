from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Text
from urllib.parse import parse_qs
from IPython.display import display

import subprocess
import json
import requests

#import tensorflow as tf; tf.test.is_gpu_available()

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '/device:GPU:0'

import sys

from khaiii.khaiii import KhaiiiExcept
pwd = sys.path[0]
kobert_path = pwd.split("ai-moderator")[0]+"ai-moderator/summarizer/KoBertSum"
kobart_path = pwd.split("ai-moderator")[0]+"ai-moderator/summarizer/KoBART-summarization"
sys.path.append(kobert_path); sys.path.append(kobart_path); 

# Ko-BERT
from src.test_summarize_string import KOBERT_SUMMARIZER
kobert_model = KOBERT_SUMMARIZER()

# Ko-BART
import torch
from kobart import get_kobart_tokenizer
try :
    from transformers.modeling_bart import BartForConditionalGeneration 
except:
    from transformers.models.bart import BartForConditionalGeneration

kobart_model = BartForConditionalGeneration.from_pretrained(kobart_path+'/kobart_summary')#, from_tf=True)
kobart_tokenizer = get_kobart_tokenizer()

def kobert_summarizing_model(input_txt):
    try :
        sent = 3
        encode = kobert_model.encode(input_txt)
        summaries = kobert_model.generate(encode, sent)
        summary = " ".join(summaries)
    except:
        return ""

    return summary

def kobart_summarizing_model(input_txt):
    try :
        text = input_txt.replace('\n', '')
        input_ids = kobart_tokenizer.encode(text)
        input_ids = torch.tensor(input_ids)
        input_ids = input_ids.unsqueeze(0)
        summary = kobart_model.generate(input_ids, eos_token_id=1, max_length=64, num_beams=5, early_stopping=True)
        summary = kobart_tokenizer.decode(summary[0], skip_special_tokens=True)

        if len(summary) > len(input_txt):
            print("INVALID:::", input_txt)
            return ""
    except:
        return ""

    return summary
################# Ko-BERT & Ko-BART ###########################################

################# Pororo ###########################################
from pororo import Pororo
summ_abstractive = Pororo(task="summarization", model="abstractive", lang="ko")
summ_extractive = Pororo(task="summarization", model="extractive", lang="ko")

def pororo_abstractive_model(input_txt):
    try :
        summary = summ_abstractive(input_txt)
        if len(summary) > len(input_txt):
            print("INVALID:::", input_txt)
            return ""
    except:
        return ""
    return summary

def pororo_extractive_model(input_txt):
    try: 
        summary = summ_extractive(input_txt)
    except:
        return ""
    return summary
################# Pororo ###########################################

################# TextRank ###########################################
# python3 -m pip install git+https://github.com/lovit/textrank.git
from konlpy.tag import Komoran
from textrank import KeysentenceSummarizer
import textrank

komoran = Komoran()
def komoran_tokenizer(sent):
    words = komoran.pos(sent, join=True)
    words = [w for w in words if ('/NN' in w or '/XR' in w or '/VA' in w or '/VV' in w)]
    return words

TextRankSummarizer = KeysentenceSummarizer(
    tokenize = komoran_tokenizer,
    min_sim = 0.3,
    verbose = False
)

def textRank_extractive_model(input_txt):
    try:
        keysents = TextRankSummarizer.summarize(input_txt, topk=3)
    except :
         return ""
    return " ".join([i[2] for i in keysents[:3]])

################# TextRank ###########################################

### Keyword extraction ###
from krwordrank.word import summarize_with_keywords
from khaiii import KhaiiiApi

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

def extract_top5_keywords(text):
    if text == "":
        #print("RETURN EMPTY KEYWORD LIST", text)
        return []
    top5_keywords = []
    processed_text = preprocessing(text)
    sentences = processed_text.split('. ')
    try:
        keywords = summarize_with_keywords(sentences, min_count=1, max_length=15)
        for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True)[:5]:
            top5_keywords.append(word)
        #print("KEYWORDS", top5_keywords)
        return top5_keywords
    except ValueError:
        print("ValueError: No keywords were extracted.")
        return []

def combined_keyword_extractor(params):
    text, po_abs, po_ext, ko_abs, ko_ext = params

    res_keywords = []
    keyword_list = {}
    klist = {}
    klist['original_key'] = extract_top5_keywords(text)
    klist['po_abs_key'] = extract_top5_keywords(po_abs)
    klist['po_ext_key'] = extract_top5_keywords(po_ext)
    klist['ko_abs_key'] = extract_top5_keywords(ko_abs)
    klist['ko_ext_key'] = extract_top5_keywords(ko_ext)

    #### Weights (Total: 10) ###
    # abs (PORORO, KoBART): 2.5 / 2.3 / 2.1 / 1.9 / 1.7
    # ext (PORORO, KoBERT): 2   / 1.8 / 1.6 / 1.4 / 1.2
    # original            : 1   / 0.8 / 0.6 / 0.4 / 0.2
    for key in klist:
        if key in ['po_abs_key', 'ko_abs_key']:
            w = 2.5
        elif key in ['po_ext_key', 'ko_ext_key']:
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

# keyword_trends = {}
# def get_trending_keyword(new_keywords):
#     top10_trending = []
#     for key in keyword_trends:
#         keyword_trends[key] *= 0.8
#     i = 5
#     for keyword in new_keywords:
#         if keyword in keyword_trends:
#             keyword_trends[keyword] += i
#         else:
#             keyword_trends[keyword] = i
#         i -= 1
    
#     for word, score in sorted(keyword_trends.items(), key=lambda x:x[1], reverse=True)[:10]:
#         # Set the lower bound for trending keywords
#         if score > 3:
#             top10_trending.append(word)
#     return top10_trending
    
### Keyword extraction ###


################# GET Confidence Sore ###########################################
from rouge import Rouge 
from numpy import inner, mean

## ROUGE
rouge = Rouge()
def get_rouge_score(summary1, summary2):
    # return average of (Rouge-1, 2, L 's F1-score)
    score_keys = ['rouge-1', 'rouge-2', 'rouge-l']
    rouge_score = rouge.get_scores(summary1, summary2)  # get_scores(hypothesis, reference)
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
import seaborn as sns

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
def get_confidence_score_between_two(summary, compare_summary, keywordList):
    if compare_summary == "":
        return keyword_score

    rouge_score = get_rouge_score(summary, compare_summary)
    google_score = get_google_universal_score(summary, compare_summary)

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

        confidence_score = get_confidence_score_between_two(summary, compare_summary, keywordList)
        confidence_scores.append(confidence_score)
    
    if len(confidence_scores) == 0:
        return 1

    return mean(confidence_scores)


################# GET Confidence Sore ###########################################

def select_rep_summary(arr):
    # SELECT Representation summary for each extractive, abstractive summmary
    abs_summary1, abs_summary2, ext_summary1, ext_summary2 = arr

    abs_summary, abs_compare_summary = abs_summary1, abs_summary2
    ext_summary, ext_compare_summary = ext_summary1, ext_summary2

    if abs_summary == "" and abs_compare_summary != "":
        abs_summary, abs_compare_summary  = abs_compare_summary, abs_summary
    if ext_summary == "" and ext_compare_summary != "":
        ext_summary, ext_compare_summary  = ext_compare_summary, ext_summary

    return abs_summary, abs_compare_summary, ext_summary, ext_compare_summary 

import re
def get_summaries(text):
    print("get_summaries for text: "+text)
    # DO NOT SUMMARIZE TEXT when text is short enough / JUST GET ABSTRACTIVE SUMMARY
    text_sentence_num = len(re.split('[.?!]', text)) 

    pororo_ab_res = pororo_abstractive_model(text)
    pororo_ex_res = pororo_extractive_model(text) if text_sentence_num > 3 else text
    kobart_ab_res = kobart_summarizing_model(text)
    kobert_ex_res = kobert_summarizing_model(text) if text_sentence_num > 3 else text

    return pororo_ab_res, pororo_ex_res, kobart_ab_res, kobert_ex_res

sentences_with_keyword = []
def get_overall_summaries(text, keyword):
    print("get_overall_summaries for keyword: " + keyword)

    # Only need extractive summary
    text_sentence_num = len(re.split("[.?!]", text))
    pororo_ab_res, kobart_ab_res = "empty text", "empty text"

    # Generate Extractive summary
    # pororo_ex_res = summ_extractive(text) if text_sentence_num > 3 else text
    # kobert_ex_res = pororo_ex_res

    # if len(re.split('[.?!]', pororo_ex_res)) < 4:
    #     if pororo_ex_res != "":
    #         return pororo_ab_res, pororo_ex_res, kobart_ab_res, kobert_ex_res

    # Generate Extractive summary with new sentences
    sentences = re.split('[.?!]', text)
    sentences_with_keyword = []
    for sentence in sentences:
        if keyword in sentence:
            sentences_with_keyword.append(sentence)
    
    pororo_ex_res = '. '.join(sentences_with_keyword[-3:])
    kobert_ex_res = '. '.join(sentences_with_keyword[-3:])

    return pororo_ab_res, pororo_ex_res, kobart_ab_res, kobert_ex_res        

import time
import json

def main():
    def get_ext_score(hypothesis, fulltext, ext_idxs):
        correct = 0
        for idx in ext_idxs:
            ref_sentence = fulltext[idx].split(".")[0].strip()
            if ref_sentence in hypothesis:
                correct += 1

        return correct / len(ext_idxs)


    times = {'pororo-ab':[], 'pororo-ex':[], 'kobart-ab':[], 'kobert-ex':[], 'textrank':[], 'CF-score':[], 'Keyword':[]}
    ext_scores = {'pororo-ex':[], 'kobert-ex':[], 'textrank': []}
    rouge_scores = {'pororo-ab':[], 'pororo-ex':[], 'kobart-ab':[], 'kobert-ex':[], 'textrank':[]}

    with open("./dataset.json", "r") as f:
        data = json.load(f)

    # SUMMARY
    N = len(list(data.keys()))
    for idx in data.keys():
    #for idx in list(data.keys())[:5]:

        text = " ".join(data[idx]['article_original'])
        fulltext = data[idx]['article_original']
        abs_reference = data[idx]['abstractive'] # e.g. ' ... '
        ext_reference = data[idx]['extractive'] # e.g. [1, 2, 4]

        summaries = [text]; #print(text)

        print("...................")
        start = time.time()
        hypothesis_1 = pororo_abstractive_model(text)
        times['pororo-ab'].append(time.time()-start)
        #print('\n', hypothesis);
        if hypothesis_1 == "":
            print("pororo-ab, NULL STRING RETURN")
        summaries.append(hypothesis_1)
        rouge_score = get_rouge_score(hypothesis_1, abs_reference) if hypothesis_1!="" else 0
        rouge_scores['pororo-ab'].append(rouge_score)

        start = time.time()
        hypothesis_2 = kobart_summarizing_model(text)
        times['kobart-ab'].append(time.time()-start)
        if hypothesis_2 == "":
            print("kobart-ab, NULL STRING RETURN")#; input()
        #print('\n', hypothesis)
        summaries.append(hypothesis_2)
        rouge_score = get_rouge_score(hypothesis_2, abs_reference) if hypothesis_2!="" else 0; rouge_scores['kobart-ab'].append(rouge_score)

        start = time.time()
        hypothesis_3 = pororo_extractive_model(text) 
        times['pororo-ex'].append(time.time()-start)
        if hypothesis_3 == "":
            print("pororo-ex, NULL STRING RETURN")#; input()
        #print('\n', hypothesis); 
        summaries.append(hypothesis_3)
        rouge_score = get_rouge_score(hypothesis_3, abs_reference) if hypothesis_3!="" else 0; rouge_scores['pororo-ex'].append(rouge_score)
        ext_score = get_ext_score(hypothesis_3, fulltext, ext_reference) if hypothesis_3!="" else 0; ext_scores['pororo-ex'].append(ext_score)

        start = time.time()
        hypothesis_4 = kobert_summarizing_model(text)
        times['kobert-ex'].append(time.time()-start)
        if hypothesis_4 == "":
            print("kobert-ex, NULL STRING RETURN")#; input()
        #print('\n', hypothesis); 
        summaries.append(hypothesis_4)
        rouge_score = get_rouge_score(hypothesis_4, abs_reference) if hypothesis_4!="" else 0; rouge_scores['kobert-ex'].append(rouge_score)
        ext_score = get_ext_score(hypothesis_4, fulltext, ext_reference) if hypothesis_4!="" else 0; ext_scores['kobert-ex'].append(ext_score)
        
        start = time.time()
        hypothesis_5 = textRank_extractive_model([text])
        times['textrank'].append(time.time()-start)
        if hypothesis_5 == "":
            print("textrank, NULL STRING RETURN")#; input()   
        #print('\n', hypothesis)
        rouge_score = get_rouge_score(hypothesis_5, abs_reference) if hypothesis_5!="" else 0; rouge_scores['textrank'].append(rouge_score)
        ext_score = get_ext_score(hypothesis_5, fulltext, ext_reference) if hypothesis_5!="" else 0; ext_scores['textrank'].append(ext_score)

        start = time.time()
        keywordList = combined_keyword_extractor(summaries)
        times['Keyword'].append(time.time()-start)

        start = time.time()
        abs_summary, abs_compare_summary, ext_summary, ext_compare_summary = select_rep_summary(summaries[1:])
        ab_confidence_score = get_confidence_score(abs_summary, [abs_compare_summary, ext_summary, ext_compare_summary], keywordList, text)
        times['CF-score'].append(time.time()-start)
        
        if int(idx) % 50 == 0 :
            print("DONE [{}/{}]".format(int(idx), N))
            print(summaries)

    for key in times.keys():
        print(key, np.mean(times[key]))#, [round(i, 3) for i in times[key]])

    # print("\n\n")
    # for key in ext_scores.keys():
    #     print(key, np.mean(ext_scores[key]))

    # print("\n\n")
    # for key in rouge_scores.keys():
    #     print(key, np.mean(rouge_scores[key]))
    

    with open("./time-test-results2/time.json", "w") as f:
        json.dump(times, f, indent=4)
    with open("./time-test-results2/ext-scores.json", "w") as f:
        json.dump(ext_scores, f, indent=4)
    with open("./time-test-results2/rouge-scores.json", "w") as f:
        json.dump(rouge_scores, f, indent=4)

if __name__ == '__main__':
    main()


