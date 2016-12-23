# notion-on-firebase

This project will scrape a `notion.so` page and its links, rewrite your `firebase.json` file with custom links, then deploy all that as static content to Firebase hosting.


Live example:
- Static content on Firebase hosting - `https://shar.iq/scrapbook`
- Source content on Notion - `https://www.notion.so/d065149ff38a4e7a9b908aeb262b0f4f`


## Goal

Super nice personal website builder

Super nice means: WYSIWYG editor, beautiful without any work, trivial to restructure


## Story

I liked using `notion.so` a lot, and wanted to have my person website / blog hosted on it. At first I just used an iframe. It was awesome: a beautiful WYSIWYG website builder that lets you focus on the content. Also you start treating your personal website like a scrapbook instead of a curated representation of you: it made me want to publish unpolished ideas. And I could trivially change the structure of the website (number of pages and how they link to each other).

But there were two things I really didn't like about using an iframe: individual pages in my scrapbook did not have custom URLs, and Google could not index any of the content on my website. Horrid.

Then I found out that putting Notion pages in iframes would soon be deprecated for some security reason: and decided to build this project. 

This project is a script you can run to turn your Notion page (and pages it links to, recursively) into static content which gets deployed on Firebase (with custom short links).


## Setup

Install Docker for your OS: https://docs.docker.com/engine/getstarted/step_one

Set up a Firebase hosting project: https://firebase.google.com/docs/hosting/quickstart

Install selenium from pip: `pip install selenium`

Install pickledb from pip: `pip install pickledb`


The entry point for running the code is `run.py`.

Example usage: `python run.py d065149ff38a4e7a9b908aeb262b0f4f ../firebase`

`d065149ff38a4e7a9b908aeb262b0f4f` would be the Notion page ID which the spider will start off from.

`../firebase` is the directory in which you set up your Firebase hosting project.


## Code breakdown

### `chrome.py`

A headless browser is needed to scrape Notion because it relies significantly on React to render the page.

This module cleanly gets a Selenium webdriver handle.

Breakdown:
- Pulls the `selenium/standalone-chrome` Docker image
- Runs that image
- Connects to the container with a remote Selenium webdriver
- Takes care of clean up with `atexit` (`docker kill` and `docker rm`)


### `notion.py`

This module scrapes and cleans up a single Notion page. 

Breakdown:
- Loads the URL and waits for some seconds
- Throws an exception if the page requires authentication or has no content
- Fixes resource links, deletes scripts, and removes manifest
- Adds mouse handlers to bring back pretty animations on clickable divs
- Keeps track of all other Notion pages linked from this page
- Inserts script element for analytics
- Returns the source for a page, and page IDs linked from that page


### `spider.py`

This module scrapes a Notion page and all other Notion pages linked from that page, recursively. Breadth first. It also takes care of replacing `https://www.notion.so/<page_id>` URLs with custom short links.

Breakdown:
- Breadth first search, starting at specified root page
- Skips over any pages which throw an exception
- Pages are all stored in memory while the spider is running
- Exposes `dump_results` to dump the spidering results to disk
- Exposes `postprocess` to go through pages on disk and replace Notion links with custom short links
- Asks user for custom short link to use for each page, then stores those using `pickledb`
- Exposes `generate_rewrites` which will be used later to modify the rewrite routes in `firebase.json`


### `run.py`

This module does everything together so you can just run it to update Firebase hosting with the newest version of your Notion.

Breakdown:
- Runs a spider
- Dumps the results to a Firebase public folder
- Overwrites `firebase.json` with updated routes
- Runs `firebase deploy`


## Love

to Simon for helping me out <3
