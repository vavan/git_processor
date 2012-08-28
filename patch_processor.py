import re, os, datetime



class Change:
    def __init__(self, date, commit, subj):
        self.date = date
        self.commit = commit
        self.subj = subj
        self.oldname = ''

class File:
    def __init__(self, name):
        self.name = name
        self.changes = []
    def add(self, change):
        self.changes.append(change)
    def sort(self):
        self.changes.sort( key = lambda x: x.date )

class BaseParser:
    def parse(self, commit, date, subj, part):
        date = datetime.datetime.strptime(date[:-6], '%Y-%m-%d %H:%M:%S')
        items = []
        raw_items = self.item_re.findall(part)
        for i in raw_items:
            c = Change(date, commit, subj)
            name, c.oldname = self.parse_name(i)
            items.append( (name, c) )
        return items

class ParserDeleteed(BaseParser):
    def __init__(self):
        self.item_re = re.compile(' delete mode \d+ (.*?)$', re.M)

    def parse_name(self, raw):
        return (raw, 'DELETED')

class ParserRenamed(BaseParser):
    def __init__(self):
        self.item_re = re.compile(' rename (.*?) \(\d+%\)$', re.M)

    def parse_name(self, raw):
        if raw.find('{') == -1:
            old = new = ''
            mid = raw
        else:
            old, mid_new = raw.split('{')
            mid, new = mid_new.split('}')
        old_mid, skip, new_mid = mid.partition(' => ')
        return (old + old_mid + new, old + new_mid + new)

class Parser:
    def __init__(self, files, parser):
        self.change_re = re.compile(r'(\w+) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (?:-|\+)\d{4})(.*)', re.M)
        self.parser = parser
        self.files = files

    def parse(self, data, prefix):
        raw_items = self.change_re.split(data)
        raw_items = raw_items[1:]
        for i in xrange(0, len(raw_items), 4):
            items = self.parser.parse(*raw_items[i:i+4])
            for name, change in items:
                name = prefix + '/' + name
                change.oldname = prefix + '/' + change.oldname

                if name not in self.files:
                    self.files[name] = File(name)
                self.files[name].add( change )


def parse():
    files = {}
    p = Parser(files, ParserDeleteed())
    for i in ('base.deleted', 'av.deleted', 'native.deleted'):
        data = file(i).read()
        p.parse(data, i.split('.')[0])
    p = Parser(files, ParserRenamed())
    for i in ('base.renamed', 'av.renamed', 'native.renamed'):
        data = file(i).read()
        p.parse(data, i.split('.')[0])
    for i in files.itervalues():
        i.sort()
    return files


def out(files):
    z = 0
    for name, afile in files.iteritems():
        print "Name: %s"%name
        for i in afile.changes:
            print "\t%s %s"%(i.date, i.oldname)
        #if z > 10:
        #    break
        z += 1



def main():
    files = parse()
    out(files)

main()