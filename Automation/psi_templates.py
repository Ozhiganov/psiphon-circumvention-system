﻿#!/usr/bin/python
# coding=utf-8
#
# Copyright (c) 2011, Psiphon Inc.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import yaml

LANGUAGES = [
    'en',
    'fa',
    'ar',
    'zh',
    'uz@cyrillic',
    'uz@Latn',
    'ru',
    'kk',
    'az',
    'tk',
    'th',
    'ug@Latn'
]

def get_language_string(language, key):
    path = os.path.join('.', 'TemplateStrings', language + '.yaml')
    with open(path) as f:
        str = yaml.load(f.read())[language][key]
    # Assumes strings have one {0} format specifier to receive the language name
    # Other format specifiers, to be substituted later, should be escaped: {{N}}
    return str.format(language)

def get_all_languages_string(key):
    return ''.join([get_language_string(language, key) for language in LANGUAGES])

def get_tweet_message(s3_bucket_name):
    bucket_root_url = 'https://s3.amazonaws.com/' + s3_bucket_name
    return 'Get Psiphon 3 here: %s/en.html' % (bucket_root_url,)

def get_plaintext_email_content(
        s3_bucket_name):
    bucket_root_url = 'https://s3.amazonaws.com/' + s3_bucket_name
    return get_all_languages_string(
        'plaintext_email_no_attachment').format(bucket_root_url)

def get_html_email_content(
        s3_bucket_name):
    bucket_root_url = 'https://s3.amazonaws.com/' + s3_bucket_name
    return get_all_languages_string(
        'html_email_no_attachment').format(bucket_root_url)

def get_plaintext_attachment_email_content(
        s3_bucket_name,
        windows_attachment_filename,
        android_attachment_filename):
    bucket_root_url = 'https://s3.amazonaws.com/' + s3_bucket_name
    return get_all_languages_string(
        'plaintext_email_with_attachment').format(
            bucket_root_url,
            windows_attachment_filename,
            android_attachment_filename)

def get_html_attachment_email_content(
        s3_bucket_name,
        windows_attachment_filename,
        android_attachment_filename):
    bucket_root_url = 'https://s3.amazonaws.com/' + s3_bucket_name
    return get_all_languages_string(
        'html_email_with_attachment').format(
            bucket_root_url,
            windows_attachment_filename,
            android_attachment_filename)
