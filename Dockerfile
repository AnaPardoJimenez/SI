
FROM python:3.12


WORKDIR /app


COPY requirements.txt requirements.txt


RUN pip install --no-cache-dir -r requirements.txt





EXPOSE 5051
EXPOSE 5050


CMD ["python"]