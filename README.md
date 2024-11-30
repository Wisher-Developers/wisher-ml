# wisher_ml

# Deploying application

To deploy application you should have [Docker](https://www.docker.com/) installed in your system.

To start application just execute:
`docker compose up --build -d`

At first run you should also add topics needed to Kafka server:
```
docker exec kafka kafka-topics.sh --create --topic product-add --bootstrap-server localhost:9092
docker exec kafka kafka-topics.sh --create --topic product-search --bootstrap-server localhost:9092
```

# Data structures accepted by Kafka

## Channel: `product-add`
format: JSON

**Incoming messages**

```
{"uuid": "<external_product_uuid>", "content": "<product_description>"}
```

**Outgoing messages**
```
Not available
```

**Testing**
```
docker exec -it kafka kafka-console-producer.sh --bootstrap-server localhost:9092 --topic product-add
```
Enter test message in console and press: Ctrl+D

## Channel: `product-search`
format: JSON

**Incoming messages**

```
{
    "request_id": "<unique_request_id>",
    "products": [
        "<product_uuid_1>",
        "<product_uuid_2>",
        "<product_uuid_3>"
    ]
}
```

**Outgoing messages**
```
{
    "request_id": "<unique_request_id>",
    "response": True,
    "products": [
        "<product_found_uuid_1>",
        "<product_found_uuid_2>",
        "<product_found_uuid_3>"
    ]
}
```

# Preparing new migrations using Alembic

`docker exec -it wisher_app alembic revision --autogenerate -m "Migration short description"`
