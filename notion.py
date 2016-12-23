import chrome
import urlparse
import time


'''
requires chrome.py be in the same directory as this module
chrome.py can be found at http://github.com/shariq/notion-on-firebase
'''


def get_driver():
    if 'chrome_selenium_driver' in globals():
        return globals()['chrome_selenium_driver']
    else:
        driver = chrome.get_selenium_driver()
        globals()['chrome_selenium_driver'] = driver
        return driver


def is_notion_page(url):
    cleaned_url = urlparse.urljoin('https://www.notion.so', url)
    parsed = urlparse.urlparse(cleaned_url)
    if 'notion.so' in parsed.netloc and parsed.path.count('/') == 1:
        potential_page_id = parsed.path.split('-')[-1].split('/')[-1]
        hexadecimal = '0123456789abcdef'
        length_correct = len(potential_page_id) == 32
        charset_correct = set(potential_page_id) <= set(hexadecimal)
        return length_correct and charset_correct
    else:
        return False


def normalize_url_from_notion(url):
    # this method should only be used from hrefs on a notion page!
    cleaned_url = urlparse.urljoin('https://www.notion.so', url)
    if is_notion_page(cleaned_url):
        parsed = urlparse.urlparse(cleaned_url)
        potential_page_id = parsed.path.split('-')[-1]
        return 'https://www.notion.so/' + potential_page_id
    else:
        return cleaned_url


def set_element_attribute(element, attribute, value):
    script = 'arguments[0].setAttribute(arguments[1], arguments[2])'
    get_driver().execute_script(script, element, attribute, value)


def normalize_href_element(element, attribute='href'):
    url = element.get_property(attribute)
    normalized = normalize_url_from_notion(url)
    set_element_attribute(element, attribute, normalized)
    return normalized


def add_focus_handler(element):
    onmouseover = "this.classList.add('focused');"
    onmouseout = "this.classList.remove('focused');"
    onmouseout += "this.classList.remove('activated');"
    onmousedown = "this.classList.add('activated');"
    set_element_attribute(element, 'onmouseover', onmouseover)
    set_element_attribute(element, 'onmouseout', onmouseout)
    set_element_attribute(element, 'onmousedown', onmousedown)


def delete_element(element):
    get_driver().execute_script(
        'arguments[0].parentNode.removeChild(arguments[0])', element)


def insert_analytics():
    # yeah this is really selfish of me...
    driver = get_driver()
    script = '''
var head = document.getElementsByTagName('head')[0];
var script = document.createElement('script');
script.type = 'text/javascript';
script.src = 'ga.js';
head.appendChild(script);
'''
    driver.execute_script(script)


def remove_manifest():
    driver = get_driver()
    script = '''
document.getElementsByTagName('html')[0].removeAttribute('manifest');
'''
    driver.execute_script(script)


def scrape_notion_page(page_id):
    driver = get_driver()
    driver.get('https://www.notion.so/' + page_id)
    time.sleep(5)
    # should change this to instead use expected_conditions or webdriverwait
    # but it's so messy to wait on react rendering...

    assert 'Docs, wikis, tasks, seamlessly in one.' not in driver.title
    # this is how we know the page is either invalid or we're not authenticated
    # there is probably a better way but HTTP status codes don't work...
    # fails anyways later on even if this assert doesn't trigger an error

    print 'page title:', driver.title

    login_element = driver.find_element_by_xpath('//a[@href="/login"]')
    script_elements = driver.find_elements_by_xpath('//script')

    for element in [login_element] + script_elements:
        delete_element(element)

    notion_pages_encountered = []

    href_elements = driver.find_elements_by_xpath('//*[@href]')  # e.g, <a>
    src_elements = driver.find_elements_by_xpath('//*[@src]')  # e.g, <img>
    for element in href_elements:
        url = normalize_href_element(element)
        if is_notion_page(url):
            notion_pages_encountered.append(url.split('/')[-1].split('-')[-1])
    for element in src_elements:
        normalize_href_element(element, 'src')

    focus_elements = driver.find_elements_by_xpath(
        '//div[contains(@class, "darkenOnActive")]')
    for element in focus_elements:
        add_focus_handler(element)

    insert_analytics()
    remove_manifest()

    time.sleep(1)
    html = driver.page_source

    # ugh it would be really nice if there was a better way to return
    # multiple things from a function... dictionaries are not much better
    return html, notion_pages_encountered
