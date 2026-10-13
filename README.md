# Get Started
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

## Contact
https://www.twitch.tv/yoshiost
