import re

URL_NAMES = []


def load_url_pattern_names(patterns, include_with_args=True):
    """Retrieve a list of urlpattern names"""
    global URL_NAMES
    for pat in patterns:
        if pat.__class__.__name__ == 'RegexURLResolver':            # load patterns from this RegexURLResolver
            load_url_pattern_names(pat.url_patterns, include_with_args)
        elif pat.__class__.__name__ == 'RegexURLPattern':           # load name from this RegexURLPattern
            if pat.name is not None and pat.name not in URL_NAMES:
                if include_with_args or re.compile(pat.regex).groups == 0:
                    URL_NAMES.append(pat.name)
    return URL_NAMES
