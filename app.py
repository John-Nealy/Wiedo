from flask import Flask, render_template, request, redirect, session, url_for, send_file, abort
from werkzeug.utils import secure_filename
import sqlite3 as sql
import os
import hashlib

#Viewing Documents
from docx import Document
import PyPDF2

#removing folders
import shutil

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
#Initial Landing Page
@app.route('/')
def login():
    if 'username' in session:
        return redirect('/home')
    return render_template('index.html')

@app.route('/Create',methods = ['POST', 'GET'])
def Create():
    return render_template("create.html") 

@app.route('/CreateUser', methods = ['POST', 'GET'])
def CreateUser():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password'].encode("utf-8")
            hashedPass = hashlib.new("sha512", password)

            with sql.connect("users.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)",(username, hashedPass.hexdigest()))
                con.commit()
            
            os.makedirs(app.config['USERS_FILE_PATH'] + f'/{username}')
            os.makedirs(app.config['USERS_FILE_PATH'] + f'/{username}/Files')
        except:
            con.rollback()
        finally:
            
            return render_template("index.html", )

@app.route('/LoggingIn',methods = ['POST', 'GET'])
def LoggingIn():
    if request.method == 'POST':
        try:
            user = ''
            name = request.form['username']
            password = request.form['password'].encode("utf-8")
            hashedPass = hashlib.new("sha512", password)
            with sql.connect("users.db") as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users WHERE username = ? AND password = ?",(name, hashedPass.hexdigest()))
                user = cur.fetchall()
                con.close()
        except:
            con.rollback()
            user = ''
        finally:
            if len(user) > 0:
                for row in user:
                    session['UserID'] = row[0]
                    session['username'] = row[1]
                    session['url'] = ''
                return redirect("/home")
            else:
                print("NUH UH")
                return redirect("/")
    else:
        return redirect("/")
@app.route('/home', methods = ['POST', 'GET'])
def Home():
    if 'username' in session:
        name = session['username']
        UserID = session['UserID']
        session['url'] = url_for('Home')
        session['folderPath'] = f'{app.config["USERS_FILE_PATH"]}/{name}/Files/'
        folders = []
        files = []
        
        
        folders, files = return_elements(f'{app.config["USERS_FILE_PATH"]}/{name}/Files')
        return render_template("home.html", name = name, folders = folders, files = files)
    return redirect("/")

@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    name = session['username']
    if request.method == 'POST':
            file = request.files['files']
                # If the user does not select a file, the browser submits an
                # empty file without a filename.
            if file.filename == '':
                print('No selected file')
                return redirect(request.url)
            if file:
                print('test')
                filename = secure_filename(file.filename)
                file.save(os.path.join(f'{session["folderPath"]}', filename))
                folders, files = return_elements(f'{session["folderPath"]}')
                return render_template("home.html", name = name, folders = folders, files = files)
                

@app.route('/view', methods = ['POST', 'GET'])
def view():
    name = session['username']
    UserID = session['UserID']
    session['url'] = url_for('view')
    if request.method == "POST":
        
        request_content = request.form['content']

        path = findPath(name, request_content)
        
        if request.form['action'] == 'view':
            if '.' in request_content:
                match request_content.split('.')[1]:
                    case 'txt':
                        with open(f"{path}/{request_content}", 'r') as file:
                            contents = file.read()
                            print(contents)
                            return render_template('fileReader.html', name=name, fileContents = contents)
                    case 'jpeg' | 'png' | 'tif' | 'tiff' | 'eps' | 'raw' | 'jpg':
                        contents = f"{path}/{request_content}"
                        return render_template('fileReader.html', name=name, fileContents = contents)
                    case 'docx':
                        f = open(f"{path}/{request_content}", 'rb')    
                        doc = Document(f)
                        fullText = []
                        for para in doc.paragraphs:
                            fullText.append(para.text)
                        contents = '\n'.join(fullText)
                        return render_template('fileReader.html', name=name, fileContents = '', wordDoc = contents)
                    case 'pdf':
                       
                        pdfFileObj = open(f"{path}/{request_content}", 'rb')
                        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
                        print(pdfReader.numPages)
                        fullText = []
                        # creating a page object
                        n = range(pdfReader.numPages)
                        for x in n:
                            pageObj = pdfReader.getPage(x)
                            print(pageObj.extractText())
                            fullText.append(pageObj.extractText())
                            print(fullText)
                        # closing the pdf file object
                        pdfFileObj.close()
                        contents = '\n'.join(fullText)
                        return render_template('fileReader.html', name=name, fileContents = '', pdf = contents)
                    case 'MOV' | 'mov' | 'MP4' | 'mp4' | 'ogg' | 'OGG':
                        print('testing')
                        contents = f"{path}/{request_content}"
                        return render_template('fileReader.html', name=name, video = contents)



                       
            else:      
                folders, files = return_elements(path)
                session['folderPath'] = path
                return render_template("home.html", name = name, folders = folders, files = files)

@app.route('/download', methods = ['POST', 'GET'])
def download():
    
    if 'username in session':
        name = session['username']
        request_content = request.form['content']
        path = findPath(name, request_content)
        print(path)
        if request.method == 'POST':
            try:
                
                folders, files = return_elements(path)
                return send_file(f'{path}/{request_content}', as_attachment=True)
            except FileNotFoundError:
                abort(404)
    return redirect("/")

@app.route('/delete', methods = ['POST', 'GET'])
def delete():
    if 'username in session':
        name = session['username']
        request_content = request.form['content']
        if '.' in request_content:
            os.remove(f"{session['folderPath']}/{request_content}")
        else:
            shutil.rmtree(f"{session['folderPath']}/{request_content}")
        folders, files = return_elements(session['folderPath'])
        return render_template("home.html", name = name, folders = folders, files = files)

    return redirect("/")

@app.route('/new', methods = ['POST', 'GET'])
def new():
    if 'username in session':
        name = session['username']
        folderName = request.form['folder-name']
        os.mkdir(f"{session['folderPath']}/{folderName}")

        folders, files = return_elements(session['folderPath'])
        return render_template("home.html", name = name, folders = folders, files = files)

    return redirect("/")

@app.route('/settings')
def settings():
    if 'username' in session:
        name = session['username']
        session['url'] = url_for('settings')
        return render_template("settings.html", name = name)
    return redirect("/")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='80')

def return_elements(path):
    files = []
    folders = []
    Contents = os.listdir(path)
    for content in Contents:
        if '.' in content:
            files.append(content)
        else:
            folders.append(content)
    print(Contents)
    return folders, files

def findPath(name, request_content):
    user_directories = [(x[0], x[2]) for x in os.walk(f'{app.config["USERS_FILE_PATH"]}/{name}/Files')]
    for d in user_directories:
        if "." in request_content:
            for e in d[1]:
                if e == request_content:
                    path = d[0]
                    print(path)
                    return path
        else:
            d_split = d[0].split('/')
            for e in d_split:
                if e == request_content:
                    path = d[0]
                    print(path)
                    return path
