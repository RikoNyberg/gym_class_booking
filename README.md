# Gym Class reserver

This is the backend for the Gym class reserver. It runs inside of a Docker container and uses MongoDB as its database. The reservation work is done with selenium chromedriver.

## Run
On a linux server that has a docker installed you can just run the following commands in the /gym_class_booking folder and you are up and running :D

Of course you have to create your MongoDB and link it to the backend but after that you are good to go.

```
$ docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome

$ docker build -t gym_classes .

$ docker run --rm --network host --name my_gym_classes gym_classes
```
