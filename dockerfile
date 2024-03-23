FROM python:3.11


# Create a non-root user
RUN useradd -ms /bin/bash myuser
USER myuser


# Set proper directory permissions
USER root



RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# ENTRYPOINT ["python"]
CMD ["python","app.py" ]