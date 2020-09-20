from flask import Flask
from flask import Response
from flask import request
from redis import Redis
from datetime import datetime
import MySQLdb
import sys
import redis 
import time
import hashlib
import os
import json
from flask import jsonify

app = Flask(__name__)
startTime = datetime.now()
R_SERVER = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379)
db = MySQLdb.connect("mysql","root","password")
cursor = db.cursor()

@app.route('/init')
def init():
    cursor.execute("DROP DATABASE IF EXISTS RBACDB")
    cursor.execute("CREATE DATABASE RBACDB")
    cursor.execute("USE RBACDB")
    sql = """CREATE TABLE DATA (
         ID int,
         DATA char(30)
     )"""
    cursor.execute(sql)
    db.commit()
    return jsonify(status = 'DB Init Done') 

@app.route("/data/", methods=['POST'])
def add_users():
    req_json = request.get_json()   
    cursor.execute("INSERT INTO RBACDB.DATA (ID, DATA) VALUES (%s,%s)", (req_json['uid'], req_json['data']))
    db.commit()
    return jsonify({"Added": req_json['data']}), 200

@app.route('/data/<uid>')
def get_users(uid):
    hash = hashlib.sha224(str(uid)).hexdigest()
    key = "sql_cache:" + hash
    
    if (R_SERVER.get(key)):
        return R_SERVER.get(key) + "(c)" 
    else:
        cursor.execute("select DATA from RBACDB.DATA where ID=" + str(uid))
        data = cursor.fetchone()
        if data:
            R_SERVER.set(key,data[0])
            R_SERVER.expire(key, 36);
            return R_SERVER.get(key)
        else:
            return "Record not found"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)