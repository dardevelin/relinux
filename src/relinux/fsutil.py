'''
General filesystem utilities
@author: MiJyn
'''

import os
import stat
import shutil
import fnmatch
import sys
import hashlib
from relinux import configutils


# Reads the link location of a file or returns None
def delink(file):
    if os.path.islink(file):
        return os.readlink(file)
    return None


# Lengthener for files to exclude
def exclude(names, files):
    excludes = []
    for i in files:
        excludes.extend(fnmatch.filter(names, i))
    return excludes


# Returns the size of the file or directory
def getSize(path):
    dlink = delink(path)
    addme = 0
    if dlink is not None:
        return getSize(dlink)
    elif os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        addme = os.path.getsize(path)
        for i in os.listdir(path):
            addme = addme + getSize(i)
        return addme
    return None


# Size translator
# size = Dictionary:
#         T = Terabytes
#         G = Gigabytes
#         M = Megabytes
#         K = Kilobytes
#         B = Bytes
# htom = Human to Machine (i.e. 4KB to 4096B). If not true, it accepts these values:
#         T = Bytes-to-Terabytes
#         etc...
def sizeTrans(size, htom=True):
    KB = 1024
    MB = 1048576
    GB = 1073741824
    TB = 1099511627776
    addme = 0
    if size["T"] > 0:
        addme = addme + size["T"] * TB
    if size["G"] > 0:
        addme = addme + size["G"] * GB
    if size["M"] > 0:
        addme = addme + size["M"] * MB
    if size["K"] > 0:
        addme = addme + size["K"] * KB
    if size["B"] > 0:
        addme = addme + size["B"]
    if htom is True:
        return addme
    else:
        if htom == "T":
            return addme / TB
        if htom == "G":
            return addme / GB
        if htom == "M":
            return addme / MB
        if htom == "K":
            return addme / KB
        if htom == "B":
            return addme


# Makes a directory
def makedir(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)


# Makes a directory tree
def maketree(arr):
    for i in arr:
        makedir(i)


# Simple implementation of the touch utility
def touch(file):
    if os.path.exists(file):
        os.utime(file, None)
    else:
        open(file, "w").close()


# Same as maketree, but for files instead
def makefiles(arr):
    for i in arr:
        touch(i)


# Removes a file
# If followlink is True, then it will remove both the link and the origin
def rm(file, followlink=False):
    rfile = file
    dfile = delink(file)
    if dfile is not None:
        file = dfile
    if os.path.isfile(file):
        os.remove(rfile)
        if followlink is True and dfile is not None:
            os.remove(file)
    elif os.path.isdir(file):
        shutil.rmtree(rfile)
        if followlink is True and dfile is not None:
            os.remove(file)


# Removes a list of files
def rmfiles(arr):
    for i in arr:
        rm(i)


# Helper function for chmod
def _chmod(c, mi):
    returnme = 0x00
    rbit = 0
    wbit = 0
    ebit = 0
    # TODO: Make this code cleaner
    #    Something like this:
    #    rbit = stat.S_IREAD
    #    ...
    #    if c == 0:
    #    ...
    #    if c == 2:
    #        rbit = rbit | SOME_SORT_OF_BIT_FLAG
    #        ...
    if c == 0:
        # These are not read/write/exec bits, but they work the same way
        ebit = stat.S_ISVTX
        wbit = stat.S_ISGID
        rbit = stat.S_ISUID
    elif c == 1:
        rbit = stat.S_IREAD
        wbit = stat.S_IWRITE
        ebit = stat.S_IEXEC
    elif c == 2:
        rbit = stat.S_IRGRP
        wbit = stat.S_IWGRP
        ebit = stat.S_IXGRP
    elif c == 3:
        rbit = stat.S_IROTH
        wbit = stat.S_IWOTH
        ebit = stat.S_IXOTH
    # Read
    if mi >= 4:
        returnme = rbit
        mi = mi - 4
    # Write
    if mi >= 2:
        returnme = returnme | wbit
        mi = mi - 2
    # Execute
    if mi >= 1:
        returnme = returnme | ebit
    return returnme


# Simple implementation of the chmod utility
def chmod(file, mod):
    val = 0x00
    c = 0
    # In case the user of this function used UGO instead of SUGO, we'll cover up for that
    if len(mod) < 4:
        c = 1
    # OR all of the chmod options
    for i in mod:
        # OR this option to val
        val = val | _chmod(c, int(i))
        c = c + 1
    # Chmod it
    os.chmod(file, val)


# List the files in a directory
# Current options:
#    recurse (True or False): If True, recurse into the directory
#    dirs (True or False): If True, show directories too
#    symlinks (True or False): If True, show symlinks too
def listdir(dirs, options):
    listed = os.listdir(dirs)
    returnme = []
    returnme.append(dirs)
    for i in listed:
        if options.symlinks is True and os.path.islink(i):
            returnme.append(i)
        if options.dirs is True and os.path.isdir(i):
            if options.recurse is True:
                returnme.extend(listdir(i, options))
            else:
                returnme.append(i)
        if os.path.isfile(i):
            returnme.append(i)
    return returnme


# Filesystem copier (like rsync --exclude... -a SRC DST)
def fscopy(src, dst, excludes1):
    # Get a list of all files
    files = os.listdir(src)
    # Exclude the files that are not wanted
    excludes = []
    if len(excludes) > 0:
        excludes = shutil.ignore_patterns(files, excludes1)
    makedir(dst)
    # Copy the files
    for file in files:
        # Make sure we don't copy files that are supposed to be excluded
        if file in excludes:
            continue
        fullpath = os.path.join(src, file)
        newpath = os.path.join(dst, file)
        dfile = delink(fullpath)
        if dfile is not None:
            os.symlink(dfile, newpath)
        elif os.path.isdir(fullpath):
            fscopy(fullpath, newpath, excludes)
        else:
            shutil.copy2(fullpath, newpath)
    shutil.copystat(src, dst)


# Removes the contents of a directory with excludes and options
# Current options:
#     excludes (True or False): If True, exclude the files listed in excludes
#     remdirs (True or False): If True, remove directories too
def adrm(dirs, options, excludes1):
    # Get a list of all files inside the directory
    files = os.listdir(dirs)
    excludes = []
    # Exclude the files listed to exclude
    if options.excludes is True:
        excludes = shutil.ignore_patterns(files, excludes1)
    # Remove the wanted files
    for file in files:
        # Make sure we don't remove files that are listed to exclude from removal
        if file in excludes:
            continue
        fullpath = os.path.join(dirs, file)
        dfile = delink(fullpath)
        if dfile is not None:
            if os.path.isfile(dfile):
                rm(fullpath)
                continue
        elif os.path.isdir(fullpath):
            adrm(fullpath, options, excludes1)
        else:
            rm(fullpath)
    if options.remdirs is True:
        rm(dirs)


# Returns the stat of a file
def getStat(file):
    return os.stat(file)


# Returns the mode of the stat of a file (can be used like this: getMode(getStat(file))
def getMode(stat):
    return stat.S_IMODE(stat.st_mode)


# Specific implementation of shutil's copystat function
def copystat(stat, dst):
    if hasattr(os, "utime"):
        os.utime(dst, (stat.st_atime, stat.st_mtime))
    if hasattr(os, "chmod"):
        os.chmod(dst, getMode(stat))
    if hasattr(os, "chflags") and hasattr(stat, "st_flags"):
        os.chflags(dst, stat.st_flags)


# Interactive file editor - Get all buffers needed
# 0 = stat
# 1 = filename
# 2 = write buffer
# 3 = file contents
def ife_getbuffers(file):
    returnme = []
    returnme[0] = getStat(file)
    returnme[1] = file
    fbuff = open(file, "r")
    rbuff = configutils.getBuffer(fbuff)
    fbuff.close()
    fbuff = open(file, "w")
    returnme[2] = fbuff
    returnme[3] = rbuff
    return returnme


# Interactive file editor
# Function must return an array:
#     0 = Write line? True or False
#     1 = Line to write (which, of course, will not be written if 0 = False), String
def ife(buffers, func):
    for i in buffers[3]:
        r = func(i)
        if r[0] is True:
            buffers[2].write(r[1])
    copystat(buffers[0], buffers[1])
    buffers[2].close()


# Finds the system architecture
def getArch():
    bits_64 = sys.maxsize > 2 ** 32
    if bits_64 is True:
        return "amd64"
    else:
        return "i386"


# Returns the installed size of a compressed filesystem (SquashFS)
def getSFSInstSize(file):
    # Not optimal, but it works
    # Sample line:
    #     drwxr-xr-x root/root               377 2012-04-25 10:04 squashfs-root
    #                                        ^^^
    #                                        That part is the size
    patt = "^ *[dlspcb-][rwx-][rwx-][rwx-][rwx-][rwx-][rwx-][rwx-][rwx-][rwx-] *[A-Za-z0-9]*/[A-Za-z0-9]* *([0-9]*).*"
    output = os.popen("unsquashfs -lls " + file)
    totsize = 0
    for line in output:
        m = patt.match(line)
        if configutils.checkMatched(m):
            totsize = totsize + int(m.group(1))
    return totsize


# Generate an MD5 checksum from a file
def genMD5(file, blocksize=65536):
    buffer = file.read(blocksize)
    m = hashlib.md5()
    while len(buffer) > 0:
        m.update(buffer)
        buffer = file.read(blocksize)
    return m.digest()


# Generate an MD5 checksum that can be read by the md5sum command from a file
def genFinalMD5(file):
    string = genMD5(file) + "  " + file + "\n"
    return string
