import upnpclient
from xml.dom.minidom import parseString
import yaml

from difflib import SequenceMatcher
from operator import itemgetter

class MinidlnaQueryHelper:
    upnpdev = None
    config = None
    def __init__(self):
        self.config = yaml.safe_load(open('./config.yml'))
        for i in range(1,4):
            try:
                self.upnpdev = upnpclient.Device(self.config['root_xml_url'])
                break
            except Exception as err:
                print(err.__doc__)
                print('{}'.format(err))
                print('failed to connect to dlna on try #'+str(i))
        if (self.upnpdev==None):
            print('couldn\'t connect to dlna, check config file')

            raise Exception('couldn\'t connect to dlna, check config file')

    def __get_object_children(self, ObjectID):
        ret = {}
        directo = parseString(self.upnpdev.ContentDirectory.Browse(ObjectID=str(ObjectID),BrowseFlag='BrowseDirectChildren',Filter='*',StartingIndex='0',RequestedCount='999',SortCriteria='+dc:title')['Result'])
        for c in directo.documentElement.childNodes[1:]:
            title = c.childNodes[0].childNodes[0].data
            id = c.attributes._attrs['id'].childNodes[0].data
            ret[title] = id
        return ret
    
    def __get_object_url(self, ObjectID):
        ret = {}
        directo = parseString(self.upnpdev.ContentDirectory.Browse(ObjectID=str(ObjectID),BrowseFlag='BrowseDirectChildren',Filter='*',StartingIndex='0',RequestedCount='999',SortCriteria='+dc:title')['Result'])
        for c in directo.documentElement.childNodes[1:]:
            title = c.childNodes[0].childNodes[0].data
            url = None
            for i in c.childNodes:
                if i.nodeName == 'res':
                    url = i.childNodes[0].data
            ret[title] = url
        return ret

    def __string_similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def query_artist_title(self, artist, title):
        music_id = self.__get_object_children(0)['Music']
        artist_id = self.__get_object_children(music_id)['Artist']
        artists = self.__get_object_children(artist_id)
        if len(artists)<=0:
            return -1, '', '', ''
        similarities = [self.__string_similarity(artist.lower(), k.lower()) for k in artists.keys()]
        idx_max, simil_max = max(enumerate(similarities), key=itemgetter(1))
        if simil_max<=self.config['similarity_threshold']:
            return -2, '', '', ''
        matched_artist = list(artists.keys())[idx_max]
        artist_id = artists[matched_artist]
        titlelist_id = self.__get_object_children(artist_id)['- All Albums -']
        titles = self.__get_object_url(titlelist_id)
        if len(titles)<=0:
            return -3, '', '', ''
        similarities = [self.__string_similarity(title.lower(), t.lower()) for t in titles.keys()]
        idx_max, simil_max = max(enumerate(similarities), key=itemgetter(1))
        if simil_max<=self.config['similarity_threshold']:
            return -4, '', '', ''
        matched_title = list(titles.keys())[idx_max]
        title_url = titles[matched_title]
        url_parts = title_url.split('/')
        port = url_parts[2].split(':')[1]
        url_parts[2] = self.config['substitute_domain']+ ':' + port
        title_url = '/'.join(url_parts)
        return 0, matched_title, matched_artist, title_url

