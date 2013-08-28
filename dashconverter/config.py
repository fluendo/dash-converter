# dash-converter - Converts multimedia streams to DASH format using GStreamer
# Copyright (C) 2013 Fluendo S.L. <support@fluendo.com>
#   * authors: Andoni Morales <amorales@fluendo.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


class OutputStream(object):

    name = 'Name'
    codec = None
    bitrate = 0

    def __init__(self, name, codec, bitrate):
        self.name = name
        self.codec = codec
        self.bitrate = bitrate


class AudioOutputStream(OutputStream):

    rate = None
    channels = 2

    def __init__(self, name, codec, bitrate, rate=None):
        OutputStream.__init__(self, name, codec, bitrate)
        self.rate = rate

    def __str__(self):
        return "%s %s %skbps" % (self.name, self.codec, self.bitrate)


class VideoOutputStream(OutputStream):

    width = 320
    height = 240
    fps_n = None
    fps_d = None
    profile = 'baseline'

    def __init__(self, name, codec, bitrate, width=320, height=240, fps_n=None,
                 fps_d=None, profile='baseline'):
        OutputStream.__init__(self, name, codec, bitrate)
        self.width = width
        self.height = height
        self.fps_n = fps_n
        self.fps_d = fps_d
        self.profile = profile

    def __str__(self):
        return "%s %s %skbps %sx%s" % (self.name, self.codec, self.bitrate,
                self.width, self.height)



class Config(object):
    '''
    Holds the configuration for the output properties

    @cvar title: Title of the stream
    @type title: str
    @cvar fragment_duration: duration of fragments in seconds
    @type fragment_duration: int
    @cvar output_directory: output directory for the new stream
    @type output_directory: str
    @cvar is_live: whether the content is live or not
    @type is_live: bool
    @cvar chunked: true if the output should be split in several files
    @type chunked: bool
    @cvar overlay_stream_desc: overlay the stream description
    @type overlay_stream_desc: bool
    @cvar overlay_timestamps: overlay timestamps
    @type overlay_timestamps: bool
    @cvar video_streams: List of L{VideoOutputStream}
    @type video_streams: list
    @cvar audio_streams: List of L{AudioOutputStream}
    @type audio_streams: list
    '''

    output_directory = '.'
    title = 'GStreamer DASH'
    fragment_duration = 2
    is_live = False
    chunked = False
    base_url = None
    overlay_stream_desc = True
    overlay_timestamps = True
    video_streams = []
    audio_streams = []

    def __init__(self):
        # Set default values
        self.video_streams = [
                VideoOutputStream ('h264_low', 'H264', 300),
                VideoOutputStream ('h264_mid', 'H264', 1000, 640, 480),
                VideoOutputStream ('h264_high', 'H264', 2000, 1280, 720),
                ]
        self.audio_streams = [
                AudioOutputStream ('aac', 'AAC', 128),
                ]

    def load(self, filename):
        config = {'AudioOutputStream': AudioOutputStream,
                  'VideoOutputStream': VideoOutputStream}
        try:
            execfile(filename, config)
        except Exception, ex:
            import traceback
            traceback.print_exc()
            raise ex
        for key, v in config.iteritems():
            setattr(self, key, v)
