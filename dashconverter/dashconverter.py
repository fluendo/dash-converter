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

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)
from gi.repository import GLib
GLib.threads_init()


class DashConverter(object):

    def __init__(self, input_file, config):
        self.input_file = input_file
        self.config = config
        self.pad_names = []

    def start(self):
        self.pipeline = Gst.Pipeline()
        self.decodebin = Gst.ElementFactory.make("uridecodebin", None)
        self.dashsink = Gst.ElementFactory.make("dashsink", None)

        self.decodebin.set_property("uri", self.input_file)
        self.dashsink.set_property("output-directory", self.config.output_directory)
        self.dashsink.set_property("fragment-duration", self.config.fragment_duration)
        self.dashsink.set_property("is-live", self.config.is_live)
        self.dashsink.set_property("chunked", self.config.chunked)
        self.dashsink.set_property("title", self.config.title)
        if self.config.base_url:
            self.dashsink.set_property("base-url", self.config.base_url)

        self.decodebin.connect('pad-added', self._on_pad_added)
        self.pipeline.add(self.decodebin)
        self.pipeline.add(self.dashsink)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch ()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop = GLib.MainLoop()
        self.mainloop.run()

    def _on_error(self, bus, message):
        sys.stderr.write(message.parse_error()[0].message)
        self.mainloop.quit()

    def _on_eos(self, bus, message):
        self.mainloop.quit()

    def _create_video_encode_bin(self, video_config):
        videoencodebin = Gst.Bin()
        outcaps = None
        if video_config.codec == 'H264':
            encoder = Gst.ElementFactory.make("x264enc", None)
            encoder.set_property ('bitrate', video_config.bitrate)
            encoder.set_property ('pass', 0)
            caps_str = "video/x-h264,stream-format=avc"
            if video_config.profile:
                caps_str += ',profile=%s' % video_config.profile
            outcaps = Gst.Caps.from_string(caps_str)
            outcaps = None
        else:
            raise Exception ("Unknown encoder %s", video_config.codec)
        scale = Gst.ElementFactory.make("videoscale", None)
        colorspace = Gst.ElementFactory.make("videoconvert", None)
        framerate = Gst.ElementFactory.make("videorate", None)
        timeoverlay = Gst.ElementFactory.make("timeoverlay", None)
        timeoverlay = Gst.ElementFactory.make("timeoverlay", None)
        textoverlay = Gst.ElementFactory.make("textoverlay", None)
        incapsfilter = Gst.ElementFactory.make("capsfilter", None)
        outcapsfilter = Gst.ElementFactory.make("capsfilter", None)
        muxer = Gst.ElementFactory.make("mp4dashmux", None)

        caps_str = 'video/x-raw'
        for f in ['width', 'height']:
            v = getattr(video_config, f)
            if v is not None:
                caps_str += ',%s=%s' % (f, v)
        incaps = Gst.Caps.from_string(caps_str)
        incapsfilter.set_property('caps', incaps)
        if outcaps:
            outcapsfilter.set_property('caps', outcaps)
        elements = [scale, colorspace, framerate, incapsfilter, timeoverlay,
                    textoverlay, encoder, outcapsfilter, muxer]
        for e in elements:
            videoencodebin.add(e)
        for i in range(len(elements) - 1):
            elements[i].link(elements[i+1])

        if self.config.overlay_stream_desc:
            textoverlay.set_property("font-desc", "DejaVu Sans Mono, 15")
            textoverlay.set_property("valignment", "center")
            textoverlay.set_property("halignment", "left")
            if video_config.height:
                textoverlay.set_property("deltay", -(video_config.height / 10))
            else:
                textoverlay.set_property("deltay", -50)
            textoverlay.set_property("text", "%s %sx%s" % (self.config.title,
                    video_config.width, video_config.height))
        else:
            textoverlay.set_property('silent', True)
        if self.config.overlay_timestamps:
            timeoverlay.set_property("font-desc", "DejaVu Sans Mono, 15")
            timeoverlay.set_property("valignment", "center")
            timeoverlay.set_property("halignment", "left")
            timeoverlay
        else:
            timeoverlay.set_property('silent', True)

        inpad = Gst.GhostPad.new('sink', scale.get_static_pad('sink'))
        outpad = Gst.GhostPad.new('src', muxer.get_static_pad('src'))
        videoencodebin.add_pad(inpad)
        videoencodebin.add_pad(outpad)
        return videoencodebin

    def _create_audio_encode_bin(self, audio_config):
        audioencodebin = Gst.Bin()
        if audio_config.codec == 'AAC':
            encoder = Gst.ElementFactory.make("faac", None)
            encoder.set_property('bitrate', audio_config.bitrate * 1000)
        else:
            raise Exception ("Unknown encoder %s", audio_config.codec)
        audioconvert = Gst.ElementFactory.make("audioconvert", None)
        audioresample = Gst.ElementFactory.make("audioresample", None)
        incapsfilter = Gst.ElementFactory.make("capsfilter", None)
        muxer = Gst.ElementFactory.make("mp4dashmux", None)

        caps_str = 'audio/x-raw'
        for f in ['rate', 'channels']:
            v = getattr(audio_config, f)
            if v is not None:
                caps_str += ',%s=%s' % (f, v)
        incaps = Gst.Caps.from_string(caps_str)
        incapsfilter.set_property('caps', incaps)

        elements = [audioconvert, audioresample, incapsfilter, encoder, muxer]
        for e in elements:
            audioencodebin.add(e)
        for i in range(len(elements) - 1):
            elements[i].link(elements[i+1])

        inpad = Gst.GhostPad.new('sink', audioconvert.get_static_pad('sink'))
        outpad = Gst.GhostPad.new('src', muxer.get_static_pad('src'))
        audioencodebin.add_pad(inpad)
        audioencodebin.add_pad(outpad)
        return audioencodebin

    def _add_encoding_branches(self, tee, streams, create_func):
        for stream_config in streams:
            encoder = create_func(stream_config)
            self.pipeline.add(encoder)
            t = Gst.ElementFactory.find("dashsink").get_static_pad_templates()
            t = t[0].get()
            name = stream_config.name
            i = 0
            while name in self.pad_names:
                i += 1
                name = '%s_%s' % (stream_config.name, i)
            t.name_template = name
            self.pad_names.append(name)
            sinkpad = self.dashsink.request_pad(t, name, None)
            tee.get_request_pad('src_%u').link(encoder.get_static_pad('sink'))
            encoder.get_static_pad('src').link(sinkpad)
            encoder.sync_state_with_parent()
            print "Adding new output %s" % stream_config

    def _on_pad_added(self, decodebin, pad):
        caps = pad.query_caps(None)
        name = caps.get_structure(0).get_name()
        if 'video' in name:
            tee = Gst.ElementFactory.make("tee", None)
            self.pipeline.add(tee)
            pad.link(tee.get_static_pad("sink"))
            tee.sync_state_with_parent()
            self._add_encoding_branches(tee,
                    self.config.video_streams,
                    self._create_video_encode_bin)
        elif 'audio' in name:
            tee = Gst.ElementFactory.make("tee", None)
            self.pipeline.add(tee)
            pad.link(tee.get_static_pad("sink"))
            tee.sync_state_with_parent()
            self._add_encoding_branches(tee, self.config.audio_streams,
                    self._create_audio_encode_bin)
        return None
