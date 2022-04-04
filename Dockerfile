FROM python:3.9-slim

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY texts.py .
COPY format_helper.py .
COPY const_variables.py .
COPY package.py .
COPY database.py .
COPY main.py .

CMD ["python", "./main.py"]