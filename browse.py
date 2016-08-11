#!/usr/bin/python
#
# Urwid example lazy directory browser / tree view
#    Copyright (C) 2004-2011  Ian Ward
#    Copyright (C) 2010  Kirk McDonald
#    Copyright (C) 2010  Rob Lanphier
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

"""
Urwid example lazy directory browser / tree view

Features:
- custom selectable widgets for files and directories
- custom message widgets to identify access errors and empty directories
- custom list walker for displaying widgets in a tree fashion
- outputs a quoted list of files and directories "selected" on exit
"""

import itertools
import re
import os

import urwid




import os
import functools
import sys

from heapq import *
from math import log

def pretty_size(n,pow=0,b=1024,u='B',pre=['']+[p for p in'KMGTPEZY']):
    pow,n=min(int(log(max(n*b**pow,1),b)),len(pre)-1),n*b**pow
    return "["+"%%.%if %%s%%s"%abs(pow%(-pow-1))%(n/b**float(pow),pre[pow],u)+"]"

startpath = os.getcwd()
count = 0
tsize = 0
if len(sys.argv) > 1:
    startpath = sys.argv[1]

all_dirs = {}
truetoabsmap = {}

def getAbsName(path):
    try:
        # strip out the size info, by looking for the second space
        parts = path.split("/")
        tpath = ""
        for part in parts:
            if part == "":
                continue
            count = 0
            npart = part
            for pos in range(len(part)):
                char = part[pos]
                if char == " ":
                    count += 1
                if count == 2:
                    npart = part[pos+1:]
                    break
            tpath += "/"+npart
        return tpath
        #return truetoabsmap[path]
    except Exception as e:
        print "ERROR: ", e.message
        return path

def getSize(path):
    try:
        return all_dirs[path]["size"]
    except:
        return 0

def getTrueName(path):
    try:
        return all_dirs[path]["truename"]
    except:
        return os.path.basename(path)

data = []
threshold = 10000000 # only files over treshold bytes


all_dirs[os.getcwd()] = {"name": os.getcwd(), "size": 0, "parent": None, "truename": os.path.basename(os.getcwd())}

def update_going_up(path, size):
    if path == None:
        return
    all_dirs[path]["size"] += size
    all_dirs[path]["truename"] = pretty_size(all_dirs[path]["size"]) + " " + os.path.basename(all_dirs[path]["name"])
    #all_dirs[path]["truename"] =  os.path.basename(all_dirs[path]["name"])
    update_going_up(all_dirs[path]["parent"], size)

for (path, dirs, files) in os.walk(startpath):
    for dirname in dirs:
        mypath = (path+"/"+dirname).replace("//", "/")
        all_dirs[mypath] = {"name": dirname, "size": 0, "parent":path}
    for filename in files:
        try:
            mypath = (path+"/"+filename).replace("//", "/")
            size = os.stat(mypath).st_size
            all_dirs[mypath] = {"name": filename, "size": size, "parent": path, "truename": filename}
            update_going_up(mypath, size)
            tsize += size
        except Exception as e:
            pass
            print "Error accessing "+path+"/"+filename, e.message
        count += 1
        if count%10000 == 0:
            print "scanned "+str(count)+" files, "+pretty_size(tsize)+" so far ("+(path+'/'+filename)+")"
#        if size >= threshold:
#            heappush(data, (-1*size, path+filename))

#for key in all_dirs:
#    parent = ""
#    if all_dirs[key]["parent"]:
#        parent = all_dirs[key]["parent"]
#
#    fakename = parent+"/"+all_dirs[key]["truename"]
#    absname = parent+"/"+all_dirs[key]["name"]
#    
#    truetoabsmap[fakename] = absname

print("\nTotal Files: "+str(count))
print("Total Size: "+pretty_size(tsize))

#print all_dirs





class FlagFileWidget(urwid.TreeWidget):
    # apply an attribute to the expand/unexpand icons
    unexpanded_icon = urwid.AttrMap(urwid.TreeWidget.unexpanded_icon,
        'dirmark')
    expanded_icon = urwid.AttrMap(urwid.TreeWidget.expanded_icon,
        'dirmark')

    def __init__(self, node):
        self.__super.__init__(node)
        # insert an extra AttrWrap for our own use
        self._w = urwid.AttrWrap(self._w, None)
        self.flagged = False
        self.update_w()

    def selectable(self):
        return True

    def keypress(self, size, key):
        """allow subclasses to intercept keystrokes"""
        flipback = False
       # if self.is_leaf:
       #     flipback = True
       #     self.is_leaf = False
        if key in ("l") and not flipback:
            key = self.__super.keypress(size, "right")
        elif key in ("h", "left") and not flipback:
            key = self.__super.keypress(size, "-")
        elif key in ("j"):
            key = self.__super.keypress(size, "down")
        elif key in ("k"):
            key = self.__super.keypress(size, "up")
        key = self.__super.keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
       # if flipback:
       #     self.is_leaf = True
        return key

    def unhandled_keys(self, size, key):
        """
        Override this method to intercept keystrokes in subclasses.
        Default behavior: Toggle flagged on space, ignore other keys.
        """
        if key == " ":
            self.flagged = not self.flagged
            self.update_w()
        else:
            return key

    def update_w(self):
        """Update the attributes of self.widget based on self.flagged.
        """
        if self.flagged:
            self._w.attr = 'flagged'
            self._w.focus_attr = 'flagged focus'
        else:
            self._w.attr = 'body'
            self._w.focus_attr = 'focus'


class FileTreeWidget(FlagFileWidget):
    """Widget for individual files."""
    def __init__(self, node):
        self.__super.__init__(node)
        path = node.get_value()
        add_widget(path, self)

    def get_display_text(self):
        return self.get_node().get_key()



class EmptyWidget(urwid.TreeWidget):
    """A marker for expanded directories with no contents."""
    def get_display_text(self):
        return ('flag', '(empty directory)')


class ErrorWidget(urwid.TreeWidget):
    """A marker for errors reading directories."""

    def get_display_text(self):
        return ('error', "(error/permission denied)")


class DirectoryWidget(FlagFileWidget):
    """Widget for a directory."""
    def __init__(self, node):
        self.__super.__init__(node)
        path = node.get_value()
        add_widget(path, self)
        self.expanded = starts_expanded(path)
        self.update_expanded_icon()

    def get_display_text(self):
        node = self.get_node()
        if node.get_depth() == 0:
            return "/"
        else:
            return node.get_key()


class FileNode(urwid.TreeNode):
    """Metadata storage for individual files"""

    def __init__(self, path, parent=None):
        depth = path.count(dir_sep())
        key = getTrueName(path)
        urwid.TreeNode.__init__(self, path, key=key, parent=parent, depth=depth)

    def load_parent(self):
        parentname, myname = os.path.split(self.get_value())
        parent = DirectoryNode(parentname)
        parent.set_child_node(self.get_key(), self)
        return parent

    def load_widget(self):
        return FileTreeWidget(self)


class EmptyNode(urwid.TreeNode):
    def load_widget(self):
        return EmptyWidget(self)


class ErrorNode(urwid.TreeNode):
    def load_widget(self):
        return ErrorWidget(self)


class DirectoryNode(urwid.ParentNode):
    """Metadata storage for directories"""

    def __init__(self, path, parent=None):
        if path == dir_sep():
            depth = 0
            key = None
        else:
            depth = path.count(dir_sep())
            key = getTrueName(path)
        urwid.ParentNode.__init__(self, path, key=key, parent=parent,
                                  depth=depth)

    def load_parent(self):
        parentname, myname = os.path.split(self.get_value())
        parent = DirectoryNode(parentname)
        parent.set_child_node(self.get_key(), self)
        return parent

    def load_child_keys(self):
        dirs = []
        files = []
        try:
            path = self.get_value()
            #dd.write("incoming: "+path+"\n")
            path = getAbsName(path)
            #dd.write("outgoing: "+path+"\n")
            # separate dirs and files
            for a in os.listdir(path):
                truepath = os.path.join(path,a)
                if os.path.isdir(truepath):
                    dirs.append( (-1*getSize(truepath), getTrueName(truepath)) )
                else:
                    files.append( (-1*getSize(truepath), getTrueName(truepath)) )
        except OSError, e:
            depth = self.get_depth() + 1
            self._children[None] = ErrorNode(self, parent=self, key=None,
                                             depth=depth)
            return [None]

        # sort dirs and files
        dirs.sort()
        files.sort()
        # store where the first file starts
        self.dir_count = len(dirs)
        # collect dirs and files together again
        keys = [x[1] for x in dirs] + [x[1] for x in files]
        if len(keys) == 0:
            depth=self.get_depth() + 1
            self._children[None] = EmptyNode(self, parent=self, key=None,
                                             depth=depth)
            keys = [None]
        return keys

    def load_child_node(self, key):
        """Return either a FileNode or DirectoryNode"""
        index = self.get_child_index(key)
        if key is None:
            return EmptyNode(None)
        else:
            path = os.path.join(self.get_value(), key)
            if index < self.dir_count:
                return DirectoryNode(path, parent=self)
            else:
                path = os.path.join(self.get_value(), key)
                return FileNode(path, parent=self)

    def load_widget(self):
        return DirectoryWidget(self)


class DirectoryBrowser:
    palette = [
        ('body', 'white', 'black'),
        ('flagged', 'yellow', 'dark cyan', ('standout', 'bold','underline')),
        ('focus', 'black', 'light gray', 'standout'),
        ('flagged focus', 'white', 'dark green',
                ('bold','standout','underline')),
        ('head', 'white', 'black', 'standout'),
        ('foot', 'light cyan', 'black'),
        ('key', 'light cyan', 'black','underline'),
        ('title', 'white', 'black', 'bold'),
        ('dirmark', 'black', 'dark cyan', 'bold'),
        ('flag', 'dark gray', 'light gray'),
        ('error', 'dark red', 'white'),
        ]

    footer_text = [
        ('title', "urwiddu - Python Disk Usage"), "    ",
        ('key', "K"), ",", ('key', "J"), ",",
        ('key', "PAGE UP"), ",", ('key', "PAGE DOWN"),
        "  ",
        ('key', "SPACE"), "  ",
        ('key', "+"), ",",
        ('key', "-"), "  ",
        ('key', "H"), "  ",
        ('key', "L"), "  ",
        ('key', "HOME"), "  ",
        ('key', "END"), "  ",
        ('key', "Q"),
        ]


    def __init__(self):
        cwd = os.getcwd()
        store_initial_cwd(cwd)
        self.header = urwid.Text("")
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(DirectoryNode(cwd)))
        self.listbox.offset_rows = 1
        self.footer = urwid.AttrWrap(urwid.Text(self.footer_text),
            'foot')
        self.view = urwid.Frame(
            urwid.AttrWrap(self.listbox, 'body'),
            header=urwid.AttrWrap(self.header, 'head'),
            footer=self.footer)

    def main(self):
        """Run the program."""

        self.loop = urwid.MainLoop(self.view, self.palette,
            unhandled_input=self.unhandled_input)
        self.loop.run()

        # on exit, write the flagged filenames to the console
        names = [escape_filename_sh(x) for x in get_flagged_names()]
        print " ".join(names)

    def unhandled_input(self, k):
        # update display of focus directory
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()


def main():
    DirectoryBrowser().main()




#######
# global cache of widgets
_widget_cache = {}

def add_widget(path, widget):
    """Add the widget for a given path"""

    _widget_cache[path] = widget

def get_flagged_names():
    """Return a list of all filenames marked as flagged."""

    l = []
    for w in _widget_cache.values():
        if w.flagged:
            l.append(w.get_node().get_value())
    return l



######
# store path components of initial current working directory
_initial_cwd = []

def store_initial_cwd(name):
    """Store the initial current working directory path components."""

    global _initial_cwd
    _initial_cwd = name.split(dir_sep())

def starts_expanded(name):
    """Return True if directory is a parent of initial cwd."""

    if name is '/':
        return True

    l = name.split(dir_sep())
    if len(l) > len(_initial_cwd):
        return False

    if l != _initial_cwd[:len(l)]:
        return False

    return True


def escape_filename_sh(name):
    """Return a hopefully safe shell-escaped version of a filename."""

    # check whether we have unprintable characters
    for ch in name:
        if ord(ch) < 32:
            # found one so use the ansi-c escaping
            return escape_filename_sh_ansic(name)

    # all printable characters, so return a double-quoted version
    name.replace('\\','\\\\')
    name.replace('"','\\"')
    name.replace('`','\\`')
    name.replace('$','\\$')
    return '"'+name+'"'


def escape_filename_sh_ansic(name):
    """Return an ansi-c shell-escaped version of a filename."""

    out =[]
    # gather the escaped characters into a list
    for ch in name:
        if ord(ch) < 32:
            out.append("\\x%02x"% ord(ch))
        elif ch == '\\':
            out.append('\\\\')
        else:
            out.append(ch)

    # slap them back together in an ansi-c quote  $'...'
    return "$'" + "".join(out) + "'"

SPLIT_RE = re.compile(r'[a-zA-Z]+|\d+')
def alphabetize(s):
    L = []
    for isdigit, group in itertools.groupby(SPLIT_RE.findall(s), key=lambda x: x.isdigit()):
        if isdigit:
            for n in group:
                L.append(('', int(n)))
        else:
            L.append((''.join(group).lower(), 0))
    return L

def dir_sep():
    """Return the separator used in this os."""
    return getattr(os.path,'sep','/')


if __name__=="__main__":
    main()

