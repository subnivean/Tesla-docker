FROM py39-pandas134

RUN apt-get update && apt-get install -y jq

WORKDIR /app

COPY ./src .

RUN mkdir /data

CMD [ "bash", "get_tesla_gateway_meter_data.sh"]
