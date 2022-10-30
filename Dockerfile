FROM python:3.10

# Tip from https://stackoverflow.com/questions/63892211
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      jq \
      sqlite3

COPY requirements.txt .
RUN python -mpip install --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

# Easiest to just do a `. ~/.bash_aliases to get handy shortcuts
COPY bash.bash_aliases .bash_aliases

WORKDIR /app
COPY ./src .

RUN mkdir /data

CMD [ "bash", "get_tesla_gateway_meter_data.sh"]
