# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2014 Germain Z. <germanosz@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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

"""Tests for weechat-vimode. Uses a gvim instance as a server to compare the
behavior of our custom implementation to vim's.

Note that a full test takes a fair bit of time.

Usage:
    python2 py.test
"""


from mock import Mock
import subprocess
import sys
import time

sys.modules['weechat'] = Mock()

import vimode


SERVER_NAME = "weechat-vimode-test"
TEST_LINES = ["    This is a test! Hello! ",
              " !olleH !tset a si sihT    ",
              # I don't think those are necessary to support in real life
              # usage (if the above tests pass), but it would be nice to have
              # 100% support if it's  possible without writing a parser from
              # scratch.
              "!?!?#?!#l;l;3l;14l;`4\\!124%*)^)!#^",
              "^#!)^)*%421!\\4`;l41;l3;l;l#!?#?!?!",
              "^#!)^\")*%421!\\4`;l'1;l3;';l#!?#?!?\"!",
              "^#!)^)*%\"4'1!\\4`;l41;l3;l;l#!?\"#'!?!"]


def vim_send(keys):
    """Send {keys} to vim server."""
    subprocess.Popen(["vim", "--servername", SERVER_NAME, "--remote-send",
                      keys], stdout=subprocess.PIPE).wait()

def vim_expr(expr):
    """Evaluate {expr} in vim server."""
    subprocess.Popen(["vim", "--servername", SERVER_NAME, "vim",
                      "--remote-expr", expr], stdout=subprocess.PIPE).wait()

def vim_get_cur():
    """Get the column of the cursor on the vim server."""
    process = subprocess.Popen(["vim", "--servername", SERVER_NAME,
                                "--remote-expr", "col('.')"],
                               stdout=subprocess.PIPE)
    out = process.communicate()[0].strip()
    return int(out)

def test_motion(motion_func, motion_keys):
    """Compare a custom function's behavior to the vim server's to test it."""
    count = 1
    for line in TEST_LINES:
        # Clear the buffer and insert our test line.
        vim_send("<Esc>ggdGi{}<Esc>".format(line))
        print(("• Testing motion \033[33m{}\033[0m with data "
               "\033[33m\"{}\"\033[0m…").format(motion_keys, line))
        # Check the behavior of our function for each possible cursor position.
        for cur in range(0, len(line)):
            # Get the cursor position, as returned by our function.
            got, _, catching = motion_func(line, cur, count)
            got = min(len(line), got + 1)
            # If it's a catching motion (e.g. "f"), it's not done yet.
            if catching:
                vimode.catching_keys_data['keys'] = "a"
                vimode.catching_keys_data['amount'] = 0
                callback = vimode.catching_keys_data['callback']
                getattr(vimode, callback)()
                got, _, _ = motion_func(line, cur, count)
                got = min(len(line), cur + 1 if got == -1 else got + 1)

            # Set the cursor's position on the vim server.
            vim_expr("setpos('.', [0, 1, {}, 0])".format(cur + 1))
            # Do the motion on the vim server.
            vim_send(motion_keys)
            # Complete the motion if it's catching (e.g. "f").
            if catching:
                vim_send("a")
            # Get the cursor's positon on the vim server.
            expected = vim_get_cur()
            # Print errors, if any.
            if got != expected:
                print("    cur: {}, count: {}: \033[31m{} ≠ {}\033[0m".format(
                    cur, count, got, expected))


# Start a vim server (we use gvim because it forks directly).
subprocess.Popen(["gvim", "--servername", SERVER_NAME]).wait()
time.sleep(0.5)  # To make sure it's completely ready.

# Test each of weechat-vimode's custom motion implementations.
for motion in vimode.VI_MOTIONS:
    # Get the function's name (special characters need to be replaced; for
    # example, "^"'s function is called "motion_carret" and not "motion_^").
    if motion in vimode.SPECIAL_CHARS:
        func = "motion_{}".format(vimode.SPECIAL_CHARS[motion])
    else:
        func = "motion_{}".format(motion)
    # Test it!
    test_motion(getattr(vimode, func), motion)

# Exit the vim server.
vim_send("<Esc>ZQ")
