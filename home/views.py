from django.shortcuts import render, redirect
from home import templates
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, auth

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
        firebase.auth().signOut()
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
        penddingSubdocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Pending').get()
        for subdoc in penddingSubdocs:
            list1.append((subdoc.id,doc.id,email))

        inProgressDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'inProgress').get()
        for subdoc in inProgressDocs:
            list2.append((subdoc.id,doc.id,email))

        assessedDocs = db.collection(u'FIR_NCR').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Assessed').get()
        for subdoc in assessedDocs:
            list3.append((subdoc.id,doc.id,email))

    return render(request, "home.html", {"user":request.session['username'], "category":"FIR_NCR", "pending_id_list":list1, "progress_id_list":list2, "assessed_id_list":list3, "fir_active": "active", "assesedNo" : len(list3), "progressNo":len(list2), "newNo":len(list1) })

def details(request, category, user, uid, case_id):

    if not request.session.has_key('username'):
        return redirect(login)
    if request.session['username'] != user:
        return redirect(login)

    metadata = {'category':category, 'user':user, 'uid':uid, 'case_id':case_id}

    if category == "PaidBribe":
        if request.GET.get('delete')=='del':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).delete()
            return redirect(paidBribe, user=user)
        if request.GET.get('accept')=='accpt':
            db.collection(category).document(uid).collection(u'all_data').document(case_id).set({
                u'Status': u'Accepted'
            }, merge=True)
            return redirect(paidBribe, user=user)

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


    if category == "FIR_NCR":
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
                u'Status': u'inProgress'
            }, merge=True)
        return render(request, "details.html", {"user":request.session['username'], "data":data, "metadata":metadata})

    if category == "NOC":
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
    for doc in docs:
        email = db.collection(u'users').document(u'{}'.format(doc.id)).get().to_dict()['email']
        pendingSubdocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Pending').get()
        for subdoc in pendingSubdocs:
            list1.append((subdoc.id,doc.id, email))

        inProcessDocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'In Process').get()
        for subdoc in inProcessDocs:
            list2.append((subdoc.id,doc.id, email))

        acceptedDocs = db.collection(u'PaidBribe').document(u'{}'.format(doc.id)).collection(u'all_data').where(u'Status',u'==',u'Accepted').get()
        for subdoc in acceptedDocs:
            list3.append((subdoc.id,doc.id, email))

    pending_cases = len(list1)
    inprocess_cases = len(list2)
    accepted_cases = len(list3)
    total_cases = (len(list1)+len(list2)+len(list3))

    return render(request, "paidBribe.html", {"user":request.session['username'], "pending_cases":pending_cases, "inprocess_cases":inprocess_cases, "accepted_cases":accepted_cases, "total_cases":total_cases, "category":"PaidBribe", "bribe_active": "active", "pending":list1, "inprocess":list2, "accepted":list3})
    
def unusualBehaviour(request, user):
    return render(request, "unusualBehaviour.html", {"user":request.session['username'], "bribe_active": "active"})

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
    return render(request, "ncr.html", {"user":request.session['username'], "ncr_active": "active"})

def police(request):
    return render(request, "police.html")