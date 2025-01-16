# LET ME USE MY 5G!

My huawei router is dumb. Every day it reset to 4G insteard 5G conection. 
I'm tired of this. Enough!. 
I will make a script to check if the router is in 5G and if not, it will play with settings until it is in 5G.
I found that when you switch from `auto` to `4G only` and then back to `auto`, the router will connect to 5G. Why they didnt made `5G only` option? I dont know.

## How to use
1. Clone this repo
2. Add config to `.env`
3. Install requirements
```
pip install -r requirements.txt
```
3. Run `python3 main.py` to see if it works
4. Add to crontab to run every 5 minutes
```
*/5 * * * * /usr/bin/python3 /path/to/main.py
```
