import os
import evalSrc
from numpy import mean
import json


## compare with answer

def compKey(extracted, answers):
    
    mapres = 0
    probres = 0
    
    totpre = 0
    rel = 0
    tot = 0
    for key in extracted:
        tot += 1
        if key in answers:
            rel += 1
            totpre += rel/tot

    if rel == 0:
        mapres = 0
    elif len(answers) == rel:
        mapres = 1
    else:
        mapres = totpre / rel
    probres = rel/tot

    return [mapres, probres]


## marujo dataset evaluation

def marujoEval():
    root_dir = ".datasets/keyword-extraction/500N-KPCrowd-v1.1"
    keywords = generate_keywords_file(root_dir)
    print(keywords)


def generate_keywords_file(root_dir):
    mapres = []
    probres = []
    zeros = 0
    totals = 0
    data_dir = root_dir + "/docsutf8"
    result_dir = "./results/keyword-extraction/marujo"
    key_dir = root_dir + "/keys"

    try:
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
    except OSError:
        print('Error: Creating directory. ' + result_dir)

    exResults = os.listdir(result_dir)
    filenames = os.listdir(data_dir)

    for file in filenames:
        keywords = []
        fe = 0
        if file in exResults:
            fe = 1
            path = os.path.join(result_dir, file)
            f = open(path, 'r')
            line = f.readline()
            while line:
                keywords.append(line)
                line = f.readline()
            f.close()
        else:
            path = os.path.join(data_dir, file)
            f = open(path, 'r')
            f.readline()
            line = f.readline()
            if line:
                fe = 1
                keywords = evalSrc.extract_keywords(line)
            f.close()
        
        if fe == 1:
            
            ans = []
            path = os.path.join(key_dir, file.split(".")[0] + ".key")
            f = open(path, 'r')
            line = f.readline()
            while line:
                ans.append(line)
                line = f.readline()
            f.close()

            res = compKey(keywords, ans)

            if res[1] == 0:
                zeros += 1
            totals += 1
            
            mapres.append(res[0])
            probres.append(res[1])

    path = os.path.join(result_dir, "result.txt")
    f = open(path, 'w')
    f.write("prob : " + str(mean(probres)) + "\n")
    f.write("map : " + str(mean(mapres)) + "\n")
    f.write("total : " + str(totals) + "\n")
    f.write("zeros : " + str(zeros) + "\n")
    f.close()


    return mapres


## kp20k evaluation
def evaluate_kp20k():

    mapres = []
    probres = []
    zeros = 0
    totals = 0

    root_dir = "./datasets/keyword-extraction/kp20k"
    result_dir = "./results/keyword-extraction/kp20k"

    try:
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
    except OSError:
        print('Error: Creating directory. ' + result_dir)

    path = os.path.join(root_dir, "kp20k_testing.json")

    f = open(path, 'r')

    line = f.readline()
    
    while line:

        if totals > 100:
            break

        tjson = json.loads(line)
        
        text = tjson["title"] + " " + tjson["abstract"]
        keywords = evalSrc.extract_keywords(text)

        ans = tjson["keyword"].split(";")

        res = compKey(keywords, ans)

        if res[1] == 0:
            zeros += 1
        totals += 1

        mapres.append(res[0])
        probres.append(res[1])

        line = f.readline()

    f.close()

    print(mapres)
    print(probres)

    path = os.path.join(result_dir, "result.txt")
    f = open(path, 'w')
    f.write("prob : " + str(mean(probres)) + "\n")
    f.write("map : " + str(mean(mapres)) + "\n")
    f.write("total : " + str(totals) + "\n")
    f.write("zeros : " + str(zeros) + "\n")
    f.close()

    return mapres

if __name__ == "__main__":
    #marujoEval()
    evaluate_kp20k()