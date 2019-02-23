
# FROM python:3

FROM ubuntu:18.04

LABEL MAINTAINER="riko@riko.fi"

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-setuptools \
    build-essential

#######

# # Install wget.
# RUN apt-get install -y wget
# # Set the Chrome repo.
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
#     && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
# # Install Chrome.
# RUN apt-get update && apt-get -y install google-chrome-stable

#######

#######
# # Install wget.
# RUN apt-get install -y wget
# RUN apt-get install -y curl
# # install google chrome
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
# RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
# RUN apt-get -y update
# RUN apt-get install -y google-chrome-stable

# # install chromedriver
# RUN apt-get install -yqq unzip
# RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
# RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# # set display port to avoid crash
# ENV DISPLAY=:99

# # install selenium
# RUN pip3 install selenium==3.8.0

#######
# RUN apt-get install -y curl
# # Install Chrome for Selenium
# RUN curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /chrome.deb
# RUN dpkg -i /chrome.deb || apt-get install -yf
# RUN rm /chrome.deb

# # Install chromedriver for Selenium
# RUN curl https://chromedriver.storage.googleapis.com/2.46/chromedriver_linux64.zip -o /usr/local/bin/chromedriver
# RUN chmod +x /usr/local/bin/chromedriver

#######

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

CMD [ "python3", "gym_classes.py" ]

