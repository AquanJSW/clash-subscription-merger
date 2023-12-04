# Clash Subscription Merger

- 合并订阅
- 基于出入口 IP 去除假、重复节点
- 基于 IP 的地区筛选

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

>>> python main.py -s sub.yaml -t temp.yaml -o assets/config.yaml
Telegram bot is disabled
sub-a Fetching subscription
sub-b Fetching subscription
Using cached clash binary
Using cached maxmind db
sub-a Starting clash
sub-a 40 / 40 proxies accepted after name filter
sub-b Starting clash
sub-b 9 / 11 proxies accepted after name filter
sub-a 21 / 40 proxies accepted after ingress filter
sub-b 9 / 9 proxies accepted after ingress filter
sub-a 14 / 21 proxies accepted after connectivity filter
sub-a Filtering proxies by egress
sub-a egress ip lookup for 新加坡01, progress 1 / 14,
sub-b 6 / 9 proxies accepted after connectivity filter
sub-b Filtering proxies by egress
sub-b egress ip lookup for 日本 | 华东联通 | NATIVE | V1, progress 1 / 6,
sub-b egress ip lookup for 台湾 | 华东移动 | 宽频 | V1, progress 2 / 6,
sub-a egress ip lookup for 新加坡02, progress 2 / 14,
sub-b egress ip lookup for 香港 | 华东移动 | 宽频 | V1, progress 3 / 6,
sub-a egress ip lookup for 新加坡03, progress 3 / 14,
sub-b egress ip lookup for 柬埔寨 | 华东移动 | 宽频 | V1, progress 4 / 6,
sub-a egress ip lookup for 日本01, progress 4 / 14,
sub-a egress ip lookup for 日本02, progress 5 / 14,
sub-b egress ip lookup for 新加坡 | IPv6 直连 | NATIVE | V1, progress 5 / 6,
sub-a egress ip lookup for 日本03, progress 6 / 14,
sub-a egress ip lookup for 美国01, progress 7 / 14,
sub-a egress ip lookup for 美国02, progress 8 / 14,
sub-a egress ip lookup for 美国03, progress 9 / 14,
sub-a egress ip lookup for 香港01, progress 10 / 14,
sub-a egress ip lookup for 香港02, progress 11 / 14,
sub-a egress ip lookup for 香港03, progress 12 / 14,
sub-b egress ip lookup for 新加坡 | 华东移动 | NATIVE | V1, progress 6 / 6,
sub-a egress ip lookup for 香港04, progress 13 / 14,
sub-b 5 / 6 proxies accepted after egress filter
sub-a egress ip lookup for 香港10, progress 14 / 14,
sub-a 9 / 14 proxies accepted after egress filter
Wrote assets/config.yaml
```

## 安装

```shell
git clone --depth=1 https://github.com/AquanJSW/clash-subscription-merger.git
cd clash-subscription-merger
python3 -m pip install -U pip pipenv
# only tested on Python 3.11 and 3.12
python3 -m pipenv --python python3
python3 -m pipenv install
python3 -m pipenv run python main.py -h
```
