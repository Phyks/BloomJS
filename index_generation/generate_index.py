#!/usr/bin/env python3

"""
Inspired by
http://www.stavros.io/posts/bloom-filter-search-engine/?print


You have to install the numpy python module for bloom to work.
"""

import bloom
import json
import os
import re
import stemmer
import struct
import sys

from lxml import html


def list_directory(path):
    """Recursively list all files in a given directory."""
    files_list = []
    for root, dirs, files in os.walk(path):
        for i in files:
            files_list.append(os.path.join(root, i))
    return files_list


def remove_common_words(words):
    """Removes all words that are less than 3 characters long."""
    returned = [word for word in words if len(word) > 3]
    return returned


if __name__ == "__main__":
    error_rate = 0.1

    os.chdir(os.path.dirname(sys.argv[0]))
    samples = list_directory("../samples/")
    pages = []
    filters = []
    p = stemmer.PorterStemmer()

    for sample in samples:
        with open(sample, 'r') as sample_fh:
            content = sample_fh.read()

        # Get text from HTML content
        words = html.fromstring(content).text_content().replace("\n", "")
        words = re.findall(r"[\w]+", words)
        # Remove all punctuation etc., convert words to lower and delete
        # duplicates
        words = list(set([word.lower() for word in words]))

        # Remove common words
        words = remove_common_words(words)
        # Stemming to reduce the number of words
        words = list(set([p.stem(word, 0, len(word)-1) for word in words]))

        tmp_filter = bloom.BloomFilter(capacity=len(words),
                                       error_rate=error_rate)
        for word in words:
            tmp_filter.add(word)

        filters.append(tmp_filter.buckets)

        pages.append({"title": re.search(r"@title=(.*)\n", content).group(1),
                      "url": sample[3:]})

    # First Int32 is length
    filters_to_write = struct.pack("<i", len(filters))
    # Then comes the length of each filter
    for i in filters:
        filters_to_write += struct.pack("<i", len(i))
    # Finally comes the filters themselves
    for i in filters:
        filters_to_write += struct.pack("<%di" % len(i), *i)

    # Write everything
    with open("../data/filters", "wb") as index_fh:
        index_fh.write(filters_to_write)

    with open("../data/pages.json", "w") as pages_fh:
        pages_fh.write(json.dumps({"index": pages}))
