# Gym Class reserver

This is the backend for the Gym class reserver. It runs inside of a Docker container and uses MongoDB as its database. The reservation work is done with selenium chromedriver.

## Run
On a linux server that has a docker installed you can just run the following commands in the /gym_class_booking folder and you are up and running :D

Of course you have to create your MongoDB and link it to the backend and create a file to 'credentials/credential.py' where you save the MONGO_URL variable. After this you are good to go :)

```
$ docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome

$ docker build -t gym_classes .

$ docker run --rm --network host --name my_gym_classes gym_classes
```

## Automatically adding classes to Google Calendar
1. Start by enabling Google Calendar API and creating the token.pickle file (follow these instructions to do these things: https://developers.google.com/calendar/quickstart/python). 

2. Before running the `quickstart.py` script, that creates token.pickle file, **remember to change the** 
```python
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
```
 to
```python
SCOPES = ['https://www.googleapis.com/auth/calendar']
```
in the `quickstart.py`. This way you will give the access to create the calendar events and not only to read them.

3. After this you can just add the token.pickle to the /credentials folder.