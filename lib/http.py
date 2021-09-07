def iri_to_uri(iri):
    from urllib.parse import quote, urlsplit, urlunsplit
    parts = urlsplit(iri)
    return urlunsplit((
        parts.scheme,
        parts.netloc.encode('idna').decode('ascii'),
        quote(parts.path),
        quote(parts.query, '='),
        quote(parts.fragment),
    ))
