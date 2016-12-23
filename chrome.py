import os
import subprocess
import re
import atexit
import time

from selenium import webdriver

'''
requires the selenium python package
requires docker be installed and available on system path
'''


def _start_selenium_container(check_exists=True):
    if check_exists:
        try:
            _get_selenium_container()
            print 'selenium container found; will not start another one'
            return
        except Exception:
            print 'selenium container not found; will have to start one'
    retvalue = os.system('docker run -d -P selenium/standalone-chrome')
    if retvalue != 0:
        raise Exception('could not successfully initialize selenium container')
    else:
        time.sleep(10)  # give it some time to warm up; hard coded horror


def _get_selenium_container():
    docker_ps = subprocess.check_output('docker ps', shell=True)
    docker_containers = docker_ps.splitlines()[1:]
    selenium_containers = [
        container for container in docker_containers if
        'selenium/standalone-chrome' in container]
    print len(selenium_containers), 'selenium server(s) found'
    if len(selenium_containers) == 0:
        raise Exception('no selenium server found')
    elif len(selenium_containers) > 1:
        print 'picking the last one'
    return selenium_containers[-1]


def _get_selenium_container_port_number():
    selenium_container = _get_selenium_container()
    port_regex = '0[.]0[.]0[.]0:([0-9]*)->4444'
    port_numbers = re.findall(port_regex, selenium_container)
    assert len(port_numbers) == 1, 'selenium container port format unexpected'
    return port_numbers[0]


def _get_selenium_container_name():
    selenium_container = _get_selenium_container()
    error = 'selenium container name format unexpected'
    assert '4444/tcp' in selenium_container.split()[-2], error
    return selenium_container.split()[-1]


def _destroy_selenium_container():
    try:
        selenium_container_name = _get_selenium_container_name()
        print 'found selenium container to destroy'
    except Exception:
        print 'could not find selenium container to destroy'
        return
    os.system('docker kill ' + selenium_container_name)
    os.system('docker rm ' + selenium_container_name)


def get_selenium_driver():
    _start_selenium_container()
    port_number = _get_selenium_container_port_number()
    remote = 'http://localhost:' + port_number + '/wd/hub'
    driver = webdriver.Remote(
        remote, webdriver.DesiredCapabilities.CHROME.copy())
    if 'atexit_registered_destroy_selenium_container' not in globals():
        globals()['atexit_registered_destroy_selenium_container'] = True
        atexit.register(_destroy_selenium_container)
    return driver
