# Gym Class reserver

Run:
$ docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome
$
$ docker build -t gym_classes .
$ docker run --rm --network host --name my_gym_classes gym_classes