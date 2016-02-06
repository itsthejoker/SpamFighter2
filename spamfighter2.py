import praw
import OAuth2Util
import re
import collections
import logging
import copy
from time import sleep

r = praw.Reddit('Python/Praw:com.itsthejoker.spamfighter:0.9 (by /u/itsthejoker)')
o = OAuth2Util.OAuth2Util(r)
o.refresh(force=True)

comment_parser = re.compile("""\[\*\*(?P<spam_url>.*)\*\*\]""")
wiki_parser = re.compile("""domain: (\[.*)""")

# must return group 1 on parser1 and parser2
# this is because I'm bad at regex
post_parser1 = re.compile("""[\( ]\W(?P<spamsite>.*\.com)[\) ]""")
post_parser2 = re.compile("""\W (?P<spamsite>.*\.com|.*\.org)""")
post_parser3 = re.compile("""^[\w\-]+\.com""")

returned_wiki = collections.namedtuple('Returned_Wiki', ['spam_websites',
                                                         'old_wiki',
                                                         'old_domains'])
subreddits = ["subreddits", "that", "you_have", "moderator", "access_to"]

blogspammr = r.get_redditor('BlogSpammr')


def clean(text):
    # removes non-ASCII characters and replaces with spaces
    return ''.join([i if ord(i) < 128 else ' ' for i in text])


def comment_reader(comment):
    # we subtract 126 characters to get rid of the comment signature
    spam_site = comment_parser.search(comment[:-126])
    return(spam_site.group('spam_url'))


def post_reader(post):

    spam_site = post_parser1.search(post)

    if spam_site is None:
        logging.info("Parser1 failed on {}".format(post))
        spam_site = post_parser2.search(post)

        if spam_site is None:
            logging.info("Parser2 failed on {}".format(post))
            spam_site = post_parser3.search(post)

            if spam_site is None:
                logging.info("All parsers failed on {}".format(post))
        else:
            return(spam_site.group(1))
    else:
        return(spam_site.group(1))

    return(spam_site.group(0))


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
        if ".com" in post.title.lower():
            post.title = clean(post.title)

            if "reddit.com" in post.title:
                post.title = post.title.replace('reddit.com', '')

            spam_websites = add_site(post_reader, post.title)

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
            #submission.remove()


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

    logging.info("-"*50)
    logging.info("Starting!")
    logging.info("-"*50)

    while True:
        spam_websites = get_blogspammr_recent()
        for sub in subreddits:
            new_spam_list = update_wiki(spam_websites, sub)
            moderate_posts(new_spam_list, sub)

        logging.info("Done. Sleeping!")
        sleep(3600)
