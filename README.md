# Clash Subscription Merger

- 合并订阅
- 去除假、重复节点
- 支持地区筛选

> 订阅配置文件与模板文件示例见 `assets` 目录

```plain
>>> python main.py -h
usage: main.py [-h] -s SUBSCRIPTION -t TEMPLATES [TEMPLATES ...] -o OUTPUTS [OUTPUTS ...] [-v] [--proxy PROXY] [--api-key API_KEY] [--chat-id CHAT_ID]

options:
  -h, --help            show this help message and exit
  -s SUBSCRIPTION, --subscription SUBSCRIPTION
                        subscription config file
  -t TEMPLATES [TEMPLATES ...], --templates TEMPLATES [TEMPLATES ...]
                        template files
  -o OUTPUTS [OUTPUTS ...], --outputs OUTPUTS [OUTPUTS ...]
                        output files / directory, same name as templates if directory is provided
  -v, --verbose
  --proxy PROXY         used to download subscriptions

bot options:
  --api-key API_KEY     telegram bot api key
  --chat-id CHAT_ID     telegram chat id

>>> python main.py -s sub.yaml -t temp.yaml -o out_dir
```
