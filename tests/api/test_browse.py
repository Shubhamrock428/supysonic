#!/usr/bin/env python
# coding: utf-8
#
# This file is part of Supysonic.
# Supysonic is a Python implementation of the Subsonic server API.
#
# Copyright (C) 2017 Alban 'spl0k' Féron
#
# Distributed under terms of the GNU AGPLv3 license.

import time
import uuid

from lxml import etree

from supysonic.db import Folder, Artist, Album, Track, db_session

from .apitestbase import ApiTestBase

class BrowseTestCase(ApiTestBase):
    def setUp(self):
        super(BrowseTestCase, self).setUp()

        with db_session:
            Folder(root = True, name = 'Empty root', path = '/tmp')
            root = Folder(root = True, name = 'Root folder', path = 'tests/assets')

            for letter in 'ABC':
                folder = Folder(
                    name = letter + 'rtist',
                    path = 'tests/assets/{}rtist'.format(letter),
                    parent = root
                )

                artist = Artist(name = letter + 'rtist')

                for lether in 'AB':
                    afolder = Folder(
                        name = letter + lether + 'lbum',
                        path = 'tests/assets/{0}rtist/{0}{1}lbum'.format(letter, lether),
                        parent = folder
                    )

                    album = Album(name = letter + lether + 'lbum', artist = artist)

                    for num, song in enumerate([ 'One', 'Two', 'Three' ]):
                        track = Track(
                            disc = 1,
                            number = num,
                            title = song,
                            duration = 2,
                            album = album,
                            artist = artist,
                            bitrate = 320,
                            path = 'tests/assets/{0}rtist/{0}{1}lbum/{2}'.format(letter, lether, song),
                            content_type = 'audio/mpeg',
                            last_modification = 0,
                            root_folder = root,
                            folder = afolder
                        )

            self.assertEqual(Folder.select().count(), 11)
            self.assertEqual(Folder.select(lambda f: f.root).count(), 2)
            self.assertEqual(Artist.select().count(), 3)
            self.assertEqual(Album.select().count(), 6)
            self.assertEqual(Track.select().count(), 18)

    def test_get_music_folders(self):
        # Do not validate against the XSD here, this is the only place where the API should return ids as ints
        # all our ids are uuids :/
        rv, child = self._make_request('getMusicFolders', tag = 'musicFolders', skip_xsd = True)
        self.assertEqual(len(child), 2)
        self.assertSequenceEqual(sorted(self._xpath(child, './musicFolder/@name')), [ 'Empty root', 'Root folder' ])

    def test_get_indexes(self):
        self._make_request('getIndexes', { 'musicFolderId': 'abcdef' }, error = 0)
        self._make_request('getIndexes', { 'musicFolderId': str(uuid.uuid4()) }, error = 70)
        self._make_request('getIndexes', { 'ifModifiedSince': 'quoi' }, error = 0)

        rv, child = self._make_request('getIndexes', { 'ifModifiedSince': int(time.time() * 1000 + 1000) }, tag = 'indexes')
        self.assertEqual(len(child), 0)

        with db_session:
            fid = Folder.get(name = 'Empty root').id
        rv, child = self._make_request('getIndexes', { 'musicFolderId': str(fid) }, tag = 'indexes')
        self.assertEqual(len(child), 0)

        rv, child = self._make_request('getIndexes', tag = 'indexes')
        self.assertEqual(len(child), 3)
        for i, letter in enumerate([ 'A', 'B', 'C' ]):
            self.assertEqual(child[i].get('name'), letter)
            self.assertEqual(len(child[i]), 1)
            self.assertEqual(child[i][0].get('name'), letter + 'rtist')

    def test_get_music_directory(self):
        self._make_request('getMusicDirectory', error = 10)
        self._make_request('getMusicDirectory', { 'id': 'id' }, error = 0)
        self._make_request('getMusicDirectory', { 'id': str(uuid.uuid4()) }, error = 70)

        # should test with folders with both children folders and tracks. this code would break in that case
        with db_session:
            for f in Folder.select():
                rv, child = self._make_request('getMusicDirectory', { 'id': str(f.id) }, tag = 'directory')
                self.assertEqual(child.get('id'), str(f.id))
                self.assertEqual(child.get('name'), f.name)
                self.assertEqual(len(child), f.children.count() + f.tracks.count())
                for dbc, xmlc in zip(sorted(f.children, key = lambda c: c.name), sorted(child, key = lambda c: c.get('title'))):
                    self.assertEqual(dbc.name, xmlc.get('title'))
                    self.assertEqual(xmlc.get('artist'), f.name)
                    self.assertEqual(xmlc.get('parent'), str(f.id))
                for t, xmlc in zip(sorted(f.tracks, key = lambda t: t.title), sorted(child, key = lambda c: c.get('title'))):
                    self.assertEqual(t.title, xmlc.get('title'))
                    self.assertEqual(xmlc.get('parent'), str(f.id))

    def test_get_artists(self):
        # same as getIndexes standard case
        # dataset should be improved to have a different directory structure than /root/Artist/Album/Track

        rv, child = self._make_request('getArtists', tag = 'artists')
        self.assertEqual(len(child), 3)
        for i, letter in enumerate([ 'A', 'B', 'C' ]):
            self.assertEqual(child[i].get('name'), letter)
            self.assertEqual(len(child[i]), 1)
            self.assertEqual(child[i][0].get('name'), letter + 'rtist')

    def test_get_artist(self):
        # dataset should be improved to have tracks by a different artist than the album's artist
        self._make_request('getArtist', error = 10)
        self._make_request('getArtist', { 'id': 'artist' }, error = 0)
        self._make_request('getArtist', { 'id': str(uuid.uuid4()) }, error = 70)

        with db_session:
            for ar in Artist.select():
                rv, child = self._make_request('getArtist', { 'id': str(ar.id) }, tag = 'artist')
                self.assertEqual(child.get('id'), str(ar.id))
                self.assertEqual(child.get('albumCount'), str(len(child)))
                self.assertEqual(len(child), ar.albums.count())
                for dal, xal in zip(sorted(ar.albums, key = lambda a: a.name), sorted(child, key = lambda c: c.get('name'))):
                    self.assertEqual(dal.name, xal.get('name'))
                    self.assertEqual(xal.get('artist'), ar.name) # could break with a better dataset
                    self.assertEqual(xal.get('artistId'), str(ar.id)) # see above

    def test_get_album(self):
        self._make_request('getAlbum', error = 10)
        self._make_request('getAlbum', { 'id': 'nastynasty' }, error = 0)
        self._make_request('getAlbum', { 'id': str(uuid.uuid4()) }, error = 70)

        with db_session:
            a = Album.select().first()
            rv, child = self._make_request('getAlbum', { 'id': str(a.id) }, tag = 'album')
            self.assertEqual(child.get('id'), str(a.id))
            self.assertEqual(child.get('songCount'), str(len(child)))

            self.assertEqual(len(child), a.tracks.count())
            for dal, xal in zip(sorted(a.tracks, key = lambda t: t.title), sorted(child, key = lambda c: c.get('title'))):
                self.assertEqual(dal.title, xal.get('title'))
                self.assertEqual(xal.get('album'), a.name)
                self.assertEqual(xal.get('albumId'), str(a.id))

    def test_get_song(self):
        self._make_request('getSong', error = 10)
        self._make_request('getSong', { 'id': 'nastynasty' }, error = 0)
        self._make_request('getSong', { 'id': str(uuid.uuid4()) }, error = 70)

        with db_session:
            s = Track.select().first()
        self._make_request('getSong', { 'id': str(s.id) }, tag = 'song')

    def test_get_videos(self):
        self._make_request('getVideos', error = 0)

if __name__ == '__main__':
    unittest.main()

