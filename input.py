from flask import Flask, render_template, request,jsonify
import pandas as pd
import re
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import sqlite3

app = Flask(__name__,template_folder='template')
#Swagger Config
app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)
#end of swagger config

#Text cleansing function
def lowercase(text):#lowercase letters
    return text.lower()
def remove_emoticon_byte(text):#remove emote
    text = text.replace("\\", " ")
    text = re.sub('x..', ' ', text)
    text = re.sub(' n ', ' ', text)
    text = re.sub('\\+', ' ', text)
    text = re.sub('  +', ' ', text)
    return text
def remove_early_space(text):#remove blank space at start
    if text[0] == ' ':
        return text[1:]
    else:
        return text
def remove_unnecessary_char(text):
    text = re.sub('\n',' ',text) # Remove every '\n'
    text = re.sub('rt',' ',text) # Remove every retweet symbol
    text = re.sub('user',' ',text) # Remove every username
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',text) # Remove every URL
    text = re.sub('  +', ' ', text) # Remove extra spaces
    text = re.sub(':', ' ', text)
    text = re.sub(';', ' ', text)
    text = re.sub('\\+n', ' ', text)
    text = re.sub('\n'," ",text) # Remove every '\n'
    text = re.sub('\\+', ' ', text)
    text = re.sub('  +', ' ', text) # Remove extra spaces
    return text   
def remove_nonalphanumeric(text):#remove non alpha numeric
    text = re.sub('[^0-9a-zA-Z]+', ' ', text) 
    return text

def cleanse(text):#calls text cleansing function
   text=lowercase(text)#1
   text=remove_emoticon_byte(text)#2
   text=remove_unnecessary_char(text)#3
   text=remove_nonalphanumeric(text)#4
   text=remove_early_space(text)#5
   return text
#------------End of Text Cleansing-------------

#Fungsi Database
#Text Input Database
def textserver(before,after):
    conn=sqlite3.connect('Clean_Tweet.db')
    cursor=conn.cursor() 
    conn.execute('''CREATE TABLE IF NOT EXISTS Tweets
                    (Text_Input varchar(255),
                    Processed_Tweet varchar(255)
                    );''')#create table name Tweets with 2 collumns Text_Input and Processed_Tweet
    cursor.execute('''INSERT INTO Tweets (Text_Input,Processed_Tweet) VALUES (?,?);''',(before,after))
    conn.commit()
    cursor.close()

#File Input Database
def data_entry(before,after):
    conn=sqlite3.connect('Clean_Tweet.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS Tweets
                    (Text_Input varchar(255),
                    Processed_Tweet varchar(255)
                    );''')#create table name Tweets with 2 collumns Text_Input and Processed_Tweet
    for i in range(len(before)):
        conn.execute("INSERT INTO Tweets(Text_Input,Processed_Tweet) VALUES(?,?)", (before[i],after[i]))
    conn.commit()#Iteration to input list
#End of Save to Database

#File Input
@swag_from("docs/files.yaml", methods=['POST'])
@app.route('/file', methods = ['POST'])
def upload_file():   
   #Get files 
   f = request.files['file']
   #CSV to pandas DataFrame
   df=pd.read_csv(f,header=0,encoding='latin-1')
   df['Clean Text']=df.apply(lambda row: cleanse(row['Tweet']), axis = 1)#cleanse text on tweet collumn
   result = df['Clean Text'].to_list()
   before= df['Tweet'].to_list()
   data_entry(before,result)#call function data_entry
   #JSON Response
   json_response = {
      'status_code': 200,
      'description': "sudah dilakukan cleansing"
      }
   response_data=jsonify(json_response)
   return response_data

#Text Input
@swag_from("docs/texts.yaml", methods=['POST'])
@app.route('/text', methods = ['POST'])
def upload_text():
   #Input text
   f=request.form['text']
   #Cleansing Process
   result=cleanse(f)
   textserver(f,result)#call function textserver
   json_response = {
        'status_code': 200,
        'description': "sudah dilakukan cleansing",
        'data': result,
        }
   response_data=jsonify(json_response)
   return response_data

if __name__ == '__main__':
   app.run(debug = True)