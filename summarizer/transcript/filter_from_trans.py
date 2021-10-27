def main():
    inputkeys = ["68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2"]
    # ["68d60d83-5080-4eb0-89f9-2265d3a878f3_강나현-4", "68d60d83-5080-4eb0-89f9-2265d3a878f3_김유승-1", "68d60d83-5080-4eb0-89f9-2265d3a878f3_박유민-3", "68d60d83-5080-4eb0-89f9-2265d3a878f3_장혁진-2", "68d60d83-5080-4eb0-89f9-2265d3a878f3_황지선-5", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_김윤혁-1", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_남홍재-6", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_안태균-2", "9172d42b-e3af-4bcb-9f35-8a10a897ea2a_정화영-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_김재호-3", "a2ece676-bc82-4bd9-8346-c77467d341d3_남궁도-4", "a2ece676-bc82-4bd9-8346-c77467d341d3_배성현-1", "a2ece676-bc82-4bd9-8346-c77467d341d3_윤소정-6", "a2ece676-bc82-4bd9-8346-c77467d341d3_정준희-5", "a2ece676-bc82-4bd9-8346-c77467d341d3_최윤지-2"]

    for idx, inputkey in enumerate(inputkeys):
      print(inputkey)

      #### original to filter
      outputname = "fbox/fbox_filter_transcript_"+inputkey+".txt"
      with open("fbox/fbox_original_transcript_"+inputkey+".txt", 'r') as ig:
        originresult = ig.readlines()

      #### filter upgrade in boost file
      # outputname = "fbox/fbox_filter2_boost_transcript_"+inputkey+".txt"
      # with open("fbox/fbox_filter_boost_transcript_"+inputkey+".txt", 'r') as ig:
      #   originresult = ig.readlines()

      pre = ""
      isvalid = False

      for oriidx, oriline in enumerate(originresult):
        print(oriline)
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




