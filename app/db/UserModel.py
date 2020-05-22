from flask import g
from psycopg2 import sql
from werkzeug.security import generate_password_hash,check_password_hash
from ..email import send_email
import os

class User:
    tablename = 'users'
    def __init__(self,username,role_id,password):
        self.username = username
        self.role_id = role_id
        self.password = password
        self.in_db = False
        if self.check_user() is False:
            self.insert_user()
    
    def check_user(self):
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_query = sql.SQL('''SELECT * FROM {} WHERE username 
            = %s;''').format(sql.Identifier(self.tablename))
            cursor.execute(sql_query,(self.username,))
            users = cursor.fetchall()
            print ('These are the user results: ', users)
            if len(users) == 0:
                return False
            else:
                self.in_db = True
                return True
        except:
            print ('Something went wrong while checking for the user')

    @property
    def password(self): 
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def insert_user(self):
        print ("We're in the insert user function")
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_insert = sql.SQL('''INSERT INTO {} (username,role_id,password_hash)
                VALUES (%s,%s,%s)''').format(sql.Identifier(self.tablename))

            cursor.execute(sql_insert,(self.username,self.role_id,self.password_hash))
            conn.commit()
            self.in_db = True
            send_email(os.environ.get('ADMIN_EMAIL'),
                   'New User', 'mail/new_user', name=self.username)
            cursor.close()
        except:
            print ('Something went wrong with the insertion')