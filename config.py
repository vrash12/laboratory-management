import os

class Config:
    SECRET_KEY = "123"
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/tsu_ccs_lab_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
