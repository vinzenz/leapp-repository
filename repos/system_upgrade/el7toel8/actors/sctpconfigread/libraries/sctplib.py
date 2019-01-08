#
# Generic functions
#
def anyfile(files):
    from os.path import isfile
    for f in files:
        try:
            if isfile(f):
                return True
        except OSError:
            continue
    return False

