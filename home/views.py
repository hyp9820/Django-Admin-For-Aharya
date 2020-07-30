from django.shortcuts import render, redirect
from home import templates
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, auth, threading
from django.core.mail import send_mail
import cv2
import os
import face_recognition
import urllib.request as req
import time
import datetime

config={
    'apiKey': "AIzaSyDMD127uosKN8bfmhCD_jwz_q09En2T_0g",
    'authDomain': "bribe-block.firebaseapp.com",
    'databaseURL': "https://bribe-block.firebaseio.com",
    'projectId': "bribe-block",
    'storageBucket': "bribe-block.appspot.com",
    'messagingSenderId': "883197621162",
    'appId': "1:883197621162:web:e1cb0f7c7735f6e84eb1d3",
    'measurementId': "G-GXPSH1W25J"
}

firebase = pyrebase.initialize_app(config)
authpy = firebase.auth()

cred = credentials.Certificate("home\\assets\\bribe-block-firebase-adminsdk-d9igq-1b0de61f8c.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
def login(request):

    if request.session.has_key('username'):
        return  redirect(paidBribe, user=request.session['username'])
        

    if request.method == 'POST':
        email = request.POST.get('email')
        passw = request.POST.get('pass')
        try:
            _ = authpy.sign_in_with_email_and_password(email,passw)
            user = auth.get_user_by_email(email)
            request.session['username'] = user.email          
            return redirect(paidBribe, user=user.email)
        except:
            message ="You have entered invalid credentials"
            return render(request,"login.html",{"message":message})
    else:
        return render(request, "login.html")

def register(request):

    if request.session.has_key('username'):
        return  redirect(paidBribe, user=request.session['username'])

    if request.method == 'POST':
        first = request.POST.get('first')
        mid = request.POST.get('mid')
        last = request.POST.get('last')
        nm = first+" "+mid+" "+last
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        passw = request.POST.get('password')
        conf_passw = request.POST.get('password_confirm')
        addr1 = request.POST.get('address1')
        addr2 = request.POST.get('address2')
        pin = request.POST.get('pincode')
        city = request.POST.get('city')
        state = request.POST.get('state')
        idtype = request.POST.get('id-type')

        if passw == conf_passw:
            auth.create_user(display_name=nm, email=email, password=passw, phone_number="+91"+phone)
            db = firestore.client()
            db.collection(u'admins').document(email).set({
                'name':nm,
                'email':email,
                'phone_no':phone,
                'gender':gender,
                'address-line-1': addr1,
                'address-line-2': addr2,
                'pincode': pin,
                'city': city,
                'state': state,
                'id-type': idtype
            })
    return render(request, "register.html")
  
def logout(request):
    if request.session.has_key('username'):
        # firebase.auth().signOut()
        request.session.flush()
    else:
        pass
    return redirect(login)

def home(request, user):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)
    
    docs = db.collection(u'FIR_NCR').stream()
    list1 = []
    list2 = []
    list3 = []
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        penddingSubdocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'FIR').where(u'Status',u'==',u'Pending').get()
        for subdoc in penddingSubdocs:
            list1.append((subdoc.id,doc.id,email))

        inProgressDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'FIR').where(u'Status',u'==',u'inProgress').get()
        for subdoc in inProgressDocs:
            list2.append((subdoc.id,doc.id,email))

        assessedDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'FIR').where(u'Status',u'==',u'Assessed').get()
        for subdoc in assessedDocs:
            list3.append((subdoc.id,doc.id,email))

    return render(request, "home.html", {"user":request.session['username'], "category":"FIR", "pending_id_list":list1, "progress_id_list":list2, "assessed_id_list":list3, "fir_active": "active", "assesedNo" : len(list3), "progressNo":len(list2), "newNo":len(list1) })

def details(request, category, user, uid, case_id):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)

    metadata = {'category':category, 'user':user, 'uid':uid, 'case_id':case_id}

    # Bride Report
    if category == "PaidBribe":
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).delete()
            return redirect(paidBribe, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'Accepted'
            }, merge=True)
            # Sent Email
            print("Sending Email")
            send_mail('Report Accepted - {}'.format(case_id),
            'Dear {},\nThis is to inform you that your bribe report with CaseID: {} has been accepted and necessary actions will be taken regarding it.\nThank you for the information.'.format(user, case_id),
            'aharyaindia@gmail.com', ['{}'.format(request.GET.get('email'))], fail_silently = False)
            return redirect(paidBribe, user=user)
        if request.GET.get('evid')=='evidence':
            face_recog()

        print("***************",category,"**************")
        doc_ref = db.collection(category).document(uid).collection(u'all_data').document(case_id)
        doc = doc_ref.get()
        case_data = doc.to_dict()
        data = {}
        for i in sorted(case_data):
            data[i] = case_data[i]
        # print(data)
        if data['Status'] == 'Pending':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'In Process'
            }, merge=True)
        return render(request, "bribeDetails.html", {"user":request.session['username'], "data":data, "metadata":metadata})

    # FIR
    if category == "FIR":
        category = "FIR_NCR"
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'FIR').document(case_id).delete()
            return redirect(home, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'FIR').document(case_id).set({
                u'Status': u'Assessed'
            }, merge=True)
            return redirect(home, user=user)
        if request.GET.get('evid')=='evidence':
            face_recog()

        print("***************",category,"**************")
        doc_ref = db.collection(category).document(uid).collection(u'FIR').document(case_id)
        doc = doc_ref.get()
        case_data = doc.to_dict()
        data = {}
        for i in sorted(case_data):
            data[i] = case_data[i]
        # print(data)
        if data['Status'] == 'Pending':
            db.collection(category).document(uid).collection(u'FIR').document(case_id).set({
                u'Status': u'inProgress'
            }, merge=True)
        return render(request, "details.html", {"user":request.session['username'], "data":data, "metadata":metadata})

    # NCR
    if category == "NCR":
        category = "FIR_NCR"
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'NCR').document(case_id).delete()
            return redirect(home, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'NCR').document(case_id).set({
                u'Status': u'Assessed'
            }, merge=True)
            return redirect(home, user=user)

        print("***************",category,"**************")
        doc_ref = db.collection(category).document(uid).collection(u'NCR').document(case_id)
        doc = doc_ref.get()
        case_data = doc.to_dict()
        data = {}
        for i in sorted(case_data):
            data[i] = case_data[i]
        # print(data)
        if data['Status'] == 'Pending':
            db.collection(category).document(uid).collection(u'NCR').document(case_id).set({
                u'Status': u'inProgress'
            }, merge=True)
        return render(request, "details.html", {"user":request.session['username'], "data":data, "metadata":metadata})

    # NOC
    if category == "NOC":
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).delete()
            return redirect(noc, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'Accepted'
            }, merge=True)
            return redirect(noc, user=user)
        print("***************",category,"**************")
        doc_ref = db.collection(category).document(uid).collection(u'all_data').document(case_id)
        doc = doc_ref.get()
        case_data = doc.to_dict()
        data = {}
        for i in sorted(case_data):
            data[i] = case_data[i]
        # print(data)
        if data['Status'] == 'Pending':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'In Process'
            }, merge=True)
        return render(request, "nocDetails.html", {"user":request.session['username'], "data":data, "metadata":metadata})

    # Unusual Behaviour
    if category == "UnusualBehaviour":
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).delete()
            return redirect(unusualBehaviour, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'Accepted'
            }, merge=True)
            return redirect(unusualBehaviour, user=user)

        print("***************",category,"**************")
        doc_ref = db.collection(category).document(uid).collection(u'all_data').document(case_id)
        doc = doc_ref.get()
        case_data = doc.to_dict()
        data = {}
        for i in sorted(case_data):
            data[i] = case_data[i]
        # print(data)
        if data['Status'] == 'Pending':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'In Process'
            }, merge=True)
        return render(request, "ubDetails.html", {"user":request.session['username'], "data":data, "metadata":metadata})
    
def paidBribe(request, user):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)

    docs = db.collection(u'PaidBribe').stream()
    list1 = []
    list2 = []
    list3 = []
    total_cases = 0
    pending_cases = 0
    states = []
    dates = []
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        pendingSubdocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Pending').get()
        for subdoc in pendingSubdocs:
            states.append(db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['state'])
            date = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['date']
            date = date.split('-')
            # adjusting date acc to js Datetime (0-11 for Month)
            date[1] = str(int(date[1]) - 1)
            date = "-".join(date)
            dates.append(date)
            list1.append((subdoc.id,doc.id, email))

        inProcessDocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'In Process').get()
        for subdoc in inProcessDocs:
            list2.append((subdoc.id,doc.id, email))
            states.append(db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['state'])
            date = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['date']
            date = date.split('-')
            # adjusting date acc to js Datetime (0-11 for Month)
            date[1] = str(int(date[1]) - 1)
            date = "-".join(date)
            dates.append(date)

        acceptedDocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Accepted').get()
        for subdoc in acceptedDocs:
            list3.append((subdoc.id,doc.id, email))
            states.append(db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['state'])
            date = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').document(subdoc.id).get().to_dict()['date']
            date = date.split('-')
            # adjusting date acc to js Datetime (0-11 for Month)
            date[1] = str(int(date[1]) - 1)
            date = "-".join(date)
            dates.append(date)

    # creating dates dict with date : no of cases
    for i in range(len(dates)):
        # converting to DateTime for sorting
        dates[i] = datetime.datetime.strptime(dates[i], '%Y-%m-%d').date()
    dates.sort()
    datesDic = {}
    i = 0
    for date in dates:
        i += 1
        datesDic[date] = i
    for key in datesDic.keys():
        print(key, datesDic[key])

    pending_cases = len(list1)
    inprocess_cases = len(list2)
    accepted_cases = len(list3)
    total_cases = (len(list1)+len(list2)+len(list3))
    return render(request, "paidBribe.html", {"user":request.session['username'], "pending_cases":pending_cases, "inprocess_cases":inprocess_cases, "accepted_cases":accepted_cases, "total_cases":total_cases, "category":"PaidBribe", "bribe_active": "active", "pending":list1, "inprocess":list2, "accepted":list3, "states": states, "dates":datesDic })
    
def hotReport(request, user):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)

    docs = db.collection(u'Hot Report').stream()
    lst = []
    for doc in docs:

        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        # print(email)
        reports = db.collection(u'Hot Report').document(u'{}'.format(doc.id)).collection(u'all_data').get()
        for report in reports:
            lst.append((report.id,doc.id, email, report.to_dict()))
            print(report.to_dict())

    return render(request, "hotReport.html",  {"user":request.session['username'], "category":"hot", "hot_active": "active", "data":lst})
    
def unusualBehaviour(request, user):
    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)

    docs = db.collection(u'UnusualBehaviour').stream()
    list1 = []
    list2 = []
    list3 = []
    total_cases = 0
    pending_cases = 0
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        pendingSubdocs = db.collection(u'UnusualBehaviour').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Pending').get()
        for subdoc in pendingSubdocs:
            list1.append((subdoc.id,doc.id, email))

        inProcessDocs = db.collection(u'UnusualBehaviour').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'In Process').get()
        for subdoc in inProcessDocs:
            list2.append((subdoc.id,doc.id, email))

        acceptedDocs = db.collection(u'UnusualBehaviour').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Accepted').get()
        for subdoc in acceptedDocs:
            list3.append((subdoc.id,doc.id, email))

    pending_cases = len(list1)
    inprocess_cases = len(list2)
    accepted_cases = len(list3)
    total_cases = (len(list1)+len(list2)+len(list3))

    return render(request, "unusualBehaviour.html", {"user":request.session['username'], "pending_cases":pending_cases, "inprocess_cases":inprocess_cases, "accepted_cases":accepted_cases, "total_cases":total_cases, "category":"UnusualBehaviour", "bribe_active": "active", "pending":list1, "inprocess":list2, "accepted":list3})

def noc(request, user):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)
    
    docs = db.collection(u'NOC').stream()
    list1 = []
    list2 = []
    list3 = []
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        pendingSubdocs = db.collection(u'NOC').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Pending').get()
        for subdoc in pendingSubdocs:
            list1.append((subdoc.id,doc.id, email))

        inProcessDocs = db.collection(u'NOC').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'In Process').get()
        for subdoc in inProcessDocs:
            list2.append((subdoc.id,doc.id, email))

        acceptedDocs = db.collection(u'NOC').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Accepted').get()
        for subdoc in acceptedDocs:
            list3.append((subdoc.id,doc.id, email))


    return render(request, "noc.html", {"user":request.session['username'], "noc_active": "active", "category":"NOC", "pending":list1, "inprocess":list2, "accepted":list3})

def ncr(request, user):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)
    
    docs = db.collection(u'FIR_NCR').stream()
    list1 = []
    list2 = []
    list3 = []
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        penddingSubdocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'NCR').where(u'Status',u'==',u'Pending').get()
        for subdoc in penddingSubdocs:
            list1.append((subdoc.id,doc.id,email))

        inProgressDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'NCR').where(u'Status',u'==',u'inProgress').get()
        for subdoc in inProgressDocs:
            list2.append((subdoc.id,doc.id,email))

        assessedDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'NCR').where(u'Status',u'==',u'Assessed').get()
        for subdoc in assessedDocs:
            list3.append((subdoc.id,doc.id,email))

    return render(request, "ncr.html", {"user":request.session['username'], "category":"NCR", "pending_id_list":list1, "progress_id_list":list2, "assessed_id_list":list3, "ncr_active": "active", "assesedNo" : len(list3), "progressNo":len(list2), "newNo":len(list1) })

def police(request):
    return render(request, "police.html")

def faceevidence(request, doc_id, rep_id):
    report = db.collection(u'Hot Report').document(u'{}'.format(doc_id)).collection(u'all_data').document(u'{}'.format(rep_id)).get().to_dict()['Url']
    l=[report]
    face_recog(l)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UNKNOWN_FACES_DIR = str(BASE_DIR)+'\\home\\evidence'
    for filename in os.listdir(UNKNOWN_FACES_DIR):
        print('deleted')
        os.remove(f'{UNKNOWN_FACES_DIR}\\{filename}')

    return redirect(hotReport,user=request.session['username'])


def face_recog(url=['http://ipfs.io/ipfs/QmcgBRywQf63rZdD27M9aVnSn1puwjchvqepAUE7zcKqCD']):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KNOWN_FACES_DIR = str(BASE_DIR)+'\\home\\known_faces'
    FOUND_FACES_DIR = str(BASE_DIR)+'\\home\\found_faces'
    print(KNOWN_FACES_DIR)
    UNKNOWN_FACES_DIR = str(BASE_DIR)+'\\home\\evidence'
    TOLERANCE = 0.6
    FRAME_THICKNESS = 3
    FONT_THICKNESS = 2
    MODEL = 'hog'
    if(len(url)>0):
        for i in range(len(url)):
            type_of_file=req.urlopen(url[i]).info()['content-type']
            if(type_of_file=="video/mp4"):
                req.urlretrieve(url[i],f'{UNKNOWN_FACES_DIR}\\sample{i}.mp4')
            elif(type_of_file == "image/jpg"):
                req.urlretrieve(url[i],f'{UNKNOWN_FACES_DIR}\\sample{i}.jpg')
            elif(type_of_file == "image/jpeg"):
                req.urlretrieve(url[i],f'{UNKNOWN_FACES_DIR}\\sample{i}.jpeg')
            elif(type_of_file == "image/png"):
                req.urlretrieve(url[i],f'{UNKNOWN_FACES_DIR}\\sample{i}.png')
            print(url)
            url=[]
    else:
        req.urlretrieve('http://ipfs.io/ipfs/QmcgBRywQf63rZdD27M9aVnSn1puwjchvqepAUE7zcKqCD',f'{UNKNOWN_FACES_DIR}\\sample2.mp4')
    # video = cv2.VideoCapture(str(BASE_DIR)+"\home\evidence\modi.mp4")  # put the video file name instead
    print("loading known faces")

    known_faces = []
    known_names = []

    for name in os.listdir(f"{KNOWN_FACES_DIR}"):
        for filename in os.listdir(f"{KNOWN_FACES_DIR}/{name}"):
            print(filename)
            image = face_recognition.load_image_file(f"{KNOWN_FACES_DIR}/{name}/{filename}")
            encodings = face_recognition.face_encodings(image)
            if(len(encodings)>0):
                encoding=encodings[0]
                known_faces.append(encoding)
                known_names.append(name)
    next_id = int(time.time())
    print("processing unknown faces")
    for filename in os.listdir(UNKNOWN_FACES_DIR):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            print(filename)
            image = face_recognition.load_image_file(f"{UNKNOWN_FACES_DIR}/{filename}")
            locations = face_recognition.face_locations(image, model=MODEL)
            encodings = face_recognition.face_encodings(image, locations)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            for face_encoding, face_location in zip(encodings, locations):
                results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
                match = None
                if True in results:
                    match = known_names[results.index(True)]
                    print(f"Match found: {match}")
                else:
                    match = str(next_id)
                    next_id =int(time.time())
                    known_names.append(match)
                    known_faces.append(face_encoding)
                    os.mkdir(f"{KNOWN_FACES_DIR}/{match}")
                    os.mkdir(f"{FOUND_FACES_DIR}/{match}")
                    cv2.imwrite(f"{FOUND_FACES_DIR}/{match}/{match}.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    cv2.imwrite(f"{KNOWN_FACES_DIR}/{match}/{match}.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 50])
                top_left = (face_location[3], face_location[0])
                bottom_right = (face_location[1], face_location[2])
                color = [0, 255, 0]
                cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)

                top_left = (face_location[3], face_location[2])
                bottom_right = (face_location[1], face_location[2] + 22)
                cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)
                cv2.putText(image, f"{match}", (face_location[3] + 5, face_location[2] + 15), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                            (200, 200, 200), FONT_THICKNESS)
                cv2.imshow(filename, image)
                cv2.waitKey(0)
                cv2.destroyWindow(filename)
                print("file deleted")
                # os.remove(f'{UNKNOWN_FACES_DIR}\\{filename}')
        else:
            video = cv2.VideoCapture(f"{UNKNOWN_FACES_DIR}/{filename}")
            print(filename)
            while True:
                ret, img = video.read()
                if(ret==False):
                    break
                image = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
                cv2.imshow("", image)
                locations = face_recognition.face_locations(image, model=MODEL)
                encodings = face_recognition.face_encodings(image, locations)
                for face_encoding, face_location in zip(encodings, locations):
                    results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
                    match = None
                    if True in results:
                        match = known_names[results.index(True)]
                        print(f"Match found: {match}")
                    else:
                        match = str(next_id)
                        next_id += 1
                        known_names.append(match)
                        known_faces.append(face_encoding)
                        os.mkdir(f"{KNOWN_FACES_DIR}/{match}")
                        os.mkdir(f"{FOUND_FACES_DIR}/{match}")
                        cv2.imwrite(f"{FOUND_FACES_DIR}/{match}/{match}.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 50])
                        cv2.imwrite(f"{KNOWN_FACES_DIR}/{match}/{match}.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    top_left = (face_location[3], face_location[0])
                    bottom_right = (face_location[1], face_location[2])
                    color = [0, 255, 0]
                    cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)

                    top_left = (face_location[3], face_location[2])
                    bottom_right = (face_location[1], face_location[2] + 22)
                    cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)
                    cv2.putText(image, f"{match}", (face_location[3] + 5, face_location[2] + 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (200, 200, 200), FONT_THICKNESS)

                cv2.imshow("", image)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("file deleted")
                    # os.remove(f'{UNKNOWN_FACES_DIR}\\{filename}')
                    break
            cv2.destroyWindow("")
        # os.close(f'{UNKNOWN_FACES_DIR}\\{filename}')
        # os.remove(f'{UNKNOWN_FACES_DIR}\\{filename}')
