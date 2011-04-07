
def unescape(html, coding='utf8'):
    def trans(m):
        if m.group(2):
            u = unichr(int(m.group(2)[1:]))
        elif m.group(3):
            u = unichr(htmlentitydefs.name2codepoint[m.group(3)])
        return u.encode(coding) if coding else u
    return re.sub(r'&((#\d+)|(\w+));', trans, html)
