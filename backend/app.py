# app.py
from flask import Flask,render_template,request,jsonify
import json
import pymysql
from flask_cors import CORS

app = Flask(__name__,template_folder="../frontend/build",static_folder="../frontend/build",static_url_path="")
app.config["JSON_AS_ASCII"] = False
CORS(app)
db = pymysql.connect(host='localhost',user='root',database='industrial_map',passwd='123',port=3306)

@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data = json.loads(request.get_data(as_text=True))
        cursor = db.cursor()
        sql = "select * from user_account where name='%s'" % data["user_name"]
        cursor.execute(sql)
        if cursor.fetchall():
            return {'code': 0,'error':"用户名已存在"}
        sql = "select * from user_account where email='%s'" % data["user_mail"]
        cursor.execute(sql)
        if cursor.fetchall():
            return {'code': 0,'error':"邮箱已存在"}
        sql = "insert into user_account values(null,'{name}','{pw}','{email}','tourist')"
        sql = sql.format(name=data["user_name"],pw=data["user_pwd"],email=data['user_mail'])
        cursor.execute(sql)
        db.commit()
        print("成功")
        msg = {'code': 1}
        return jsonify(msg)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data = json.loads(request.get_data(as_text=True))
        cursor = db.cursor()
        sql = "select password,name,type from user_account where name='%s'"%data["user_name"]
        cursor.execute(sql)
        account = cursor.fetchone()
        if account:
            if account[0] == data['user_pwd']:
                print("登陆成功")
                msg = {
                    "code": 1,
                    "cookie": {
                        "sessionName": account[1],
                        "type": account[2]
                    }
                }
                return jsonify(msg)
            else:
                #密码错误
                msg = {
                    "code": 0
                }
                return jsonify(msg)
        else:
            #用户名不存在
            return "用户名不存在"
        db.commit()

@app.route('/imap', methods=['GET','POST'])
def click():
    if request.method == 'POST':
        data = json.loads(request.get_data(as_text=True))
        cursor = db.cursor()
        if data["en_type"]:
            sql = "select * from enterprise where type='%s'" % data["en_type"]
            cursor.execute(sql)
            enterprises = cursor.fetchall()
            sql = "select * from material where id in " \
                  "(select ma_id from enter_mater where " \
                  "en_id in (select id from enterprise where type='%s'))" % data["en_type"]
            cursor.execute(sql)
            materials = cursor.fetchall()
            msg = {
                'enterprise_info': enterprises,
                'Material': materials
            }
            return jsonify(msg)
        if data['chosen_material']:
            if data['chosen_province']:
                sql = "select city from enterprise where province='%s'" % data["chosen_province"]
                cursor.execute(sql)
                cities = cursor.fetchall()
            else:
                sql = "select city from enterprise where id in " \
                      "(select en_id from enter_mater where " \
                      "ma_id in (select id from material where name = '%s'))" % data["chosen_material"]
                cursor.execute(sql)
                cities = cursor.fetchall()
            sql = "select * from enterprise where id in " \
                      "(select en_id from enter_mater where " \
                      "ma_id in (select id from material where name = '%s'))" % data["chosen_material"]
            cursor.execute(sql)
            enterprises = cursor.fetchall()
            sql = "select * from material where name = '%s'" % data["chosen_material"]
            cursor.execute(sql)
            materials = cursor.fetchone()
            msg = {
                'cities_name' : cities,
                'enterprise_info' : enterprises,
                'Material' :
                    {
                        'id' : materials[0],
                        'name' : materials[1],
                        'content' : materials[2]
                    }
            }
            return jsonify(msg)
        else:
            sql = "select city from enterprise where province='%s'" % data["chosen_province"]
            cursor.execute(sql)
            cities = cursor.fetchall()
            sql = "select * from enterprise where province='%s'" % data["chosen_province"]
            cursor.execute(sql)
            enterprises = cursor.fetchall()
            sql = "select * from material where id in " \
                  "(select ma_id in enter_mater where " \
                  "en_id in (select id from enterprise where province='%s'))" % data["chosen_province"]
            cursor.execute(sql)
            materials = cursor.fetchall()
            msg = {
                'cities_name': cities,
                'enterprise_info': enterprises,
                'Material': materials
            }
            return jsonify(msg)

@app.route('/mdata', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        data = json.loads(request.get_data(as_text=True))
        cursor = db.cursor()
        if data["type"] == "insert":
            if data["table"] == "material":
                sql = "insert into material values(null,'{name}','{intro}')"
                sql = sql.format(name=data["ma_name"],intro=data["introduction"])
                cursor.execute(sql)
                db.commit()
            elif data["table"] == "enterprise":
                sql = "select id from enterprise where name='%s'" % data["en_name"]
                cursor.execute(sql)
                en_id = cursor.fetchone()
                if not en_id:
                    sql = "insert into enterprise values(null,'{name}','{pro}','{city}',{amount},'{type}',{long},{lati})"
                    sql = sql.format(name=data["en_name"],pro=data["province"],
                                     city=data["city"],amount=data["amount"],type=data["en_type"],
                                     long=data["longitude"],la=data["latitude"])
                    cursor.execute(sql)
                    db.commit()
                sql = "select id from material where name='%s'" % data["ma_name"]
                cursor.execute(sql)
                ma_id = cursor.fetchone()
                sql = "insert into enter_mater values(null,{en},{ma})"
                sql = sql.format(en=en_id[0],ma=ma_id[0])
                cursor.execute(sql)
                db.commit()
            return "添加成功"
        elif data["type"] == "delete":
            if data["table"] == "material":
                sql = "delete from material where name='%s'" % data['en_name']
                cursor.execute(sql)
                db.commit()
            elif data["table"] == "enterprise":
                sql = "delete from enterprise where name='%s'" % data['en_name']
                cursor.execute(sql)
                db.commit()
            return "删除成功"
        else:
            column_name = ["province","city","amount","en_type","longitude","latitude"]
            for i in column_name:
                if data[i] != "":
                    if i == "amount":
                        sql = "update enterprise set amount={new} where name='{name}'"
                        sql = sql.format(new=int(data[i]), name=data["en_name"])
                    elif i == "longitude" or i == "latitude":
                        sql = "update enterprise set {col}={new} where name='{name}'"
                        sql = sql.format(col=i, new=float(data[i]), name=data["en_name"])
                    else:
                        sql = "update enterprise set {col}='{new}' where name='{name}'"
                        sql = sql.format(col=i,new=data[i], name=data["en_name"])
            cursor.execute(sql)
            db.commit()
            return "修改成功"

        #print("成功")
        msg = {'code': 0}
        return jsonify(msg)

if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)