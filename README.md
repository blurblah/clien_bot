<h1 align="center">Welcome to clien_bot 👋</h1>
<p>
  <a href="https://twitter.com/blurblah">
    <img alt="Twitter: blurblah" src="https://img.shields.io/twitter/follow/blurblah.svg?style=social" target="_blank" />
  </a>
</p>

> Clien bot crawls articles of 'allsell' board in clien.net and notifies to Telegram users who registered specific keywords.

## Requirements
Python 3.5.2+

MongoDB

RabbitMQ

## Prerequisites
1. Create a database named 'clien_bot'
2. Create two collections named 'crawl_info' and 'allsell'
3. Add a following document to crawl info
```json
{
    "_id": ObjectID(),
    "board": "allsell",
    "name": "사고팔고",
    "url": "https://www.clien.net/service/group/allsell",
    "latest_sn": 0
}
``` 

## Install dependencies
To use virtualenv is recommended.

```sh
pip3 install -r requirements.txt
```

## Run
```sh
python3 -m crawler
python3 -m bot
```

## Author

👤 **blurblah**

* Twitter: [@blurblah](https://twitter.com/blurblah)
* Github: [@blurblah](https://github.com/blurblah)

## Show your support

Give a ⭐️ if this project helped you!

***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_