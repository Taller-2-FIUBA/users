FROM python:3.11

COPY . .

RUN pip install pip --upgrade
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR .

CMD ["uvicorn", "users.main:app", "--host", "0.0.0.0", "--port", "8000"]

