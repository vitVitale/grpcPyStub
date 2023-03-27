## gRPC STUBS ##


> :warning: **Сборка docker образа**: 


#### Интерактивная документация: ####

* swagger -> http://127.0.0.1:8022/docs


## Пример использования с cURL
#### Создание заглушки на ендпоинт [service=ExampleService, rpc=GetUserById]
```commandline
curl -X POST 'http://localhost:8022/define_stub?service=ExampleService&rpc=GetUserById' \
-H 'Content-Type: application/json' \
-d '{
  "status": "OK",
  "user": {
    "name": "Vit",
    "surname": "Vitale",
    "email": "viiiittt@gmail.com",
    "phone": "123456789",
    "subscriptionData": [
      {
        "isPremium": {
            "data": true
        },
        "expiresAt": {
            "null": null
        },
        "serviceType": "FOOD_DELIVERY",
        "agreementDate": "2023-01-13T20:38:31.000223242Z"
      }
    ]
  }
}'
```

#### Просмотр установленных заглушек
```commandline
curl -X GET 'http://localhost:8022/stubs' \
-H 'accept: application/json'
```

#### Просмотр запросов по всем методам сервисов
```commandline
curl -X GET 'http://localhost:8022/requests' \
-H 'accept: application/json'
```
