# RSA_Projeto
RSA_Projeto

# How to start Vanetza
## Prerequisites
- Docker
- Docker Compose
- Python 3.8 or higher

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo bash -c 'echo "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker-ce.list'
sudo apt update
sudo apt install docker-ce docker-compose
```

## Install vanetza
```bash
cd vanetza-nap
docker network create vanetzalan0 --subnet 192.168.98.0/24
```

## How to run vanetza

```bash
cd vanetza-nap
docker-compose up
```

# How to run the flask app

## Prerequisites

- Python 3.8 or higher
- Flask
- Flask-SocketIO
- Flask-Cors

## Start Backend
```bash
cd dashboard
python3 server.py
```

## Start Frontend
```bash
cd dashboard/app
npm run start
```