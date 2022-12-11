import json
import logging
import math
import os
import requests
import sys
import time
from classes.gameinfo import GameInfo, Asset, Media


class Scraper(object):
    def __init__(self, name = '', baseUrl = '', baseUrlParams = '', apiKey = '', devUser = '', devPassword = '', user = '', password = ''):
        self.name = name
        self.baseUrl = baseUrl
        self.baseUrlParams = baseUrlParams
        self.apiKey = apiKey
        self.devUser = devUser
        self.devPassword = devPassword
        self.user = user
        self.password = password
        self.cacheDir = self.cacheFolder()
        self.platformCacheFile= self.cacheDir + '/' + self.name + '_platforms.cache'
        self.platformCache = self.loadPlatformsCache()
        self.session = None # If we need to handle a HTTP session

    # def __del__(self):
        # self.savePlatformsCache()

    def cacheFolder(self) -> str:
        cacheDir = ''
        if sys.platform == 'win32':
            cacheDir = os.path.expanduser('%LOCALAPPDATA%')
        # Common Linux/MacOS
        else:
            cacheDir = os.path.expanduser('~')
        cacheDir += '/.cache/altscraper'
        if not os.path.exists(cacheDir):
            logging.debug('Creating cache folder ' + cacheDir)
            os.mkdir(cacheDir)
        return cacheDir

    def download(self, endpoint: str, params: dict[str, str] = {}) -> dict:
        """Basic downloading using endpoints and parameters"""
        # First build up the url with trha parameters
        isFirstParam = True
        targetUrl = self.baseUrl + '/' + endpoint
        if self.baseUrlParams:
            targetUrl += '?' + self.baseUrlParams
            isFirstParam = False
        if params:
            for k, v in params.items():
                if isFirstParam:
                    targetUrl += '?{}={}'.format(k, v)
                    isFirstParam = False
                else:
                    targetUrl += '&{}={}'.format(k, v)
        # logging.debug(targetUrl)
        return self.downloadFromUrl(targetUrl)

    def downloadFromUrl(self, targetUrl: str, allow_retry: bool = True) -> dict:
        """Low level downloading using an URL"""
        pause_time = 0
        # try:
        if pause_time == 0:
            if self.session:
                r = self.session.get(targetUrl)
            else:
                r = requests.get(targetUrl)
            # logging.debug(r.headers)
            if 'Retry-After' in r.headers:
                pause_time = float(r.headers["Retry-After"])
            elif 'X-Ratelimit-Retryafter' in r.headers:
                value = r.headers["X-Ratelimit-Retryafter"]
                if value[-2:] == 'ms':
                    pause_time = 1
                else:
                    pause_time = math.ceil(float(value[:-1]))
            if pause_time > 0:
                # pause_time += 1
                logging.warn('The server wants us to go easy on requests. Pausing for %d seconds not to spam the server', pause_time)
                time.sleep(pause_time)
                if allow_retry:
                    logging.info('Retrying the query')
                    return self.downloadFromUrl(targetUrl, False)
            return {'status_code': r.status_code, 'content': r.content}
        # except:
            logging.error("An error ocurred when downloading from an URL")
        return {}

    def downloadToFileFromUrl(self, url: str, destinationFile: str, force_mkdir: bool=False, force_download=False):
        """Download to a file using an URL"""
        logging.debug('Trying to download to "%s"' % destinationFile)
        if os.path.exists(destinationFile) and not force_download:
            logging.info('%s already exists, skipping download', destinationFile)
            return
        data = self.downloadFromUrl(url)
        if not data or data['status_code'] != 200:
            return None
        if force_mkdir:
            dest_path = os.path.dirname(destinationFile)
            if not os.path.exists(dest_path):
                logging.info("%s doesn't exist, creating it", dest_path)
                os.makedirs(dest_path)
        with open(destinationFile,'wb') as f:
            logging.debug("Writing %s", destinationFile)
            f.write(data['content'])
        
    def downloadToFile(self, destinationFile:str, endpoint: str, params: dict = {}) -> bool:
        """Downloads a file to disk
        If you need to retrieve json or xml, don't use that
        """
        logging.debug('Trying to download to "%s"' % destinationFile)
        httpdata = self.download(endpoint, params)
        if not httpdata['status_code'] == 200:
            return False
        # Should go try/catch when writing the file
        with open(destinationFile,'wb') as f:
            f.write(httpdata['content'])
        return True

    def downloadGameAsset(self, media: Media, destination: str, force_mkdir: bool=False, overwrite: bool=False):
        """Download a media asset to disk"""
        logging.info('Downloading media: %s', Asset(media.type).name)
        self.downloadToFileFromUrl(media.url, destination, force_mkdir, overwrite)

    # The following methods MUST be implemented in the child class
    # Gets the complete data for a game and fill the GameInfo object
    def getGameInfo(self, rom, system) -> GameInfo:
        raise NotImplementedError()
    # Get the platforms + their ids from the scraping site. Up to the child
    # to call it, since the user may want to force a refresh from cmdline
    def getPlatforms(self):
        raise NotImplementedError()

    # Need to implement some cache for scrapers regarding known platforms + their id
    def loadPlatformsCache(self):
        logging.debug('Loading platforms cache data from ' + self.platformCacheFile)
        if not os.path.exists(self.platformCacheFile):
            logging.info('No platforms cache available')
            return None
        with open(self.platformCacheFile) as f:
            data = json.load(f)
        return data

    def savePlatformsCache(self):
        logging.debug('Saving platforms cache data to ' + self.platformCacheFile)
        if not self.platformCache:
            return
        with open(self.platformCacheFile, 'w') as f:
            json.dump(self.platformCache, f, indent=4)
