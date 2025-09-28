import sys
import http.client
import json
import argparse
from datetime import datetime
try:
    import pytz
    print("pytz is installed")
except ImportError as e:
    print("Error -> ", e)
import pytz
import csv
import math
import re

# Bible book abbreviations
book_abbreviations = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM", "Deuteronomy": "DEU",
    "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "1 Samuel": "1SA", "2 Samuel": "2SA",
    "1 Kings": "1KI", "2 Kings": "2KI", "1 Chronicles": "1CH", "2 Chronicles": "2CH",
    "Ezra": "EZR", "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalm": "PSA", "Psalms": "PSA",
    "Proverbs": "PRO", "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA",
    "Jeremiah": "JER", "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN",
    "Hosea": "HOS", "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
    "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG",
    "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK",
    "John": "JHN", "Acts": "ACT", "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO",
    "Galatians": "GAL", "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL",
    "1 Thessalonians": "1TH", "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI",
    "Titus": "TIT", "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN", "Jude": "JUD", "Revelation": "REV"
}

def parse_reference(ref):
    """Parse a Bible reference into book, chapter, and verses (if present)."""
    # Match patterns like 'Genesis 1', 'Matthew 2:1-12', or 'Psalms 1:1-6'
    pattern = r'^([\w\s]+)\s(\d+)(?::(\d+(?:-\d+)?))?$'
    match = re.match(pattern, ref.strip())
    if not match:
        return None, None, None
    book, chapter, verses = match.groups()
    return book, chapter, verses



def tobool(bool):
    bool_mapping = {
        "true": True,
        "false": False
    }
    real_boolean = bool_mapping.get(bool.strip().lower(), False)
    return real_boolean
def gettoday(tz):
    formatted_date = datetime.now(pytz.timezone(tz)).strftime("%B %d").lstrip("0")
    return(formatted_date)

def getplanday(startdate):
    datetime_now = int(datetime.utcnow().timestamp() * 1000)  # Current time in ms
    # Calculate delta time
    countup = math.floor((datetime_now - startdate) / (1000 * 60 * 60 * 24)+1)

    return countup

def getverses(csvfile,day):
    with open(csvfile, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)  # Read remaining rows
        value = rows[2][day]
        cleaned_text = "\n".join(line for line in value.splitlines() if line.strip())
        return cleaned_text

def convert_verses(verses, site, version, embed):

    lines = verses.splitlines()
    newstring = ""
    for line in lines:
        if site == "YV":
            newstring += convert_to_bible_link_yv(line, version, embed) + "\n"
        elif site == "biblegateway":
            newstring += convert_to_bible_link_bg(line, version, embed) + "\n"
        elif site == "LSB":
            newstring += convert_to_bible_link_lsb(line, embed) + "\n"
        elif site == "ebible":
            newstring += convert_to_bible_link_webus(line) + "\n"
    return newstring

def convert_to_bible_link_yv(reference, version="web", embed=True):
    # Bible version mapping
    bible_versions = {
        "web": 206,
        "esv": 59,
        "lsb": 3345,
    }

    version_number = bible_versions.get(version.lower())
    if not version_number:
        raise ValueError("Invalid Bible version")

    # Extract book name, chapter, and verse(s)
    match = re.match(r'^(\d*)\s*([\w\s]+)\s+(\d+)(?::(\d[-\d]*))?$', reference)
    if not match:
        raise ValueError("Invalid format")

    book_number, book_name, chapter, verses = match.groups()

    special_books = {"Samuel", "Kings", "Chronicles", "Corinthians", "Thessalonians", "Timothy", "Peter", "John"}
    book_name = book_name.strip()
    if book_name in special_books and book_number:
        book_name = f"{book_number} {book_name}"

    book_code = book_abbreviations.get(book_name)
    if not book_code:
        raise ValueError("Book name not recognized")

    # Construct URL
    base_url = f"https://www.bible.com/bible/{version_number}/{book_code}.{chapter}"
    if verses:
        base_url += f".{verses}"

    url = base_url if embed else f"<{base_url}>"

    # Convert to Markdown format
    return f"[{reference}]({url})"

def convert_to_bible_link_lsb(reference, embed=True):
    # the difference between embed and not does not matter for now, but one day it might!:
    if embed:
        return f"[{reference}](https://read.lsbible.org/?q={reference.replace(' ', '+').replace(':', '%3A')})"
    else:
        return f"[{reference}](<https://read.lsbible.org/?q={reference.replace(' ', '+').replace(':', '%3A')}>)"

def convert_to_bible_link_bg(reference, version="web", embed=True):
    if embed:
        return f"[{reference}](https://www.biblegateway.com/passage/?search={reference.replace(' ', '+').replace(':', '%3A')}&version={version})"
    else:
        return f"[{reference}](<https://www.biblegateway.com/passage/?search={reference.replace(' ', '+').replace(':', '%3A')}&version={version}>)"

def convert_to_bible_link_webus(reference, local=False):
    """Generate a Markdown link for a Bible reference."""
    book, chapter, verses = parse_reference(reference)
    if not book or book not in book_abbreviations:
        return f"Invalid reference: {reference}"

    # Get the book abbreviation
    abbr = book_abbreviations[book]
    # Format chapter as two digits
    chapter = int(chapter)
    if local:
        folder = folder
    else :
        folder = "https://ebible.org/engwebu/"
    if abbr == 'PSA':
        filename = f"{folder}{abbr}{chapter:03d}.htm"
    else:
        filename = f"{folder}{abbr}{chapter:02d}.htm"
    # Use the full reference as the link text
    link_text = reference
    return f"[{link_text}]({filename})"

def sendplan(hook):
    # Extract the first hook (modify as needed if there are multiple)
    # hook = config["hooks"][0]
    timezone = hook.get("timezone", 'America/New_York')
    # Webhook details
    WEBHOOK_URL = hook["webhookURL"]
    bot_name = hook["botname"]
    image = hook["image"]
    startdate = hook["startdate"]
    plan_date = gettoday(timezone)
    plan_day = getplanday(int(startdate))
    plan_verses = getverses(hook["csvfile"],plan_day)
    embed = tobool(hook["embed"])
    # Webhook message content
    plan_verses = convert_verses(plan_verses, hook["site"], hook["version"], embed)
    message = {
        "username": bot_name,  # Sets the bot's display name
        "avatar_url": image,  # Sets the bot's profile picture
        "content": f"{plan_date}\n**Day {plan_day}**\n{plan_verses}",  # Message content
    }
    print(message["content"])

    # Extracting host and path from the webhook URL
    host = "discord.com"
    path = WEBHOOK_URL.replace("https://discord.com", "")

    # Making the HTTP request
    conn = http.client.HTTPSConnection(host)
    headers = {"Content-Type": "application/json"}
    conn.request("POST", path, body=json.dumps(message), headers=headers)
    print("Sent!")

    # Getting the response
    response = conn.getresponse()
    print(response.status, response.reason)
    print(response.read().decode())

    # Closing connection
    conn.close()

def testplan(hook):
    timezone = hook.get("timezone", 'America/New_York')
    # Webhook details
    WEBHOOK_URL = hook["webhookURL"]
    bot_name = hook["botname"]
    image = hook["image"]
    startdate = hook["startdate"]
    plan_date = gettoday(timezone)
    plan_day = getplanday(int(startdate))
    plan_verses = getverses(hook["csvfile"],plan_day)
    embed = tobool(hook["embed"])
    # Webhook message content
    plan_verses = convert_verses(plan_verses, hook["site"], hook["version"], embed)
    message = {
        "username": bot_name,  # Sets the bot's display name
        "avatar_url": image,  # Sets the bot's profile picture
        "content": f"{plan_date}\n**Day {plan_day}**\n{plan_verses}",  # Message content
    }
    print(message["content"])


if __name__ == "__main__":
    # print(len(sys.argv))
    n_arguments = len(sys.argv)
    if (n_arguments != 2 and n_arguments != 1):
        print("No arguments = send")
        print("Argument options")
        print(n_arguments)
    else:
        try:
            # Load config from config.json
            with open("config.json", "r") as file:
                config = json.load(file)
            if sys.argv[1] == "send":
                for hook in config["hooks"]:
                    sendplan(hook)
            elif sys.argv[1] == "test":
                print("testing")
                for hook in config["hooks"]:
                    testplan(hook)
            else:
                print("invalid arguments. try test or send")
        except ValueError:
            print("Please provide a valid integer for the line number.")
