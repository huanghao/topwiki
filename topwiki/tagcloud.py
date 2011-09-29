import sys

styles = [
    ('smallest_tag', '{ font-size:xx-small; color:#666666; }'),
    ('small_tag',    '{ font-size:small;    color:#cc9999; }'),
    ('medium_tag',   '{ font-size:medium;   color:#cccccc; }'),
    ('large_tag',    '{ font-size:large;    color:#ff6666; }'),
    ('largest_tag',  '{ font-size:xx-large; color:#ff6600; }'),
]

def main():
    tags = {}
    for line in sys.stdin:
        try:
            priority, tag, href = line.strip().split('|', 2)
        except ValueError:
            continue
        weight = float(priority)
        tags.setdefault(href, [tag, 0])
        tags[href][1] += weight

    tags = [ (weight, tag, href) for href, (tag, weight) in tags.items() ]
    ws = map(lambda x:x[0], tags)
    bins = get_bins(min(ws), max(ws), len(styles))
    write_cloud(tags, bins)


def get_bins(_min, _max, n):
    step = (_max-_min)/float(n)
    return [ _min+step*i for i in range(1, n+1) ]


def write_styles():
    print '''<style>
%s
body    { background-color: #333333; }
a       { text-decoration: none; }
a:hover { color: green; }
span    { margin: 4px; }
</style>
''' % '\n'.join([ '.%s a %s' % (cls,css) for cls,css in styles ])


def index(w, bins):
    for i, low in enumerate(bins):
        if w <= low:
            return i
    return i

def write_cloud(tags, bins):
    write_styles()
    for weight, tag, href in tags:
        idx = index(weight, bins)
        cls = styles[idx][0]
        print '<span class="%s"><a href="%s" title="%d" target="_blank">%s</a></span>' % (cls, href, weight, tag)


if __name__ == "__main__":
    main()
