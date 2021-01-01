from requests.exceptions import HTTPError


class ResponseObj:
    _DEFAULT_HEADER = {"Content-Type": "text/plain"}

    def __init__(self, content, headers=_DEFAULT_HEADER, status_code=200):
        self._content = content
        self.headers = headers
        self.status_code = status_code

    def text(self):
        return str(self._content)

    def json(self):
        return self._content

    def raise_for_status(self):
        raise HTTPError(str(self.status_code))


class MockServer:
    BASE_URL = "http://nova.astrometry.net"

    def __init__(self, get=None, post=None, base_url=None):
        self.get_map = get if get else {}
        self.post_map = post if post else {}

        if base_url is not None:
            self.BASE_URL = base_url

    def dispatch(self, mapper, path):
        try:
            path = path[len(self.BASE_URL) :]
        except Exception:
            # Likely a different base path was specified
            return self.not_found

        print(f"Matching: {path}")
        # Order keys which match the path based on length
        matches = sorted(
            [key for key in mapper.keys() if path.startswith(key)], key=len
        )
        print(f"Matches: {matches}")

        # If there are matching dispatch functions, use the longest
        #  (so most specific) match.
        if matches:
            return mapper[matches[-1]]
        return self.not_found

    def dispatch_post(self, path):
        return self.dispatch(self.post_map, path)

    def dispatch_get(self, path):
        return self.dispatch(self.get_map, path)

    # Methods used to patch requests.get/post
    def get(self, url, *args, **kwargs):
        handler = self.dispatch_get(url)
        return handler(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        handler = self.dispatch_post(url)
        return handler(url, *args, **kwargs)

    def not_found(self, *args, **kwargs):
        return ResponseObj({"status": "notfound"}, status_code=404)
