import notion
import traceback
import os
import pickledb
import sys
import json


'''
requires notion.py be in the same directory as this module
notion.py can be found at http://github.com/shariq/notion-on-firebase
'''


def notion_spider(root_page, meta_json={}):
    # page in this function means a notion page identifier
    # like b9b2d96c8e844556be0740771db875a3

    # eventually this should check the last updated timestamp and
    # request pages which are out of date...

    spider_results = {}
    to_scrape = [root_page]  # should be a deque, but ew dependencies
    while len(to_scrape):
        page = to_scrape.pop(0)
        # shifting everything in memory over by one... so what lol
        if page in spider_results:
            continue
        print 'now scraping', page
        try:
            html, new_pages = notion.scrape_notion_page(page, meta_json=meta_json)
        except Exception:
            print 'encountered error while scraping', page
            traceback.print_exc()
            print 'skipping', page, 'for now'
            continue
        spider_results[page] = html
        # dumping to disk is nice for resuming after crash
        for new_page in new_pages:
            if new_page not in spider_results and new_page not in to_scrape:
                to_scrape.append(new_page)
    return spider_results


def dump_results(results, results_path='./results'):
    for page, html in results.items():
        path = os.path.join(results_path, page + '.html')
        with open(path, 'w') as handle:
            handle.write(html.encode('utf8'))


def postprocess(results_path='./results', rewrite_db_path='rewrite.db'):
    pages = [
        page.replace('.html', '') for page in os.listdir(results_path)
        if '.html' in page and len(page) == 32+5]
    paths = [os.path.join(results_path, page + '.html') for page in pages]
    htmls = [open(path).read() for path in paths]
    rewrite_db = pickledb.load(rewrite_db_path, True)
    for page, html in zip(pages, htmls):
        if rewrite_db.get(page) == None:
            print 'What should the short form of', page, 'be?'
            title_index = html.index('<title>')
            print '[only alphanumeric characters please]'
            print html[title_index:title_index+150]
            short_url = str(raw_input(''))
            rewrite_db.set(page, short_url)
    for path, page, html in zip(paths, pages, htmls):
        print 'postprocessing', path, '...'
        processed_html = html[:].decode('utf8')
        for page in pages:
            short_url = rewrite_db.get(page)
            processed_html = processed_html.replace(
                'https://www.notion.so/' + page, '/' + short_url)
        with open(path, 'w') as handle:
            handle.write(processed_html.encode('utf8'))


def generate_rewrites(results_path='./results', rewrite_db_path='rewrite.db'):
    rewrites = []
    pages = [
        page.replace('.html', '') for page in os.listdir(results_path)
        if '.html' in page and len(page) == 32+5]
    rewrite_db = pickledb.load(rewrite_db_path, True)
    for page in pages:
        rewrite = {}
        rewrite['source'] = '/' + rewrite_db.get(page)
        rewrite['destination'] = '/' + page + '.html'
        rewrites.append(rewrite)
    return rewrites


def run(root_page, results_path='./results', meta_json={}):
    results = notion_spider(root_page, meta_json=meta_json)
    dump_results(results, results_path)
    postprocess(results_path)
    rewrites = generate_rewrites(results_path)
    print json.dumps(rewrites)
    return rewrites


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'This script dumps spider results to the results directory.'
        print 'usage: python spider.py <root_page>'
        print 'e.g, python spider.py d065149ff38a4e7a9b908aeb262b0f4f'
        sys.exit(-1)
    root_page = sys.argv[-1]
    run(root_page)
