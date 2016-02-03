import praw
import OAuth2Util
import re
import collections
import logging
from time import sleep

r = praw.Reddit('Python/Praw:com.itsthejoker.spamfighter:0.6 (by /u/itsthejoker)')
o = OAuth2Util.OAuth2Util(r)
o.refresh(force=True)

comment_parser = re.compile("""\[\*\*(?P<spam_url>.*)\*\*\]""")
wiki_parser = re.compile("""domain: (\[.*)""")
returned_wiki = collections.namedtuple('Returned_Wiki', ['spam_websites',
                                                         'old_wiki',
                                                         'old_domains'])
master_sub = "subreddit_name"  # sub to pull existing config from, like "funny"
# subreddits to duplicate updated automod config to
subreddits = ["subreddits", "that", "you_have", "moderator", "access_to"]

spam_websites = []

blogspammr = r.get_redditor('BlogSpammr')
gen = blogspammr.get_comments(limit=None)


def comment_reader(comment):
    # we subtract 126 characters to get rid of the comment signature
    spam_site = comment_parser.search(comment[:-126])
    return(spam_site.group('spam_url'))


def wiki_reader(wiki):
    domain_list = wiki_parser.search(wiki)
    return(domain_list.group(1))


def sub_logprint(subreddit, message):
    logging.info("{} - {}".format(subreddit, message))


def retrieve_wiki():
    logging.info("Getting wiki page from master, {}...".format(master_sub))
    wiki = r.get_wiki_page(master_sub, "config/automoderator")
    wiki_domain_list = wiki_reader(wiki.content_md)

    # strip the [] from the ends
    wiki_domain_list = str(wiki_domain_list).translate(None, '[]').rstrip()
    spam_websites = wiki_domain_list.split(", ")

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
    p = returned_wiki(spam_websites, old_wiki=wiki,
                      old_domains=wiki_domain_list)
    return(p)


def update_wiki(old_wiki_info, subreddit):
    new_wiki = re.sub(wiki_parser, "domain: "+str(old_wiki_info.spam_websites)
                      .translate(None, "'"), old_wiki_info.old_wiki.content_md)

    if old_wiki_info.old_domains != old_wiki_info.spam_websites:
        sub_logprint(subreddit, "Updating the wiki!")
        r.edit_wiki_page(subreddit, 'config/automoderator', new_wiki)
        sub_logprint(subreddit, "Wiki updated!")
    else:
        sub_logprint(subreddit, "No changes since last time; "
                     "leaving the wiki alone.")


def moderate_posts(subreddit):
    sub_logprint(subreddit,
                 "Checking existing posts for violations of the domain "
                 "banned list...")
    new_posts = r.get_subreddit(subreddit)
    for submission in new_posts.get_new(limit=100):
        for spamsite in spam_websites:
            if spamsite in submission.url:
                if not submission.author:
                    author_name = '[deleted]'
                else:
                    author_name = submission.author.name
                sub_logprint(subreddit, "Found one! Nuking submission '{}' by {}"
                             .format(submission.title, author_name))
            submission.remove()


if __name__ == '__main__':

    logging.basicConfig(filename='spamfighter2.log',
                        level=logging.INFO,
                        format='[%(asctime)s] - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filemode='w')
    # logging information for writing to console
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)-8s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.info("Starting!")

    while True:
        new_information = retrieve_wiki()
        for sub in subreddits:
            update_wiki(new_information, sub)
            moderate_posts(sub)

        logging.info("Done. Sleeping!")
        sleep(3600)
