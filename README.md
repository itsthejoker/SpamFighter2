# SpamFighter2
An Automoderator Updater for Banned Domains, Powered by /u/BlogSpammr
---

Over the last few weeks, Reddit has been inundated with severe amounts of spam from many different sources. One user, /u/BlogSpammr, has done a wonderful job of identifying these sources and making everyone aware. What this script does is effectively follow /u/BlogSpammr around and scrape the URLs out their comments.

All your Automoderator config needs to have is one of these inside the config:

    domain: []
    action: remove
    comment: "Ha ha, silly spammers! Your post has been removed!"

Right now the script can only have one "domain" section inside the config, so this won't work with a domain whitelist active as well. This is probably a good thing, since I actually can't come up with a reason why you would run a whitelist and a blacklist at the same time.

Obviously, the account running this script will need to be a moderator for the subreddits that you're attempting to modify. You'll also need to create an application through Reddit and get an Application ID and Secret for OAuth2Util.

## Requirements
* [PRAW](https://praw.readthedocs.org/en/stable/) - 3.3.0; installable by `pip install praw` 
* [PRAW-OAuth2Util](https://github.com/SmBe19/praw-OAuth2Util) - 0.3.4; installable by `pip install praw-oauth2util`

PRAW-OAuth2Util will require an "oauth.ini" file, but [you can find more information on that here](https://github.com/SmBe19/praw-OAuth2Util/blob/master/OAuth2Util/README.md).
