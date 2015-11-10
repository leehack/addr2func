#!/usr/bin/python -E
# This script is used to resolve backtraces dumped from libc_debug.so
# by Freepine<freepine@gmail.com>

import getopt
import sys
import os
import string

def PrintUsage():
    print
    print "  usage: " + sys.argv[0] + " [options] <memory-diff> "
    print
    print "  --root-dir=path"
    print "       the path to android source code root directory"
    print
    print "  --maps-file=file"
    print "       the maps file of the process, which is used to find the corresponding libraries of the address"
    print
    print "  --product=product-name"
    print "       the target product, which is used to find related output dir"
    print
    sys.exit(1)

class AddressConverter:
    'A class to convert an given address to the corresponding function and file no.'
    maps=[]
    symbols_dir=''
    prebuilt_dir=''
    debug=0
    def __init__(self, mapfilename, rootdir, product, debug=0):
        self.__readmaps(mapfilename)
        self.symbols_dir = rootdir + '/out/target/product/' + product + '/symbols/'
        self.prebuilt_dir = rootdir + '/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.8/bin/'
        self.debug = debug

    def __readmaps(self, mapfilename):
        fileobj = open(mapfilename, 'r')
        contents = fileobj.readlines()
        fileobj.close()
        for line in contents:
            mapitem = self.__parseoneline(line)
            self.maps.append(mapitem)

    def __parseoneline(self, aLine):
        startAddress = int(aLine[0:8], 16)
        if(startAddress <= 0x00010000):
            startAddress = 0
        endAddress = int(aLine[9:17], 16)
        libraryName = (aLine[aLine.find('/'):]).strip()
        return [startAddress, endAddress, libraryName]

    def __findlib(self, address):
        i=0
        while i<len(self.maps) and self.maps[i][0] <= address:
            if self.maps[i][1] >= address:
                return self.maps[i][2], address-self.maps[i][0]
            i = i+1
        return 'Unknown', 0

    def getfunction(self, address):
        libname, offset = self.__findlib(address)
        if self.debug == 1:
            if libname == '/system/lib/libc.so':
                libname = '/system/lib/libc_debug.so'

        if libname != 'Unknown' and os.path.isfile(self.symbols_dir + libname):
            cmd = self.prebuilt_dir + "arm-linux-androideabi-addr2line -f -e " \
                  + self.symbols_dir + libname + " 0x" + `'%x' % offset`
            stream = os.popen(cmd)
            lines = stream.readlines()
            stream.close()
            if lines != []:
                cmd = self.prebuilt_dir + "arm-linux-androideabi-c++filt " + lines[0]
                stream = os.popen(cmd)
                lines[0] = stream.readline()
                stream.close()
                return lines[0].strip(), lines[1].strip()
        else:
            return self.symbols_dir + libname, '<Unknown>'

if __name__ == '__main__':
    rootdir = '.'
    product = 'generic'
    mapsfile = None
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "", ["root-dir=", "maps-file=", "product=", "help"])
    except getopt.GetoptError, error:
        PrintUsage()

    for option, value in options:
        if option == "--help":
            PrintUsage()
        if option == "--root-dir":
            rootdir = value
        if option == "--product":
            product = value
        if option == "--maps-file":
            mapsfile = value

    if mapsfile == None or len(arguments) == 0:
        PrintUsage()

    libc_debug_exist = 0
    if(os.path.isfile(rootdir + '/out/target/product/' + product + '/symbols/system/bin/libc_debug.so')):
        print "Code base: Eclair, replacing libc with libc_debug..."
        libc_debug_exist = 1
    my_converter = AddressConverter(mapsfile, rootdir, product, libc_debug_exist)
    diffobj = open(arguments[0], 'r')
    allocations = diffobj.readlines()
    diffobj.close()

    for onealloc in allocations:
        if onealloc.startswith('< size ') or onealloc.startswith('> size '):
            backtraces = map(string.strip, onealloc[27:].split(','))
            print onealloc[0:27]
            for address in backtraces:
                function, lineinfile = my_converter.getfunction(int(address[2:], 16))
                print '    ' + function +', ' + lineinfile
        else:
            print onealloc 
