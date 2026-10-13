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
from urllib.parse import urlencode

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

# OSIS book identifiers used by .lxbp plans, mapped to the names used by link converters.
osis_book_names = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth",
    "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Kings", "2Kgs": "2 Kings",
    "1Chr": "1 Chronicles", "2Chr": "2 Chronicles", "Ezra": "Ezra", "Neh": "Nehemiah",
    "Esth": "Esther", "Job": "Job", "Ps": "Psalms", "Prov": "Proverbs",
    "Eccl": "Ecclesiastes", "Song": "Song of Solomon", "Isa": "Isaiah",
    "Jer": "Jeremiah", "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah",
    "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk",
    "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi",
    "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John",
    "Acts": "Acts", "Rom": "Romans", "1Cor": "1 Corinthians", "2Cor": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
    "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians", "1Tim": "1 Timothy",
    "2Tim": "2 Timothy", "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pet": "1 Peter", "2Pet": "2 Peter", "1John": "1 John",
    "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation"
}

def osis_to_reference(passage):
    """Convert OSIS references such as Matt.5.3-Matt.5.10 to readable Bible references."""
    def endpoint(value):
        parts = value.split(".")
        if len(parts) not in (2, 3) or parts[0] not in osis_book_names:
            raise ValueError(f"Invalid .lxbp passage reference: {value}")
        if not parts[1].isdigit() or (len(parts) == 3 and not parts[2].isdigit()):
            raise ValueError(f"Invalid .lxbp passage reference: {value}")
        return osis_book_names[parts[0]], int(parts[1]), int(parts[2]) if len(parts) == 3 else None

    ends = passage.split("-")
    if len(ends) not in (1, 2):
        raise ValueError(f"Invalid .lxbp passage reference: {passage}")
    start = endpoint(ends[0])
    start_text = f"{start[0]} {start[1]}" if start[2] is None else f"{start[0]} {start[1]}:{start[2]}"
    if len(ends) == 1:
        return start_text
    end = endpoint(ends[1])
    end_text = f"{end[0]} {end[1]}" if end[2] is None else f"{end[0]} {end[1]}:{end[2]}"
    if start[0] == end[0] and start[1] == end[1] and start[2] is not None and end[2] is not None:
        return f"{start[0]} {start[1]}:{start[2]}-{end[2]}"
    return f"{start_text}-{end_text}"


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

def getverses(planfile, day):
    """Read one day's passages from a .lxbp JSON plan or the legacy CSV."""
    if planfile.lower().endswith(".lxbp"):
        with open(planfile, "r", encoding="utf-8") as file:
            plan = json.load(file)
        days = plan.get("days")
        if not isinstance(days, list) or not 1 <= day <= len(days):
            raise ValueError(f"Plan day {day} is outside the .lxbp plan")
        passages = days[day - 1].get("passages", [])
        if not isinstance(passages, list):
            raise ValueError(f"Day {day} has an invalid passages list")
        # Empty passages are valid Review & Reflect days.
        return "\n".join(osis_to_reference(passage) for passage in passages)

    # Backwards compatibility for existing CSV plans.
    with open(planfile, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)
        value = rows[2][day]
        return "\n".join(line for line in value.splitlines() if line.strip())


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
        elif site.lower() == "yoshiost":
            newstring += convert_to_bible_link_yoshiost(line, version) + "\n"
        elif site.lower() == "lux":
            newstring += convert_to_bible_link_lux(line) + "\n"
        else:
            raise ValueError(f"Unsupported Bible site: {site}")
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


# Yoshiost BSB book IDs and URL slugs.
yoshiost_books = {
    "Genesis": (1, "genesis"), "Exodus": (2, "exodus"), "Leviticus": (3, "leviticus"),
    "Numbers": (4, "numbers"), "Deuteronomy": (5, "deuteronomy"), "Joshua": (6, "joshua"),
    "Judges": (7, "judges"), "Ruth": (8, "ruth"), "1 Samuel": (9, "1_samuel"),
    "2 Samuel": (10, "2_samuel"), "1 Kings": (11, "1_kings"), "2 Kings": (12, "2_kings"),
    "1 Chronicles": (13, "1_chronicles"), "2 Chronicles": (14, "2_chronicles"),
    "Ezra": (15, "ezra"), "Nehemiah": (16, "nehemiah"), "Esther": (17, "esther"),
    "Job": (18, "job"), "Psalms": (19, "psalm"), "Psalm": (19, "psalm"),
    "Proverbs": (20, "proverbs"), "Ecclesiastes": (21, "ecclesiastes"),
    "Song of Solomon": (22, "song_of_solomon"), "Isaiah": (23, "isaiah"),
    "Jeremiah": (24, "jeremiah"), "Lamentations": (25, "lamentations"),
    "Ezekiel": (26, "ezekiel"), "Daniel": (27, "daniel"), "Hosea": (28, "hosea"),
    "Joel": (29, "joel"), "Amos": (30, "amos"), "Obadiah": (31, "obadiah"),
    "Jonah": (32, "jonah"), "Micah": (33, "micah"), "Nahum": (34, "nahum"),
    "Habakkuk": (35, "habakkuk"), "Zephaniah": (36, "zephaniah"), "Haggai": (37, "haggai"),
    "Zechariah": (38, "zechariah"), "Malachi": (39, "malachi"), "Matthew": (40, "matthew"),
    "Mark": (41, "mark"), "Luke": (42, "luke"), "John": (43, "john"), "Acts": (44, "acts"),
    "Romans": (45, "romans"), "1 Corinthians": (46, "1_corinthians"),
    "2 Corinthians": (47, "2_corinthians"), "Galatians": (48, "galatians"),
    "Ephesians": (49, "ephesians"), "Philippians": (50, "philippians"),
    "Colossians": (51, "colossians"), "1 Thessalonians": (52, "1_thessalonians"),
    "2 Thessalonians": (53, "2_thessalonians"), "1 Timothy": (54, "1_timothy"),
    "2 Timothy": (55, "2_timothy"), "Titus": (56, "titus"), "Philemon": (57, "philemon"),
    "Hebrews": (58, "hebrews"), "James": (59, "james"), "1 Peter": (60, "1_peter"),
    "2 Peter": (61, "2_peter"), "1 John": (62, "1_john"), "2 John": (63, "2_john"),
    "3 John": (64, "3_john"), "Jude": (65, "jude"), "Revelation": (66, "revelation"),
}

def convert_to_bible_link_lux(reference):
    """Build a LUX Bible passage link using OSIS book identifiers."""
    # Accept references such as Genesis 1, Genesis 1:1, and
    # Numbers 1:1-1:2 or Genesis 1:1-Exodus 2:3.
    reverse_osis = {name: code for code, name in osis_book_names.items()}
    # Prefer the standard OSIS name for Psalms.
    reverse_osis["Psalm"] = "Ps"

    def endpoint(text):
        match = re.fullmatch(r"(.+?)\s+(\d+)(?::(\d+))?", text.strip())
        if not match:
            raise ValueError(f"Unsupported LUX reference endpoint: {text}")
        book, chapter, verse = match.groups()
        book = book.strip()
        if book not in reverse_osis:
            raise ValueError(f"Unknown Bible book for LUX: {book}")
        osis = f"{reverse_osis[book]}.{int(chapter)}"
        if verse is not None:
            osis += f".{int(verse)}"
        return osis

    parts = reference.strip().split("-")
    if len(parts) == 1:
        osis_ref = endpoint(parts[0])
    elif len(parts) == 2:
        # Compact same-chapter ranges like "Numbers 1:1-2" need their
        # second endpoint expanded; full endpoints are also supported.
        first = endpoint(parts[0])
        second_text = parts[1].strip()
        if re.fullmatch(r"\d+", second_text):
            if first.count(".") != 2:
                raise ValueError(f"A verse range needs a starting verse: {reference}")
            second = first.rsplit(".", 1)[0] + "." + second_text
        elif re.fullmatch(r"\d+:\d+", second_text):
            book_chapter = first.rsplit(".", 1)[0] if first.count(".") == 2 else first
            second = book_chapter + "." + second_text.split(":", 1)[1]
        else:
            second = endpoint(second_text)
        osis_ref = f"{first}-{second}"
    else:
        raise ValueError(f"Invalid LUX reference range: {reference}")

    url = f"https://app.luxbible.app/passage/{osis_ref}"
    return f"[{reference}]({url})"


def convert_to_bible_link_yoshiost(reference, version="BSB"):
    """Build a Yoshiost BSB link for a chapter, verse, or same-chapter verse range."""
    if str(version).upper() != "BSB":
        raise ValueError(f"Unsupported Yoshiost version: {version}")
    match = re.fullmatch(r"(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?", reference.strip())
    if not match:
        raise ValueError(f"Unsupported Yoshiost reference: {reference}")
    book, chapter, verse_from, verse_to = match.groups()
    book = book.strip()
    if book not in yoshiost_books:
        raise ValueError(f"Unknown Bible book for Yoshiost: {book}")
    book_id, slug = yoshiost_books[book]
    url = f"https://bsb.yoshiost.com/chapters/bsb_bk{book_id:02d}_{slug}_{int(chapter)}"
    if verse_from is None:
        url += ".html"
    else:
        if verse_to is None:
            verse_to = verse_from
        if int(verse_from) > int(verse_to):
            raise ValueError(f"Invalid verse range: {reference}")
        url += "?" + urlencode({"verseFrom": verse_from, "verseTo": verse_to})
    return f"[{reference}]({url})"


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
    planfile = hook.get("lxbpfile", hook.get("planfile", hook.get("csvfile")))
    if not planfile:
        raise KeyError("Configure lxbpfile (or legacy csvfile) in config.json")
    plan_verses = getverses(planfile, plan_day)
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
    planfile = hook.get("lxbpfile", hook.get("planfile", hook.get("csvfile")))
    if not planfile:
        raise KeyError("Configure lxbpfile (or legacy csvfile) in config.json")
    plan_verses = getverses(planfile, plan_day)
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
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
