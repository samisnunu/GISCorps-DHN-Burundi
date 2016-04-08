#! /usr/bin/python2
# vim: fileencoding=utf-8 encoding=utf-8 et sw=4

# Copyright (C) 2009 Jacek Konieczny <jajcus@jajcus.net>
# Copyright (C) 2009 Andrzej Zaborowski <balrogg@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#-------------------------------------------------------------------------------
# Edit: March 25,2016 by Sami Snunu, OSMID: SamiSnunu:
#               - Tested to conform with the latest (Python 2.7.6) release
#				- Removed unnecessary encoding commands.
#				- Added the OSM DEV server URL
# 				- Let the process create a new changeset, always
#				- Ensure to close the (.diffxml) file
#               - Modified several entries for meaningfull error descriptions.
# Edit: April 1,2016 by Sami Snunu, OSMID: SamiSnunu:
#               - In case of change type "modify", retrieve the version of the element first.
#


"""
Uploads complete osmChange 0.3 files.  Use your login (not email) as username.
"""

__version__ = "$Revision: 21 $"

import os
import subprocess
import sys
import traceback
import httplib
import xml.etree.cElementTree as ElementTree
import xml.etree.ElementTree as ET
import urlparse
import locale, codecs

# try:
    # locale.setlocale(locale.LC_ALL, "en_Us.UTF-8")
    # encoding = locale.getlocale()[1]
    # sys.stdout = codecs.getwriter(encoding)(sys.stdout, errors = "replace")
    # sys.stderr = codecs.getwriter(encoding)(sys.stderr, errors = "replace")
# except locale.Error:
    # pass

class HTTPError(Exception):
    pass

class OSM_API(object):
     # Using OSM DEV server (Master Dev) 'http://master.apis.dev.openstreetmap.org/'
     # or 'http://api06.dev.openstreetmap.org/'
	 # For the Production OSM Server URL, replace by 'http://api.openstreetmap.org/'
    url ='http://api06.dev.openstreetmap.org/'
    def __init__(self, username = None, password = None):
        if username and password:
            self.username = username
            self.password = password
        else:
            self.username = ""
            self.password = ""
        self.changeset = None
        self.progress_msg = None

    def __del__(self):
        if self.changeset is not None:
            self.close_changeset()
        pass

    def msg(self, mesg):
        sys.stderr.write(u"\r%s...                     " % (self.progress_msg))
        sys.stderr.write(u"\r%s...%s" % (self.progress_msg, mesg))
        sys.stderr.flush()

    def request(self, conn, method, url, body, headers, progress):
        if progress:
            self.msg("making request")
            conn.putrequest(method, url)
            self.msg("sending headers")
            if body:
                conn.putheader('Content-Length', str(len(body)))
            for hdr, value in headers.iteritems():
                conn.putheader(hdr, value)
            self.msg("end of headers")
            conn.endheaders()
            self.msg(" 0%")
            if body:
                start = 0
                size = len(body)
                chunk = size / 100
                if chunk < 16384:
                    chunk = 16384
                while start < size:
                    end = min(size, start + chunk)
                    conn.send(body[start:end])
                    start = end
                    self.msg("%2i%%" % (start * 100 / size))
        else:
            self.msg(" ")
            conn.request(method, url, body, headers)

    def _run_request(self, method, url, body = None, progress = 0, content_type = "text/xml"):
        url = urlparse.urljoin(self.url, url)
        purl = urlparse.urlparse(url)
        if purl.scheme != "http":
            raise ValueError, "Unsupported url scheme: %r" % (purl.scheme,)
        if ":" in purl.netloc:
            host, port = purl.netloc.split(":", 1)
            port = int(port)
        else:
            host = purl.netloc
            port = None
        url = purl.path
        if purl.query:
            url += "?" + query
        headers = {}
        if body:
            headers["Content-Type"] = content_type

        try_no_auth = 0

        if not try_no_auth and not self.username:
            raise HTTPError, (0, "Need a username")

        try:
            self.msg("Connecting")
            conn = httplib.HTTPConnection(host, port)
#            conn.set_debuglevel(10)

            if try_no_auth:
                self.request(conn, method, url, body, headers, progress)
                self.msg("Waiting for status")
                response = conn.getresponse()

            if not try_no_auth or (response.status == httplib.UNAUTHORIZED and
                    self.username):
                if try_no_auth:
                    conn.close()
                    self.msg("Re-connecting")
                    conn = httplib.HTTPConnection(host, port)
#                    conn.set_debuglevel(10)

                creds = self.username + ":" + self.password
                headers["Authorization"] = "Basic " + \
                        creds.encode("base64").strip()
                self.request(conn, method, url, body, headers, progress)
                self.msg("Waiting for status")
                response = conn.getresponse()

            if response.status == httplib.OK:
                self.msg("Reading response...OK")
                sys.stderr.flush()
                response_body = response.read()
            else:
                raise HTTPError, (response.status, "%03i: %s (%s)" % (
                    response.status, response.reason, response.read()))
        finally:
            conn.close()
        return response_body

    def create_changeset(self, comment):
        if self.changeset is not None:
            raise RuntimeError, "Changeset already opened: (Create Changeset)"
        self.progress_msg = "I'm creating a new changeset"
        self.msg("")
        root = ElementTree.Element("osm")
        tree = ElementTree.ElementTree(root)
        element = ElementTree.SubElement(root, "changeset")
#        ElementTree.SubElement(element, "tag", {"k": "created_by", "v": created_by})
        ElementTree.SubElement(element, "tag", {"k": "comment", "v": comment})
#        ElementTree.SubElement(element, "tag", {"k": "import", "v": "yes"})
#        ElementTree.SubElement(element, "tag", {"k": "source", "v": "DHN"})
#       ElementTree.SubElement(element, "tag", {"k": "revert", "v": "yes"})
#       ElementTree.SubElement(element, "tag", {"k": "url", "v": "http://www.openstreetmap.org/user/nmixter/diary/8218"})
        body = ElementTree.tostring(root, "utf-8")
        reply = self._run_request("PUT", "/api/0.6/changeset/create", body)
        changeset = int(reply.strip())
        self.msg("Done. New changeset ID is: %i" % (changeset))
        print >>sys.stderr, ""
        self.changeset = changeset

    def upload(self, change):
        if self.changeset is None:
            raise RuntimeError, "Uploading...Changeset not opened: (Upload)"
        self.progress_msg = "Now I'm sending changes"
        self.msg("")
        for operation in change:
            if operation.tag not in ("create", "modify", "delete"):
                continue
            # get the node element version and increment it by 1:
            elemvers =0
            for element in operation:
                elem= element.attrib["id"]
                if not int(elem) < 0:
                   try:
                        elemver = self._run_request("GET", "/api/0.6/node/" + elem)
                        treev = ET.fromstring(elemver)
                        for child in treev:
                            for atrb in child.attrib:
                                if atrb=="version":
                                    elemvers= int(child.attrib["version"])
                                    break
                   except Exception, err:
                        print err
                        Exit(1)

                element.attrib["version"] = str(elemvers)
                element.attrib["changeset"] = str(self.changeset)
        body = ElementTree.tostring(change, "utf-8")
        reply = self._run_request("POST", "/api/0.6/changeset/%i/upload"
                                                % (self.changeset,), body, 1)
        self.msg("Done.")
        print >>sys.stderr, ""
        return reply

    def close_changeset(self):
        if self.changeset is None:
            raise RuntimeError, "Changeset not opened: Close Changeset"
        self.progress_msg = "Closing"
        self.msg("")
        reply = self._run_request("PUT", "/api/0.6/changeset/%i/close"
                                                    % (self.changeset,))
        self.changeset = None
        self.msg("Cloased the changeset.")
        print >>sys.stderr, ""


try:
    this_dir = os.path.dirname(__file__)
    try:
        version = int(subprocess.Popen(["svnversion", this_dir], stdout = subprocess.PIPE).communicate()[0].strip())
    except:
        version = 1
    if len(sys.argv) < 2:
        print >>sys.stderr, "Synopsis:"
        print >>sys.stderr, "    %s Missing <file-name.osc> [<file-name.osc>...]"
        sys.exit(1)

    filenames = []
    param = {}
    num = 0
    skip = 0
    for arg in sys.argv[1:]:
        num += 1
        if skip:
            skip -= 1
            continue

        if arg == "-u":
            param['user'] = sys.argv[num + 1]
            skip = 1
        elif arg == "-p":
            param['pass'] = sys.argv[num + 1]
            skip = 1
        elif arg == "-c":
            param['confirm'] = sys.argv[num + 1]
            skip = 1
        elif arg == "-m":
            param['comment'] = sys.argv[num + 1]
            skip = 1
        elif arg == "-s":
            param['changeset'] = sys.argv[num + 1]
            skip = 1
        elif arg == "-n":
            param['start'] = 1
            skip = 0
        else:
            filenames.append(arg)

    if 'user' in param:
        login = param['user']
    else:
        login = raw_input("OSM login: ")
    if not login:
        sys.exit(1)
    if 'pass' in param:
        password = param['pass']
    else:
        password = raw_input("OSM password: ")
    if not password:
        sys.exit(1)

    api = OSM_API(login, password)

    changes = []
    for filename in filenames:
        if not os.path.exists(filename):
            print >>sys.stderr, "File %r doesn't exist!" % (filename,)
            sys.exit(1)
        tree = ElementTree.parse(filename)
        root = tree.getroot()
        if root.tag != "osmChange" or (root.attrib.get("version") != "0.3" and
                root.attrib.get("version") != "0.6"):
            print >>sys.stderr, "File %s is not a v0.3 osmChange file!" % (filename,)
            sys.exit(1)

        if filename.endswith(".osc"):
            diff_fn = filename[:-4] + ".diff.xml"
        else:
            diff_fn = filename + ".diff.xml"
        # if os.path.exists(diff_fn):
            # print >>sys.stderr, "Diff file %r already exists, delete it " \
                    # "if you're sure you want to re-upload" % (diff_fn,)
            # sys.exit(1) #  modify  to overwrite the file, no need  keep it, sami

        if filename.endswith(".osc"):
            comment_fn = filename[:-4] + ".comment"
        else:
            comment_fn = filename + ".comment"
        try:
            comment_file = codecs.open(comment_fn, "r", "utf-8")
            comment = comment_file.read().strip()
            comment_file.close()
        except IOError:
            comment = None
        if not comment:
            if 'comment' in param:
                comment = param['comment']
            else:
                comment = raw_input("Your comment to %r: " % (filename,))
            if not comment:
                sys.exit(1)
            try:
                comment = comment.decode(locale.getlocale()[1])
            except TypeError:
				comment = comment.decode("UTF-8")

        print >>sys.stderr, "     File: %r" % (filename,)
        print >>sys.stderr, "     Comment: %s" % (comment,)

        if 'confirm' in param:
            sure = param['confirm']
        else:
            print >>sys.stderr, "Are you sure you want to send these changes?",
            sure = raw_input()
        if sure.lower() not in ("y", "yes"):
            print >>sys.stderr, "Skipping...\n"
            continue
        print >>sys.stderr, ""
        if 'changeset' not in param:
            #api.changeset = int(param['changeset'])      # no just create a new changeset
        #else:

            api.create_changeset("%s" % comment)
            #if 'start' in param:
                #print api.changeset
                #sys.exit(0)                               # no.. keep going
        try:
            diff_file = codecs.open(diff_fn, "w", "utf-8")
            diff = api.upload(root)
            diff_file.write(diff)
            diff_file.close()
        except HTTPError, (code, err):
            sys.stderr.write("\n Error: " + err + "\n")
            if code in [ 404, 409, 412 ]: # Merge conflict
               #print  err + ":  " +  str(code)
			   # TODO: also unlink when not the whole file has been uploaded
                # because then likely the server will not be able to parse
                # it and nothing gets committed
               diff_file.close()                           #close the file first
               os.unlink(diff_fn)
            sys.exit(1)
        finally:
            if 'changeset' not in param:
				api.close_changeset()



except HTTPError, (code, err):
    sys.stderr.write(err)
    sys.exit(1)
except Exception, err:
    print >>sys.stderr, repr(err)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
