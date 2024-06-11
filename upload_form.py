from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms.fields.core import SelectField


class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    model = SelectField('model',
                        choices=[('tiny', 'tiny'), ('base', 'base'), ('small', 'small'), ('medium', 'medium'), 
                                 ('large', 'large'), ('large-v1', 'large-v1'), ('large-v2', 'large-v2'),
                                 ('large-v3', 'large-v3')], default='small')
    language = SelectField('language',
                           choices=[('Automatic Detection', 'Automatic Detection'), ('English', 'English'),
                                    ('German', 'German')], default='Automatic Detection')
    compute_type = SelectField('compute_type',
                               choices=[('int8', 'int8'), ('float16', 'float16'), ('int8_float16', 'int8_float16'),
                                        ('float32', 'float32'), ('int8_float132', 'int8_float132')], default='int8')
