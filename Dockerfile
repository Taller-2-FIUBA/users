FROM python:3.11

RUN mkdir -p /home/app

COPY ./users /home/app
COPY . /home/

WORKDIR /home/app

RUN pip install --no-cache-dir --upgrade -r /home/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

