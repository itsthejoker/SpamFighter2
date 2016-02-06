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
returned_wiki = collections.namedtuple('Returned_Wiki', ['spam_websites',
                                                         'old_wiki',
                                                         'old_domains'])
subreddits = ["subreddits", "that", "you_have", "moderator", "access_to"]


blogspammr = r.get_redditor('BlogSpammr')


def comment_reader(comment):
    # we subtract 126 characters to get rid of the comment signature
    spam_site = comment_parser.search(comment[:-126])
    return(spam_site.group('spam_url'))



def wiki_reader(wiki):
    domain_list = wiki_parser.search(wiki)
    return(domain_list.group(1))


def sub_logprint(subreddit, message):
    logging.info("{} - {}".format(subreddit, message))





    # retrieve new list from BlogSpammr's history
    logging.info("Getting new list from BlogSpammr's history...")
    for comment in gen:
        if "caution" in comment.body.lower():
            try:
                spam_site = comment_reader(comment.body)
            except AttributeError:
                pass
            if spam_site not in spam_websites:
                spam_websites.append(str(spam_site))
    logging.info("Retrieved new list!")



        sub_logprint(subreddit, "Updating the wiki!")
        r.edit_wiki_page(subreddit, 'config/automoderator', new_wiki)
        sub_logprint(subreddit, "Wiki updated!")
    else:
        sub_logprint(subreddit, "No changes since last time; "
                     "leaving the wiki alone.")


    sub_logprint(subreddit,
                 "Checking existing posts for violations of the domain "
                 "banned list...")
    new_posts = r.get_subreddit(subreddit)
    for submission in new_posts.get_new(limit=100):
            if spamsite in submission.url:
                if not submission.author:
                    author_name = '[deleted]'
                else:
                    author_name = submission.author.name


if __name__ == '__main__':

                        format='[%(asctime)s] - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.info("Starting!")

    while True:
        for sub in subreddits:

        logging.info("Done. Sleeping!")
        sleep(3600)
