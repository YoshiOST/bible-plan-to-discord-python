
# Get Started with Bible Plan to Discord
this is the python version
## Dependencies

* **Python 3** — Required to run the script.
* **pytz** — Used for timezone-aware date handling.

### Install dependencies

```bash
python -m pip install pytz
```

All other dependencies (`json`, `csv`, `datetime`, `http.client`, `argparse`, `math`, `re`, `urllib.parse`, and `sys`) are included with Python.

## How does it send everyday?
Setup a config at https://yoshiost.com/planconfig
- you will need to get a webhook from the discord/message platform's channel where it will post.
- use a chron like program to run the run.sh
  - windows has taskscheduler
  - linux cron
- alternatively running ```python notify-plan.py send```
- if you need to simulate what happens please use ```python notify-plan.py test```
- boom everyday you see the plan sent.

[sample bible plan](https://github.com/YoshiOST/bible-plan-to-discord-python/blob/master/oneyearbible.lxbp)  

[lxbp format spec](https://www.luxbible.app/resources/lxbp)  

[sample config.json](https://github.com/YoshiOST/bible-plan-to-discord-python/blob/master/config.json)  

## Contact
https://www.twitch.tv/yoshiost
