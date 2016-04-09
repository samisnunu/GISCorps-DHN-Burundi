# source: https://github.com/Vanuan/csv2osm
#
# Edit April 2, 2016 Sami Snunu, OSM ID: Sami Snunu
#           - Added proper header  to xml
#           - Syntax of tags with tab instead of spaces.
#           - Save output into .osm file instead to print.
#           - Commented valid tags, and removed as parameters from methods.
#           - Check if empty element id is supplied, create a negative ID to create.
#           - Added exception error catch.
#           - Remove id as tag, preventing duplicate entries.
#           - Reformat the python code for optimization.
#
#  Example running the command as follows:
#  python "C:\Scripts\csv2osm.py" "C:\Data\Test.csv"
#
# The output will be, 'C:\OSM Data\test.osm' file.
#

import csv
import os
import sys


def print_osm_xml(reader, lat, lon):
    i = -1
    for row in reader:
        if 'id' in row:
            if row['id'] != "":
                osm_id = row['id']
                action = "modify"
            else:
                osm_id = i
                i -= 1
                action = "create"
        else:
            osm_id = i
            i -= 1
            action = "create"
        version = ''
        if 'version' in row:
            version = 'version="%s"' % row['version']
        output.write('\t\t<node id="%s" action="%s" lat="%f" lon="%f" %s visible="true">\n' %
                     (osm_id, action, float(row[lat].replace(',', '.')), float(row[lon].replace(',', '.')), version))
        print_tags(row, lat, lon)
        output.write('\t\t</node>\n')
    output.write('\t</osm>')


def print_tags(row, lat, lon):
    for k, v in row.iteritems():
        if k != lat and k != lon and k != 'id' and v != '':
            output.write('\t\t\t<tag k="%s" v="%s" />\n' % (k, v))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage: ', sys.argv[0], ' table.csv'
        sys.exit(-1)

try:
    osm_file = os.path.splitext(sys.argv[1])[0] + ".osm"
    with open(osm_file, 'w', ) as output:
        with open(sys.argv[1], 'rb') as csv_file:
            output.write(
                "<?xml version='1.0' encoding='UTF-8'?>"'\n<osm version="0.6" upload="true" generator="csv2osm">\n')
            reader = csv.DictReader(csv_file, delimiter=',', dialect='excel')
            print_osm_xml(reader, 'lat', 'lon')
    print("Successfully created " + osm_file)

except Exception as err:
    sys.exit("Error: Could't create the osm file:\n\t\t" + str(err))
