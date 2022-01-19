
### Keyword extraction ###
import RAKE
from summarizer import Summarizer
bert_model = Summarizer()

# from transformers import pipeline
# bart_summarizer = pipeline("summarization")
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


def get_summaries(text):
    #print("    * get_summaries for text: "+text)
    bert_res = bert_summarizing_model(text, 0, 0.2)
    bart_res = bart_summarizing_model(text, 200)
    return bert_res, bart_res


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
        #print("KEYWORDS", top5_keywords)
        return top5_keywords
    except ValueError:
        print("ValueError: No keywords were extracted.")
        return []

def combined_keyword_extractor(text, bart, bert, prior):
    res_keywords = []
    keyword_list = {}
    klist = {}
    klist['original_key'] = extract_top5_keywords(text)
    klist['bart_key'] = extract_top5_keywords(bart)
    klist['bert_key'] = extract_top5_keywords(bert)

    #### Weights (Total: 5) ###
    # prior     : 3   / 2.8 / 2.6 / 2.4 / 2.2
    # abs (bart): 2   / 1.8 / 1.6 / 1.4 / 1.2
    # ext (bert): 2   / 1.8 / 1.6 / 1.4 / 1.2
    # original  : 1   / 0.8 / 0.6 / 0.4 / 0.2
    for key in klist:
        if key in ['bart_key', 'bert_key']:
            w = 2
        else:
            w = 1
        if key == prior:
            w += 1
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

def get_rouge(sum, ans):
    score_keys = ['rouge-1', 'rouge-2', 'rouge-l']
    rouge_score = rouge.get_scores(sum, ans)[0]
    res={}
    for key in score_keys:
        res[key] = rouge_score[key]['f']
    return res

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
    
    #print("    * rouge_score", rouge_score, "/ google_score", google_score)

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


def get_summary(text):

    bert_res, bart_res = get_summaries(text)

    ab_confidence_score = get_confidence_score_between_two(text, bart_res)
    ex_confidence_score = get_confidence_score_between_two(text, bert_res)

    if ab_confidence_score < 0.5 and ex_confidence_score < 0.5:
        return None

    return bart_res if ab_confidence_score > ex_confidence_score else bert_res


### Keyword extraction ###

def extract_keywords(text):
    
    bert_res, bart_res = get_summaries(text)

    ab_confidence_score = get_confidence_score_between_two(text, bart_res)
    ex_confidence_score = get_confidence_score_between_two(text, bert_res)
    
    keywordList = combined_keyword_extractor(text, bart_res, bert_res, 'bart_key' if ab_confidence_score > ex_confidence_score else 'bert_key')

    #print("Final Results")
    return keywordList

if __name__ == '__main__':
    text = """
        We have to think about what we can get by going to college. so number one, you will learn things not only that can get you a job but things that will help you out in life. if you have a finance degree you'll learn about investing in taxes that'll help you out no matter what. right? Everybody needs to know finance and then beyond that, connections with people. My college, it depends on what college you go to, I just went to a state school nothing fancy. But we still had connections with entrepreneurs, businessmen, and people in our neighborhoods. And like I learned a lot from people like that also professors, I learned a ton from my professors not in class but just in talking to them in conversation about life. So I think there's a ton of value you can get from just being in that environment.
    """
    text="""
        Georges Dambier, whose work is the subject of a delightful exhibition at the Bonni Benrubi Gallery on East 57th Street (through May 14), liked to use Paris as the backdrop for his fashion photographs. Or Cannes or Marrakesh. This was the postwar world of jazz clubs, existentialists, cheap travel, uncrowded streets, beautiful cars, artists and, of course, Paris couture. With his Rolleiflex, Mr. Dambier, who will be 86 on Tuesday, captured all of this with honest joie de vivre, publishing his fashion images in French Elle. And he worked with some of the era's great beauties: Suzy Parker, Dorian Leigh, Bettina, Marie-Hélène Arnaud, Capucine, Ivy Nicholson and a young Brigitte Bardot. I admit: his name was new to me. But when I saw some images online, I was attracted to his sense of color and the carefree quality of his fashion work, which nicely mingled sophistication with girl-next-door sex appeal. ""He shot for Elle in the ""50s,"" said Rachel Smith, the director of the Benrubi gallery. ""He's never really broken past that French sphere. I don't think he got the credit he deserves."" Richard Avedon and Irving Penn, among others, dominate that era. Yet it's interesting that Mr. Dambier, like Avedon, was photographing in the streets, using Paris cafes and other scenes, and in a way that feels more natural and familiar than his American counterpart, who photographed for Harper's Bazaar and helped bring more action to fashion images. One of my favorites, from a 2008 monograph of Mr. Dambier's black and white images, shows the model Sophie Litvak at close range as she pays a taxi driver, her face framed by the raised collar of her coat and the opened flap of her handbag. This is the second exhibition of Mr. Dambier's work at Bonni Benrubi, which first heard about him 10 years ago through a colleague in London. Mr. Dambier lives in Provence, where he has run a bed-and-breakfast for many years. About nine months ago, Ms. Smith said, he mentioned that he also had color images. ""He said, ""I think I could get these negatives restored,"" "" Ms. Smith recalled with a light laugh. ""When we saw the scans, we were bowled over by the color."" In the last decade, digital retouching has made everything look oversharp and perfect - and, as Ms. Smith said of the Dambier images, ""they're not perfect and that's why they're amazing. They have that sense of color that doesn't exist anymore."" She added: ""He's just a complete find. He pulls these images out, like the girl in the polka-dot bathing suit, and you think, ""Where have you been hiding this?"" "" In addition to treating high fashion as a popular art, by photographing it in the street, Mr. Dambier's pictures of fresh-faced models at the beach (including one posed with a surfboard), seem to summon the ""60s.
    """
    print(extract_keywords(text))