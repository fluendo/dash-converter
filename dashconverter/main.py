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

try:
    import argparse
except ImportError, e:
    print "Could not import argparse. Try installing it with "\
          "'sudo easy_install argparse"
    raise e

import sys
import os

import config
import dashconverter

description = ('Converts multimedia files to DASH format using GStreamer')


class Main(object):

    def __init__(self, args):
        self.create_parser()
        self.parse_arguments(args)
        self.load_config()
        self.start_conversion()

    def log_error(self, msg, print_usage=False):
        ''' Log an error and exit '''
        if print_usage:
            self.parser.print_usage()
        sys.exit(msg)

    def create_parser(self):
        ''' Creates the arguments parser '''
        self.parser = argparse.ArgumentParser(description=description)
        self.parser.add_argument('input_file', type=str,
                help='Input file to convert')
        self.parser.add_argument('-c', '--config', type=str, default=None,
                help='Output format configuration file')

    def parse_arguments(self, args):
        ''' Parse the command line arguments '''
        self.args = self.parser.parse_args(args)

    def load_config(self):
        ''' Load the configuration '''
        self.output_config = config.Config()
        if (self.args.config):
            self.output_config.load(self.args.config)

    def start_conversion(self):
        input_file = self.args.input_file
        if os.path.isfile(input_file):
            input_file = 'file://%s' % os.path.abspath(input_file)
        converter = dashconverter.DashConverter(input_file, self.output_config)
        converter.start()


def main():
    Main(sys.argv[1:])


if __name__ == "__main__":
    main()

