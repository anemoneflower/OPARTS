import os
import evalSrc
from numpy import mean


def generate_sum_file(dataset):

    score_keys = ['rouge-1', 'rouge-2', 'rouge-l']
    rouge_scores = {}
    for key in score_keys:
        rouge_scores[key] = []

    data_dir = "./datasets/summarization/" + dataset + "/stories"
    result_dir = "./results/summarization/" + dataset

    try:
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
    except OSError:
        print('Error: Creating directory. ' + result_dir)

    exResults = os.listdir(result_dir)
    filenames = os.listdir(data_dir)

    succ = 0
    fail = 0

    cnt = 0

    for file in filenames:
        cnt += 1
        if cnt > 5000:
            break
        sum = ""
        line = None
        al = 0
        cursuc = 0
        if file in exResults:
            path = os.path.join(result_dir, file)
            f = open(path, 'r')
            sum = f.readline()
            succ += 1
            cursuc = 1
            al = 1
            f.close()
        else:
            path = os.path.join(data_dir, file)
            f = open(path, 'r')
            res = ""
            line = f.readline()
            while line:
                if line.find("@highlight") != -1:
                    break
                if line != "\n":
                    res += line.replace("\n", " ")
                line = f.readline()
            if res != "":
                try:
                    sum = evalSrc.get_summary(res)
                except:
                    print(res)
                    path = os.path.join(result_dir, "result_error.txt")
                    t = open(path, 'w')
                    t.write("error occured\n")
                    t.write("success : " + str(succ) + " / fail : " + str(fail) + "\n")
                    for key in score_keys:
                        t.write(key + " : " + str(mean(rouge_scores[key])) + "\n")
                    t.close()

                    print("@@@dataset : ", dataset, " / success : ", succ, " / fail : ", fail)
                    continue
                if sum == None:
                    fail += 1
                    continue
                succ += 1
                cursuc = 1
            else:
                continue
        if al == 1:
            path = os.path.join(data_dir, file)
            f = open(path, 'r')
            line = f.readline()
            while line:
                if line.find("@highlight") != -1:
                    break
                line = f.readline()
        
        if cursuc == 1:
            ans = ""
            while line:
                if line != "\n" and line.find("@highlight") == -1:
                    ans += line.replace("\n", " ")
                line = f.readline()
            f.close()

            rouge = evalSrc.get_rouge(sum, ans)
            
            for key in score_keys:
                rouge_scores[key].append(rouge[key])


    path = os.path.join(result_dir, "result10000.txt")
    f = open(path, 'w')
    f.write("testing10000\n")
    f.write("success : " + str(succ) + " / fail : " + str(fail) + "\n")
    for key in score_keys:
        f.write(key + " : " + str(mean(rouge_scores[key])) + "\n")
    f.close()

    print("@@@dataset : ", dataset, " / success : ", succ, " / fail : ", fail)
    return



if __name__ == "__main__":
    #cnnres = generate_sum_file('cnn')
    dailyres = generate_sum_file('dailymail')