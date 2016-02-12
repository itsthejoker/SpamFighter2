import praw
import OAuth2Util
import re
import collections
import logging
import copy
import urllib2
from time import sleep

__author__ = "https://github.com/itsthejoker"
__version__ = 0.93
__source__ = "https://raw.githubusercontent.com/itsthejoker/SpamFighter2/master/spamfighter2.py"

r = praw.Reddit('Python/Praw:com.itsthejoker.spamfighter:{} (by /u/itsthejoker)'
                .format(__version__))
o = OAuth2Util.OAuth2Util(r)
o.refresh(force=True)

comment_parser = re.compile("""\[\*\*(?P<spam_url>.*)\*\*\]""")
wiki_parser = re.compile("""domain: (\[.*)""")

# must return group 1 on parser1, 2, & 3
# must return group 0 on parser4
# this is because I'm bad at regex
post_parser1 = re.compile("""TheIdiotSpammer: (?P<spamsite>.*)""")
post_parser2 = re.compile("""[\( ]\W(?P<spamsite>.*\.com)[\) ]""")
post_parser3 = re.compile("""\W (?P<spamsite>.*\.com|.*\.org)""")
post_parser4 = re.compile("""^[\w\-]+\.[\w]+\\b""")
post_parser5 = re.compile("""\\b \((?P<asdf>.*)\)\(""")

update_parser = re.compile("""__version__ = (?P<version>[\d\.]+)""")
old_update_parser = re.compile("""itsthejoker\.spamfighter:(?P<version>[\d\.]+)""")

post_parsers = {post_parser1: 1, post_parser2: 1, post_parser3: 1,
                post_parser4: 0, post_parser5: 1}

returned_wiki = collections.namedtuple('Returned_Wiki', ['spam_websites',
                                                         'old_wiki',
                                                         'old_domains'])
subreddits = ["subreddits", "that", "you_have", "moderator", "access_to"]

# list of things to ignore post titles for
title_exceptions = ["SPAM FREE", "I'm doing my job but"]

blogspammr = r.get_redditor('BlogSpammr')


def log_separator():
    logging.info("-"*50)


def log_header(message):
    log_separator()
    logging.info(message)
    log_separator()


def clean(text):
    # removes non-ASCII characters and replaces with spaces
    return ''.join([i if ord(i) < 128 else ' ' for i in text])


def comment_reader(comment):
    # we subtract 126 characters to get rid of the comment signature
    spam_site = comment_parser.search(comment[:-126])
    return(spam_site.group('spam_url'))


def post_reader(post):
    for parser, group_num in post_parsers.iteritems():
        spam_site = parser.search(post)
        if spam_site is not None:
            return(spam_site.group(group_num))
    logging.info("Unable to find url in {}".format(post))


def wiki_reader(wiki):
    domain_list = wiki_parser.search(wiki)
    return(domain_list.group(1))


def sub_logprint(subreddit, message):
    logging.info("{} - {}".format(subreddit, message))


def get_blogspammr_recent():
    spam_websites = []  # start with clear list

    def add_site(parser, thing_to_parse):
        spam_site = None

        try:
            spam_site = parser(thing_to_parse)
        except AttributeError:
            pass

        if spam_site not in spam_websites and spam_site is not None:
            spam_websites.append(str(spam_site))

        return(spam_websites)

    # retrieve new list from BlogSpammr's history
    logging.info("Getting new list from BlogSpammr's history...")
    gen = blogspammr.get_comments(limit=None)  # get last 1000 comments
    submitted_gen = blogspammr.get_submitted(limit=None)  # get last 1000 posts

    for comment in gen:
        if "caution" in comment.body.lower():
            spam_websites = add_site(comment_reader, comment.body)

    for post in submitted_gen:
        if "." in post.title.lower():
            post.title = clean(post.title)
            post.title = post.title.replace('reddit.com', '')

            excepted = False

            for post_exception in title_exceptions:
                if post_exception in post.title:
                    excepted = True

            if not excepted:
                spam_websites = add_site(post_reader, post.title)
            else:
                logging.debug('Skipping post "{}" for being on the exception'
                              ' list.'.format(post.title))

    logging.info("Retrieved new list!")
    return(spam_websites)


def update_wiki(new_BS_list, subreddit):

    new_spam_list = []  # clear the spamlist

    logging.info("Getting wiki page from r/{}...".format(subreddit))
    wiki = r.get_wiki_page(subreddit, "config/automoderator")
    wiki_domain_list = wiki_reader(wiki.content_md)

    # strip the [] from the ends and turn it into a usable list
    wiki_domain_list = str(wiki_domain_list).translate(None, '[]').rstrip()
    current_spam_websites = wiki_domain_list.split(", ")
    new_spam_list = copy.copy(current_spam_websites)

    for site in new_BS_list:
        if site not in current_spam_websites:
            new_spam_list.append(site)

    new_wiki = re.sub(wiki_parser, "domain: "+str(new_spam_list)
                      .translate(None, "'"), wiki.content_md)

    if new_spam_list != current_spam_websites:
        sub_logprint(subreddit, "Updating the wiki!")
        r.edit_wiki_page(subreddit, 'config/automoderator', new_wiki)
        sub_logprint(subreddit, "Wiki updated!")
    else:
        sub_logprint(subreddit, "No changes since last time; "
                     "leaving the wiki alone.")

    return new_spam_list


def moderate_posts(new_spam_list, subreddit):
    sub_logprint(subreddit,
                 "Checking existing posts for violations of the domain "
                 "banned list...")
    new_posts = r.get_subreddit(subreddit)
    for submission in new_posts.get_new(limit=100):
        for spamsite in new_spam_list:
            if spamsite in submission.url:
                if not submission.author:
                    author_name = '[deleted]'
                else:
                    author_name = submission.author.name
                sub_logprint(subreddit, "Found one! Pretending to nuke"
                             " submission '{}' by {}".format(submission.title,
                                                             author_name))
                # sub_logprint(subreddit, "Found one! Nuking submission '{}' by {}"
                             # .format(submission.title, author_name))
                # submission.remove()


def check_for_updates():
    # check for updates
    logging.info("Checking for updates...")

    try:
        spamfighter2_source = urllib2.urlopen(__source__).read()
        print spamfighter2_source
    except urllib2.HTTPError:
        logging.info("There appears to be an issue contacting Github. Skipping"
                     " the update check.")
        log_separator()
        return None

    github_version = update_parser.search(spamfighter2_source)
    if github_version is None:
        github_version = old_update_parser.search(spamfighter2_source)

    if float(github_version.group('version')) > float(__version__):
        logging.info("There's a newer version available! You should head over "
                     "to {} and get the newest version!".format(__source__))
    else:
        logging.info("We're up to date!")
        log_separator()


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='spamfighter2.log')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] - %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    log_header("Starting!")

    while True:

        check_for_updates()

        try:
            spam_websites = get_blogspammr_recent()
            for sub in subreddits:
                new_spam_list = update_wiki(spam_websites, sub)
                moderate_posts(new_spam_list, sub)

        except praw.errors.HTTPException:
            logging.info("EXCEPTION: PRAW threw a HTTP error; waiting 5 "
                         "minutes and trying again.")
            sleep(300)

        else:
            logging.info("Done. Sleeping!")
            sleep(3600)
