import logging, yaml, upnpclient
from xml.dom.minidom import parseString

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
        directo = parseString(self.upnpdev.ContentDirectory.Browse(ObjectID=str(ObjectID),BrowseFlag='BrowseDirectChildren',Filter='*',StartingIndex='0',RequestedCount='0',SortCriteria='+dc:title')['Result'])
        for c in directo.documentElement.childNodes[1:]:
            title = c.childNodes[0].childNodes[0].data
            id = c.attributes._attrs['id'].childNodes[0].data
            ret[title] = id
        return ret
    
    def __get_object_url(self, ObjectID, sort_criteria='+dc:title'):
        ret = {}
        directo = parseString(self.upnpdev.ContentDirectory.Browse(ObjectID=str(ObjectID),BrowseFlag='BrowseDirectChildren',Filter='*',StartingIndex='0',RequestedCount='0',SortCriteria=sort_criteria)['Result'])
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
        logging.info('best matching artist is: ' + str(list(artists.keys())[idx_max]))       
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
        return 0, matched_title, matched_artist, title_url

    def query_artist_album(self, artist, album):
        music_id = self.__get_object_children(0)['Music']
        artist_id = self.__get_object_children(music_id)['Artist']
        artists = self.__get_object_children(artist_id)
        if len(artists)<=0:
            return -1, '', '', ''
        similarities = [self.__string_similarity(artist.lower(), k.lower()) for k in artists.keys()]
        idx_max, simil_max = max(enumerate(similarities), key=itemgetter(1))
        logging.info('best matching artist is: ' + str(list(artists.keys())[idx_max]))
        if simil_max<=self.config['similarity_threshold']:
            return -2, '', '', ''
        matched_artist = list(artists.keys())[idx_max]
        artist_id = artists[matched_artist]
        albums = self.__get_object_children(artist_id)
        if len(albums)<=0:
            return -3, '', '', ''
        similarities = [self.__string_similarity(album.lower(), k.lower()) for k in albums.keys()]
        idx_max, simil_max = max(enumerate(similarities), key=itemgetter(1))
        logging.info('best matching album is: ' + str(list(albums.keys())[idx_max]))
        if simil_max<=self.config['similarity_threshold']:
            return -4, '', '', ''
        matched_album = list(albums.keys())[idx_max]
        album_id = albums[matched_album]
        titles = self.__get_object_url(album_id, sort_criteria='+upnp:class,+upnp:originalTrackNumber,+dc:title') # '+pv:numberOfThisDisc not supported, still works as intended for me?
        return 0, matched_album, matched_artist, titles.values()