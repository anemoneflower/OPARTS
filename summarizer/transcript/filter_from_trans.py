def main():
    inputkeys = ["19bc34cd-feee-4ffa-afdb-1901b1d24f90_길이삭", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_김다연-5", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_노유정-3", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_이기쁨-6", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_최진영-4", "19bc34cd-feee-4ffa-afdb-1901b1d24f90_한동훈-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_박준석-6", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_강호진-3", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_송재엽-2", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_장경석-4", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_정현제-1", "773f2a03-dc39-425a-86bb-39e40bcf9ab9_황정석-5", "4499b593-365b-407d-a143-00533e7bce42_김동훈-6", "4499b593-365b-407d-a143-00533e7bce42_김윤정-3", "4499b593-365b-407d-a143-00533e7bce42_김현정-4", "4499b593-365b-407d-a143-00533e7bce42_염주선 2", "4499b593-365b-407d-a143-00533e7bce42_이주원-5", "4499b593-365b-407d-a143-00533e7bce42_전승민-1"]

    for idx, inputkey in enumerate(inputkeys):
      print(inputkey)

      #### original to filter
      # outputname = "fbox/fbox_filter_transcript_"+inputkey+".txt"
      # with open("fbox/fbox_original_transcript_"+inputkey+".txt", 'r') as ig:
      #   originresult = ig.readlines()

      #### filter upgrade in boost file
      outputname = "fbox/fbox_filter2_boost_transcript_"+inputkey+".txt"
      with open("fbox/fbox_filter_boost_transcript_"+inputkey+".txt", 'r') as ig:
        originresult = ig.readlines()

      pre = ""
      isvalid = False

      for oriidx, oriline in enumerate(originresult):
        if oriline[0] == '(':
          oriparse = oriline.split(', ')[1].split(') ')
          oritag = oriparse[1].strip() # e.g., SPEECH-START
          if oritag == "SPEECH-START":
            pre = oriline
          elif isvalid:
            with open(outputname, 'a') as rf:
              rf.write(oriline)
            isvalid = False
        else:
          if oriline.strip() not in [
              '엄마', '아빠', '오빠',
              '쯧', '습', '이씨', '허허', '아', '어', '응', '아휴', '아우', '아흠', '에', '오', '음', '아 아', '음 음', '흑', '흠', '흠흠', '허허허', '으흠', '하아', '흐흠', '에휴', '이', '허어', '이보게', '아', '어허', '아유', '어허허허허허허허', '허', '흐흐', '흐흐흐', '흐흐흐흐', '흐흐', 
              '아이고', '아이', '이런', 
              '아마 실행되고 있는 브라우저는 다른 책을 치지 마세요.', '아이 데이터가 실행되고 있는 브라우저는 다른 탭을 끼지 마세요.', '아이 메이저가 진행되고 있는 브라우저는 다른 태도에 그치지 마세요.', '아이 데이터가 되고 있는 브라우저를 다른 탭을 주지 마세요.', '아이들이 저희가 진행되고 있는 브라우저는 다른 책을 쓰지 마세요.', '아이 데이터가 실행되고 있는 버가우자는 다른 탭을 짓지 마세요.', '아이들이 저는 책임지고 있는 브라우저는 다른 책을 기지 마세요.']:
            with open(outputname, 'a') as rf:
              if pre:
                rf.write(pre)
                pre = ""
              rf.write(oriline)
              isvalid = True
            

if __name__ == '__main__':
    main()




