FROM continuumio/miniconda3

WORKDIR /app
COPY . .

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install pyannote.audio

EXPOSE 80
ENTRYPOINT ["python3", "app.py"]