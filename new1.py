from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy, Model
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid,os
import jwt 
from datetime import datetime as dt ,timedelta 


app = Flask(__name__)
ENV = 'dev'

app.config['SECRET_KEY'] = 'thisissecret'
base_dir=os.path.abspath(os.path.dirname(__file__))

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + +os.path.join(base_dir , "dbnew.sqlite")
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

class Advisor(db.Model):
    __tablename__="Advisor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    photo_url = db.Column(db.String(50))
    call=db.relationship("Calls" , backref="advisor")

# def __repr__(self):
#             return "Advisor('{}','{}')".format(self.name,self.photo_url)
    # booking_time=db.Column(db.DateTime)
    # booking_id=db.Column(db.Integer, unique=True)


class User(db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))
    admin = db.Column(db.Boolean)

# def __repr__(self):
#             return "User('{}','{}','{}','{}'')".format(self.name,self.email,self.password,self.admin)    


class Calls(db.Model):
    __tablename__="calls"
    booking_id =db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    advisor_id=db.Column(db.Integer,db.ForeignKey("Advisor.id"))
    booking_time=db.Column(db.DateTime)

# def __repr__(self):
#             return "Calls('{}','{}','{}')".format(self.user_id,self.advisor_id,self.booking_time)     

db.create_all()
db.session.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None

        if "access-token" in request.headers:
            token = request.headers["access-token"]

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data=(token,app.config['SECRET_KEY'])
            
        except:
            return jsonify({'message' : "token in valid" }), 401
            

        return f(token, *args, **kwargs)

    return decorated

#add_an_advisor
@app.route("/admin/advisor", methods=["POST"])
def add_an_advisor():
        name={}
        photo_url={}      

        try:
            name=request.json["name"]
            photo_url=request.json["photo_url"]
            new_advisor=Advisor(name=name,photo_url=photo_url)     
            db.session.add(new_advisor)
            db.session.commit()           
            return make_response('OK', 200)

        except:
            if not name or not photo_url:
                return make_response('BAD_REQUEST', 400)

            
    

#user_registration
@app.route("/user/register", methods=["POST"])
@token_required
def add_an_user(token):
    
    email={}
    password={}
    name={}

    try:
        name=request.json["name"]
        email=request.json["email"]
        password=request.json["password"]
        hashed_password=generate_password_hash(password,method="sha256")
        new_user=User(name=name,email=email,password=hashed_password,admin=True)
        db.session.add(new_user)    
        db.session.commit()
        userid= new_user.id
        return jsonify({"id" : userid, "token" : token})

    except:
        if not email or not password:
             return make_response("BAD_REQUEST" , 400)


#user_login_ username="admin"_Password="admin"
@app.route("/user/login")
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password :
        return make_response('Could not verify1', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify user', 401, {'WWW-Authenticate' : 'Basic realm="not a user!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'id' : user.id, 'exp' : dt.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token, "id": user.id })

    return make_response('Could not verify3', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})    


#advisor_list
@app.route("/user/<user_id>/advisors", methods=["GET"])
def get_advisor_list(user_id):
     current_user= User.query.filter_by(id=user_id).first()

     if not current_user:
        return jsonify ( { "msg" : " no user found"})
    
     advisors=Advisor.query.all()
     output=[]
     for advisor in advisors:
         advisor_data={}
         advisor_data["name"]=advisor.name
         advisor_data["photo_url"]=advisor.photo_url
         advisor_data["advisor_id"]=advisor.id
         output.append(advisor_data)

     return jsonify ({ "advisors" : output })   

# advisor_booking
@app.route("/user/<user_id>/advisor/<advisor_id>", methods=["POST"])
def book_a_call(user_id,advisor_id): 

    current_user= User.query.filter_by(id=user_id).first()
    current_advisor= Advisor.query.filter_by(id=advisor_id).first()

    if not current_user:
        return make_response('No user found', 400,)
        # return jsonify ( { "msg" : " no user found"})

    if not current_advisor: 
        # return jsonify ( { "msg" : " no advisor found"})  
        return make_response('No  advisor found', 400,)

    booking_time={}

    try:
        booking_time=request.json["booking_time"]
        new_call=Calls(booking_time=dt.strptime(booking_time,"%d/%m/%Y %H:%M:%S"),user_id=current_user.id, advisor_id=current_advisor.id )
        db.session.add(new_call)
        db.session.commit()

    except:
        if not booking_time:
          return make_response('Enter the time in format = date/month/year hour:minutes:seconds ', 400,)  
          # return jsonify( { "msg" : "enter the time", "format": "date/month/year hour:minutes:seconds"})

    return make_response("ok" , 200)

#booking_list
@app.route("/user/<user_id>/advisor/booking", methods=["GET"])
def booked_call_list(user_id):
    current_user= User.query.filter_by(id=user_id).first()

    bookings=db.session.query(Advisor,Calls).outerjoin(Calls, Advisor.id == Calls.advisor_id).filter(Calls.user_id==current_user.id)
   
    output=[]
    for booking in bookings:
        if booking[1]:
                booking_data={ }
                booking_data["name"]= booking[0].name
                booking_data["photo_url"]=booking[0].photo_url
                booking_data["advisor_id"]=booking[0].id
                booking_data["booking_id"]=booking[1].booking_id
                booking_data["time"]=booking[1].booking_time
                output.append(booking_data)
        
    return jsonify({"msg" :output})



if __name__ == '__main__':
     app.run()