#!/usr/bin/env python

'''
Given a directory path, uploads objects to a Cloud Files container, sets
appropriate container metadata, and CDN-enables the container so that all
files in the original path can be used as a static website.
'''

import sys
import os
from urllib import quote
from optparse import OptionParser

import cloudfiles
import cf_auth

def find_objects_iter(root):
    for base, dirs, filenames in os.walk(root):
        for f in filenames:
            yield os.path.join(base, f)
        for d in dirs:
            for x in find_objects_iter(os.path.join(base, d)):
                yield x


if __name__ == '__main__':
    usage = 'Usage: %prog [options] path'
    parser = OptionParser(usage=usage)
    parser.add_option('-D', '--domain', dest='domain', default=None,
                  help='Domain to use instead of the container\'s public URI')
    parser.add_option('-c', '--container', dest='container', default=None,
                  help='Container to use')

    options, args = parser.parse_args()
    site_container_name = options.container or 'website'
    conn = cloudfiles.get_connection(username=cf_auth.username,
                                     api_key=cf_auth.apikey)
    # make sure we have the container
    container = conn.create_container(site_container_name)
    # make sure the container is public and has the staticweb metadata
    container.make_public()
    container.set_staticweb_metadata(index='index.html',
                                     listings=False,
                                     error='error.html',
                                     listings_css=None)
    root = args[0]
    for i in find_objects_iter(root):
        object_name = quote(i[len(root) + 1:])
        obj = container.create_object(object_name)
        try:
            obj.load_from_filename(i)
        except Exception, err:
            print 'error (%s) with %s' % (err, i)
            continue
        else:
            print object_name, 'uploaded'
    container_url = options.domain if options.domain else container.public_uri()
    if not container_url.startswith('http://'):
        container_url = 'http://' + container_url + '/'
    print container_url
