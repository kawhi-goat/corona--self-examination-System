import os, base64, json, serial, cv2, numpy as np
from flask import Flask, render_template, request, redirect, jsonify, make_response, url_for
from collections import OrderedDict
from datetime import date

# 서버 위치 내 폴더로 디렉토리 지정하기 (os.chdir(""))

app = Flask(__name__)

def detect_text(path):
    # Detects text in the file
    from google.cloud import vision
    import io

    credential_path = "C:/Users/김성재/Desktop/nodejs/Arduino/JSON/APIKEY.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    file = open('test.txt', 'w', encoding="utf-8")

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text

    file.write(text)
    file.close()

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    # OCR처리한 txt파일 List화
    L = []
    file = open('test.txt', 'r', encoding="utf-8")
    while (1):
        line = file.readline()
        try:
            escape = line.index('\n')
        except:
            escape = len(line)

        if line:
            L.append(line[0:escape])
        else:
            break

    file.close()
    # 개인 정보 찾기
    file_data = OrderedDict()

    def hasNumbers(inputString):
        return any(char.isdigit() for char in inputString)

    def by_size(words, size):
        return [word for word in words if len(word) == size]

    def month_return(arg):
        months = {
            "JAN" : "01",
            "FEB" : "02",
            "MAR" : "03",
            "APR" : "04",
            "MAY" : "05",
            "JUN" : "06",
            "JUL" : "07",
            "AUG" : "08",
            "SEP" : "09",
            "OCT" : "10",
            "NOV" : "11",
            "DEC" : "12",
        }
        return months.get(arg, "00")

    try:# 이름
        matching = [s for s in L if ("한글" or "성명") in s]
        nameIndex = L.index(matching[0])
        while hasNumbers(L[nameIndex+1]):
           nameIndex = nameIndex + 1
        file_data["name"] = L[nameIndex+1]
    except:
        file_data["name"] = "error"

    try:# 성별
        matching = [s for s in L if ("Sex" or "성별") in s]
        sexIndex = L.index(matching[0])
        if L[sexIndex+1] == 'F':
            file_data["sex"] = "F"
        elif L[sexIndex+1] == 'M':
            file_data["sex"] = "M"
        else:
            file_data["sex"] = "error"
    except:
        file_data["sex"] = "error"
        
    try:# 여권번호
        matching = [s for s in L if s.startswith(
            ('M', 'S', 'R', 'G', 'D'))]
        num = by_size(matching, 9)
        file_data["num"] = num[0]
    except:        
        file_data["num"] = "error"

    try:# 생년월일
        matching = [s for s in L if 
                    ("JAN" or "FEB" or "MAR" or "APR" or "MAY" or "JUN" or 
                     "JUL" or "AUG" or "SEP" or "OCT" or "NOV" or "DEC") in s]
        date = by_size(matching, 11)
        splited = date[0].split(' ')
        final_date = [splited[2] ,month_return(splited[1]), splited[0]]
        file_data["date"] = '.'.join(final_date)
    except:
        file_data["date"] = "error"
    # json파일에 작성
    with open('userdata.json', 'w', encoding="utf-8") as make_file:
        json.dump(file_data, make_file, ensure_ascii=False, indent="\t")

def img_encode(string):
    content = string.split(';')[1]
    image_encoded = content.split(',')[1]
    body = base64.decodebytes(image_encoded.encode('utf-8'))

    nparr = np.frombuffer(body, np.uint8)
    print(nparr)

    img = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    cv2.imwrite('img.png', img)

    # cv2.imshow("frame", img) # opencv 이미지 출력 *테스트용*
    # cv2.waitKey(0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/2')
def detect():
    return render_template('face.html')

@app.route('/3')
def temp():
    return render_template('tempCheck.html') # 체온 검출 페이지

@app.route('/4')
def check(): # 문진 페이지
    return render_template('askCheck.html')

@app.route('/5')
def result():
    with open('userdata.json', encoding='utf-8') as json_file:
       json_data = json.load(json_file)
       json_name = json_data["name"]
       json_sex = json_data["sex"]
       json_num = json_data["num"]
       json_date = json_data["date"]
    # 체온 값
    with open('tempdata.json', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        json_temp = json_data["temp"]
    # 결과 (위험군 설정) float(json_temp), age값 비교 분석 결과 String타입으로 반환,
    with open('askdata.json', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        json_symp = json_data["symptom"]

    def calculate_age(born):
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    year, month, day = [int(f) for f in json_date.split('.')]
    bornday = date(year, month, day)
    json_age = calculate_age(bornday)

    # json파일로 저장

    file_data = OrderedDict()
    file_data["name"] = json_name
    file_data["sex"] = json_sex
    file_data["num"] = json_num
    file_data["age"] = json_age
    file_data["temp"] = json_temp
    file_data["symp"] = json_symp

    if(os.path.exists('examdata.json')):
        with open('examdata.json', 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
        data.update(file_data)

        with open('examdata.json', 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False, indent="\t")
    else:
        with open('examdata.json', 'w', encoding="utf-8") as make_file:
            json.dump(file_data, make_file, ensure_ascii=False, indent="\t")

    symp = ''
    temp_result = ''

    if(float(json_temp) >= 37.5):
        temp_result = "현재 발열"
    else:
        temp_result = "현재 정상"

    if(json_age >= 50 and json_age < 60):
        json_symp = json_symp*1.1
    elif(json_age >= 60 and json_age < 70):
        json_symp = json_symp*1.2
    elif(json_age >= 70):
        json_symp = json_symp*1.3

    if(int(json_symp) < 1):
        symp = '건강'
    elif((int(json_symp) >= 1) and (int(json_symp) < 4)):
        symp = '관심'
    elif((int(json_symp) >= 4) and (int(json_symp) < 7)):
        symp = '주의'
    else:
        symp = '심각'

    return render_template('result.html', name=json_name,
                           sex=json_sex, num=json_num, age=json_age, temp=temp_result, st=symp)
    # 통과

@app.route('/receiver', methods=['POST'])
def idcheck():
   data = request.get_json()
   result = ''
   result = str(data['url'])
   
   img_encode(result)
   detect_text('img.png')
   with open('userdata.json', encoding='utf-8') as json_file:
       json_data = json.load(json_file)
       json_name = json_data["name"]
       json_sex = json_data["sex"]
       json_num = json_data["num"]
       json_date = json_data["date"]
   return jsonify({"name":json_name,"sex":json_sex,"num":json_num,"date":json_date})

@app.route('/arduino_receiver', methods=['POST'])
def temp_check():
    ard = serial.Serial(
        port = 'COM3',
        baudrate = 9600
    )
    listen = ard.readline()
    temp = listen.decode()[:len(listen) - 1]
    temp = temp[:len(temp)-1]
    file_data = OrderedDict()
    file_data["temp"] = temp

    with open('tempdata.json', 'w', encoding="utf-8") as make_file:
        json.dump(file_data, make_file, ensure_ascii=False, indent="\t")
    
    return jsonify({"temp" : temp})

@app.route('/ask_receiver', methods=['POST'])
def ask_check():
    data = request.get_json()
    country = ''
    symptom = ''

    country = str(data['country'])
    symptom = str(data['symptom'])

    file_data = OrderedDict()
    file_data["country"] = country
    file_data["symptom"] = symptom

    with open('askdata.json', 'w', encoding="utf-8") as make_file:
        json.dump(file_data, make_file, ensure_ascii=False, indent="\t")

    return country

if __name__ == "__main__":
    # app.run(host='172.30.1.47', port=5000)
    app.run(host="localhost", debug=True)
