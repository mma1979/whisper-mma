import boto3
from botocore.exceptions import NoCredentialsError
from flask import Flask, render_template, request
from flask import send_file, redirect
from werkzeug.utils import secure_filename
import os

from utils import Utils
from engine import WhipsMMAEngine
from upload_form import UploadForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
s3 = boto3.client('s3',
                  endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
                  aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", 'admin'),
                  aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", 'Abc@1234'),
                  config=boto3.session.Config(signature_version='s3v4'),
                  region_name='us-east-1')

bucket_name = os.environ.get("S3_BUCKET_NAME", 'whisper-mma')


def get_all_files():
    files = []

    try:
        result = s3.list_objects(Bucket=bucket_name)

        if 'Contents' in result:
            files = [content['Key'] for content in result['Contents']]
    except:
        pass

    return files


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.is_submitted():
        f = form.file.data
        model = form.model.data
        language = form.language.data
        compute_type = 'float32'  # form.compute_type.data
        filename = secure_filename(f.filename)
        try:
            f.save(os.path.join(app.root_path, 'files', filename))
            Utils.log_info(f'Uploading {filename}')
            s3.upload_fileobj(f, bucket_name, filename)
            engine = WhipsMMAEngine(s3, bucket_name, model, compute_type)
            engine.generate_conversation_file(filename)
            return redirect("/files", code=302)
        except NoCredentialsError:
            return 'Missing credentials'
    return render_template('upload.html', form=form)


@app.route('/files')
def files():
    file_list = get_all_files()
    return render_template('files.html', files=file_list)


@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(app.root_path, 'files', filename)
    s3.download_file(bucket_name, filename, path)
    return send_file(path, as_attachment=True)


@app.route('/clean', methods=['POST'])
def clean_workspace():
    # clean Local files
    work_files = os.listdir(os.path.join(app.root_path, 'files'))
    for file in work_files:
        os.remove(os.path.join('files', file))

    # clean s3 files
    response = s3.list_objects_v2(Bucket=bucket_name)
    for obj in response['Contents']:
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])

    # clean log file
    log_file_path = os.path.join(app.root_path, 'logs', 'log.txt')
    log_file = open(log_file_path, 'r+')
    log_file.truncate(0)

    return redirect("/", code=302)


@app.route('/log', methods=['GET'])
def log():
    log_file = os.path.join(app.root_path, 'logs', 'log.txt')
    with open(log_file, 'r') as f:
        return f.read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
