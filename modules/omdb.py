import logging, requests
from modules import util
from modules.util import Failed
from retrying import retry

logger = logging.getLogger("Plex Meta Manager")

class OMDbObj:
    def __init__(self, imdb_id, data):
        self._imdb_id = imdb_id
        self._data = data
        if data["Response"] == "False":
            raise Failed(f"OMDb Error: {data['Error']} IMDb ID: {imdb_id}")
        self.title = data["Title"]
        try:
            self.year = int(data["Year"])
        except (ValueError, TypeError):
            self.year = None
        self.content_rating = data["Rated"]
        self.genres = util.get_list(data["Genre"])
        self.genres_str = data["Genre"]
        try:
            self.imdb_rating = float(data["imdbRating"])
        except (ValueError, TypeError):
            self.imdb_rating = None
        try:
            self.imdb_votes = int(str(data["imdbVotes"]).replace(',', ''))
        except (ValueError, TypeError):
            self.imdb_votes = None
        try:
            self.metacritic_rating = int(data["Metascore"])
        except (ValueError, TypeError):
            self.metacritic_rating = None
        self.imdb_id = data["imdbID"]
        self.type = data["Type"]

class OMDb:
    def __init__(self, params, Cache=None):
        self.url = "http://www.omdbapi.com/"
        self.apikey = params["apikey"]
        self.limit = False
        self.Cache = Cache
        self.get_omdb("tt0080684")

    @retry(stop_max_attempt_number=6, wait_fixed=10000, retry_on_exception=util.retry_if_not_failed)
    def get_omdb(self, imdb_id):
        expired = None
        if self.Cache:
            omdb_dict, expired = self.Cache.query_omdb(imdb_id)
            if omdb_dict and expired is False:
                return OMDbObj(imdb_id, omdb_dict)
        response = requests.get(self.url, params={"i": imdb_id, "apikey": self.apikey})
        if response.status_code < 400:
            omdb = OMDbObj(imdb_id, response.json())
            if self.Cache:
                self.Cache.update_omdb(expired, omdb)
            return omdb
        else:
            error = response.json()['Error']
            if error == "Request limit reached!":
                self.limit = True
            raise Failed(f"OMDb Error: {error}")
