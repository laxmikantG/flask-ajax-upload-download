import os
import json
import urllib
import h5py
import pickle as pk
import numpy as np

from os.path import join, dirname, realpath
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, flash
from werkzeug.utils import secure_filename
from keras.preprocessing.image import img_to_array, load_img

#from keras.models import load_model
#import engine # remember to reinclude this

# A <form> tag is marked with enctype=multipart/form-data and an <input type=file> is placed in that form.
# The application accesses the file from the files dictionary on the request object.
# use the save() method of the file to save the file permanently somewhere on the filesystem.

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static', 'uploads') # where uploaded files are stored
ALLOWED_EXTENSIONS = set(['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG', 'gif', 'GIF']) # models support png and gif as well

#location_model = load_model('d3_ft_model.h5')
print ("Location model loaded")
#severity_model = load_model('d3_ft_model.h5')
print ("Severity model loaded")


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # max upload - 10MB
app.secret_key = 'secret'

# check if an extension is valid and that uploads the file and redirects the user to the URL for the uploaded file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('index.html', result=None)

@app.route('/<a>')
def available(a):
    flash('{} coming soon!'.format(a))
    return render_template('index.html', result=None, scroll='third')

@app.route('/assessment')
def assess():
    return render_template('index.html', result=None, scroll='third')

def location_assessment(img_256, model):
    print ("Determining location of damage...")
    pred = model.predict(img_256)
    pred_label = np.argmax(pred, axis=1)
    d = {0: 'Front', 1: 'Rear', 2: 'Side'}
    for key in d.iterkeys():
        if pred_label[0] == key:
            return d[key]

def severity_assessment(img_256, model):
    print ("Determining severity of damage...")
    pred = model.predict(img_256)
    pred_label = np.argmax(pred, axis=1)
    d = {0: 'Minor', 1: 'Moderate', 2: 'Severe'}
    for key in d.iterkeys():
        if pred_label[0] == key:
            return d[key]

def prepare_img_256(img_path):
    img = load_img(img_path, target_size=(256, 256)) # this is a PIL image 
    x = img_to_array(img) # this is a Numpy array with shape (3, 256, 256)
    x = x.reshape((1,) + x.shape)/255
    return x


@app.route('/assessment', methods=['GET', 'POST'])
def upload_and_classify():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('assess'))
        
        file = request.files['file']

        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('assess'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename) # used to secure a filename before storing it directly on the filesystem
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(filepath)
            file.save(filepath)
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
#            model_results = engine.engine(filepath)
            img_256 = prepare_img_256(filepath)
#            x = location_assessment(img_256, location_model)
#            y = severity_assessment(img_256, severity_model)
            model_results = {'gate1': 'Car validation check: ', 
    'gate1_result': 1, 
    'gate1_message': {0: None, 1: None},
    'gate2': 'Damage presence check: ',
    'gate2_result': 1,
    'gate2_message': {0: None, 1: None},
    'location': "",
    'severity': "",
    'final': 'Damage assessment complete!'}
            return render_template('results.html', result=model_results, scroll='third', filename=filename)
    
    flash('Invalid file format - please try your upload again.')
    return redirect(url_for('assess'))


# @app.route('/show/<filename>')
# def uploaded_file(filename):
#     return render_template('template.html', filename=filename)

@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Now one last thing is missing: the serving of the uploaded files. 
# In the upload_file() we redirect the user to url_for('uploaded_file', filename=filename), 
# that is, /uploads/filename. So we write the uploaded_file() function to return the file of that name. 

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False) # remember to set back to False    
