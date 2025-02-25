import html
import json
import logging
from scrapers.scraper import Scraper
from classes.gameinfo import GameInfo, Asset, Media, Regions


# This list uses the absolute same index as Asset(). It helps setting the
# SS media type to the corresponding asset. When a value is a list, it's to set
# a prefered order for the possible SS media type that fit for the corresponding Asset()
SSMedia = ['ss', 'video', 'box-texture', 'box-3D', 'box-2D' , 'box-2D-side', 'box-2D-back', ['wheel', 'wheel-hd', 'screenmarquee', 'screenmarquee-hd'], 'sstitle', ['wheel-carbon', 'wheel-steel']]


class ScreenScraper(Scraper):
    def __init__(self, devUser = '', devPassword = '', user = '', password = ''):
        urlParams = 'softname=GroovyScrape&output=json'
        if devUser and devPassword:
            urlParams += '&devid={}&devpassword={}'.format(devUser, devPassword)
        if user and password:
            urlParams += '&ssid={}&sspassword={}'.format(user, password)
        super(ScreenScraper, self).__init__(name='ScreenScraper', devUser=devUser
                , devPassword=devPassword, user=user
                , password=password
                , baseUrl = 'https://www.screenscraper.fr/api2'
                , baseUrlParams = urlParams)

    def getPlatforms(self):
        self.platformCache = json.loads(self.download('systemesListe.php')['content'])
        self.savePlatformsCache()

    def queryGameInfo(self, rom, system = None):
        jsData = dict()
        req_trad = {'crc': rom.crc, 'md5': rom.md5, 'romnom': rom.romfile}
        if not system in ['mame', 'arcade', 'mame-libretro', 'mame4all', 'fba']:
            for req_type, req_value in req_trad.items():
                ret = self.download('jeuInfos.php', {req_type: req_value})
                logging.debug('%s: URL returned status code %s using %s', rom.romfile, str(ret['status_code']), req_type)
                if ret['status_code'] == 200:
                    jsData = json.loads(ret['content'])
                    break
        else:
            # Force system id to 75 (MAME/arcade)
            ret = self.download('jeuInfos.php', {'systemid': '75', 'romnom': rom.romfile})
            logging.debug('%s: URL returned status code %s for system %s', rom.romfile, str(ret['status_code']), system)
            if ret['status_code'] == 200:
                jsData = json.loads(ret['content'])
        return jsData

    # jsData is a list which length is the number of possible categories
    # then each category is a dict with keys lange and text
    def categoryDataToDict(self, jsData, dataType = 'langue'):
        categories = dict()
        for g in jsData:
            for c in g['noms']:
                if categories and c[dataType] in categories:
                    categories[c[dataType]].append(c['text'])
                else:
                    categories[c[dataType]] = [c['text']]
        return categories

    # jsData is a list made of dicts that have 2 keys: region and text
    def regiontextListToDict(self, jsData, dataType='region'):
        return {x[dataType]: html.unescape(x['text']) for x in jsData}

    def regionmediaToDict(self, jsData):
        medias = []
        for m in jsData:
            if m['type'] not in SSMedia:
                # Some SSmedia elements can be a list
                mediaIsInList = False
                for ssm in SSMedia:
                    if not isinstance(ssm, list):
                        continue
                    if m['type'] in ssm:
                        mediaIsInList = True
                        break
                if not mediaIsInList:
                    continue
            if 'region' not in m and m['type'] != 'video':
                logging.debug('Media has no region')
                logging.debug(m)
                continue
            elif 'region' in m and m['region'] not in Regions:
                logging.debug('Unknown media region: %s', m['region'])
                continue
            mediaData = Media()
            if m['type'] in SSMedia:
                mediaData.type = SSMedia.index(m['type'])
            else:
                for ssm in SSMedia:
                    if not isinstance(ssm, list):
                        continue
                    if m['type'] in ssm:
                        mediaData.type = SSMedia.index(ssm)
                        break
            mediaData.hashes['crc32'] = m['crc'] if m['crc'] else None
            mediaData.hashes['md5'] = m['md5'] if m['md5'] else None
            mediaData.hashes['sha1'] = m['sha1'] if m['sha1'] else None
            mediaData.url = m['url']
            mediaData.scraperMediaType = m['type']
            mediaData.extension = m['format']
            if 'region' in m:
                mediaData.region = m['region']
            # logging.debug(mediaData)
            medias.append(mediaData)
        return medias

    def filterMultipleMedias(self, medias):
        filteredMedias = dict()
        for m in medias:
            mediaIndex = Asset(m.type).value
            # logging.debug(mediaIndex)
            if not isinstance(SSMedia[mediaIndex], list):
                filteredMedias[mediaIndex] = m
                # logging.debug(m.scraperMediaType)
                continue
            for ssm in SSMedia[mediaIndex]:
                if mediaIndex not in filteredMedias:
                    filteredMedias[mediaIndex] = m
                else:
                    # Here is the real filtering deal
                    # logging.debug(SSMedia[mediaIndex].index(m.scraperMediaType))
                    if SSMedia[mediaIndex].index(m.scraperMediaType) < SSMedia[mediaIndex].index(filteredMedias[mediaIndex].scraperMediaType):
                        filteredMedias[mediaIndex] = m
        return list(filteredMedias.values())

    def getGameInfo(self, rom, system = None) -> GameInfo | None:
        # Now Let's reorganize this
        logging.info("Getting rom information...")
        jsData = self.queryGameInfo(rom, system)
        if not (jsData and jsData['response'] and jsData['response']['jeu']):
            logging.warning('Got no data for rom')
            return None
        gameData = jsData['response']['jeu']
        myGameInfo = GameInfo()
        if 'editeur' in gameData:
            myGameInfo.publisher = gameData['editeur']['text']
        if 'noms' in gameData:
            myGameInfo.title = self.regiontextListToDict(gameData['noms'])
        if 'dates' in gameData:
            myGameInfo.date = self.regiontextListToDict(gameData['dates'])
        if 'genres' in gameData:
            myGameInfo.category = self.categoryDataToDict(gameData['genres'])
        if 'synopsis' in gameData:
            myGameInfo.description = self.regiontextListToDict(gameData['synopsis'], 'langue')
        if 'joueurs' in gameData:
            myGameInfo.players = gameData['joueurs']['text']
        if 'rotation' in gameData:
            myGameInfo.rotation = gameData['rotation']
        if 'medias' in gameData:
            # ssMedia = self.regionmediaToDict(gameData['medias'])
            myGameInfo.medias = self.regionmediaToDict(gameData['medias'])
        # logging.debug(str(myGameInfo))
        myGameInfo.medias = self.filterMultipleMedias(myGameInfo.medias)
        return myGameInfo
