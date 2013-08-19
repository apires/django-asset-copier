from StringIO import StringIO
import os
from tempfile import TemporaryFile
from django.conf import settings
from django.contrib.staticfiles.finders import get_finders
from django.core.files.storage import get_storage_class, FileSystemStorage
import tarfile
import sys


class FileSystemStorageExporter():
    def __init__(self, ptr):
        self.ptr = ptr

    def walk(self, path):
        file_list = []

        def _walk(self, path):
            try:
                subs, files = self.ptr.listdir(path)
                for directory in subs:
                    _walk(self, "%s/%s" % (path, directory))
                for f in files:
                    file_list.append(self.ptr.path("%s/%s" % (path, f)))
            except OSError as e:
                print e
        _walk(self, path)
        return file_list

    def gen_tarball(self, name_and_path=None):
        if name_and_path is None:
            name_and_path = TemporaryFile()
            out = tarfile.open(fileobj=name_and_path, mode="w")
        else:
            out = tarfile.open(name_and_path, "w")
        for f in self.walk("."):
            relative_name = f.split(self.ptr.base_location)[1]
            out.add(f, relative_name)
        out.close()
        return name_and_path


def dump_database(name='default'):
    db_info = settings.DATABASES[name]

    if db_info['ENGINE'] == 'django.db.backends.sqlite3':
        shell = os.popen2('echo ".dump" | sqlite3 %s' % db_info['NAME'])
        db_dump = StringIO(shell[1].read())

    elif db_info['ENGINE'] == "django.db.backends.mysql":
        db = db_info['OPTIONS'].get('db', db_info['NAME'])
        user = db_info['OPTIONS'].get('user', db_info['USER'])
        passwd = db_info['OPTIONS'].get('passwd', db_info['PASSWORD'])
        host = db_info['OPTIONS'].get('host', db_info['HOST'])
        port = db_info['OPTIONS'].get('port', db_info['PORT'])

        if host and port:
            shell = os.popen2('mysqldump %s --user=%s --password=%s --host=%s --port=%s' % (db, user, passwd, host, port))
        else:
            shell = os.popen2('mysqldump %s --user=%s --password=%s' % (db, user, passwd))
        db_dump = StringIO(shell[1].read())
    else:
        db_dump = "ERROR DUMPING DB"
    return db_dump


def grab_static_files():

    f = TemporaryFile()
    tar = tarfile.open(fileobj=f, mode="w")

    found_files = set()
    for finder in get_finders():
        for path, storage in finder.list(['CVS', '.*', '*~']):
            if getattr(storage, 'prefix', None):
                prefixed_path = os.path.join(storage.prefix, path)
            else:
                prefixed_path = path

            if prefixed_path not in found_files:
                found_files.add(prefixed_path)
                tar.add(storage.path(path), prefixed_path)
    tar.close()

    return f


if __name__ == "__main__":

    outfile = sys.argv[1]

    # get Storage files
    storage_class = get_storage_class()
    ptr = storage_class()

    exporter = {
        FileSystemStorage: FileSystemStorageExporter
    }.get(storage_class)

    x = exporter(ptr)
    storage_files = x.gen_tarball()

    # get STATIC files
    static_files = grab_static_files()  # key = prefixed path, value = path

    # get DB
    db_dump = dump_database()

    out = tarfile.open("%s.tbz2" % outfile, "w:bz2")

    storage_info = tarfile.TarInfo(name="storage_files.tar")
    storage_info.size = storage_files.tell()
    storage_files.seek(0)
    out.addfile(storage_info, storage_files)
    
    static_info = tarfile.TarInfo(name="static_files.tar")
    static_info.size = static_files.tell()
    static_files.seek(0)
    out.addfile(static_info, static_files)

    db_dump_info = tarfile.TarInfo()
    db_dump_info.size = db_dump.len
    db_dump_info.name = "dbdump.sql"

    out.addfile(db_dump_info, db_dump)
    out.close()