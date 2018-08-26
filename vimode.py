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

#
# Add vi/vim-like modes to WeeChat.
#


import csv
import json
import os
import re
import subprocess
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import time

import weechat


# Script info.
# ============

SCRIPT_NAME = "vimode"
SCRIPT_AUTHOR = "GermainZ <germanosz@gmail.com>"
SCRIPT_VERSION = "0.7"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = ("Add vi/vim-like modes and keybindings to WeeChat.")


# Global variables.
# =================

# General.
# --------

# Halp! Halp! Halp!
GITHUB_BASE = "https://github.com/GermainZ/weechat-vimode/blob/master/"
README_URL = GITHUB_BASE + "README.md"
FAQ_KEYBINDINGS = GITHUB_BASE + "FAQ.md#problematic-key-bindings"
FAQ_ESC = GITHUB_BASE + "FAQ.md#esc-key-not-being-detected-instantly"

# Holds the text of the tab-completions for the command-line mode.
cmd_compl_text = ""
# Holds the original text of the command-line mode, used for completion.
cmd_text_orig = None
# Index of current suggestion, used for completion.
cmd_compl_pos = 0
# Used for command-line mode history.
cmd_history = []
cmd_history_index = 0
# Used to store the content of the input line when going into COMMAND mode.
input_line_backup = {}
# Mode we're in. One of INSERT, NORMAL, REPLACE, COMMAND or SEARCH.
# SEARCH is only used if search_vim is enabled.
mode = "INSERT"
# Holds normal commands (e.g. "dd").
vi_buffer = ""
# See `cb_key_combo_default()`.
esc_pressed = 0
# See `cb_key_pressed()`.
last_signal_time = 0
# See `start_catching_keys()` for more info.
catching_keys_data = {'amount': 0}
# Used for ; and , to store the last f/F/t/T motion.
last_search_motion = {'motion': None, 'data': None}
# Used for undo history.
undo_history = {}
undo_history_index = {}
# Holds mode colors (loaded from vimode_settings).
mode_colors = {}

# Script options.
vimode_settings = {
    'no_warn': ("off", ("don't warn about problematic keybindings and "
                        "tmux/screen")),
    'copy_clipboard_cmd': ("xclip -selection c",
                           ("command used to copy to clipboard; must read "
                            "input from stdin")),
    'paste_clipboard_cmd': ("xclip -selection c -o",
                            ("command used to paste clipboard; must output "
                             "content to stdout")),
    'imap_esc': ("", ("use alternate mapping to enter Normal mode while in "
                      "Insert mode; having it set to 'jk' is similar to "
                      "`:imap jk <Esc>` in vim")),
    'imap_esc_timeout': ("1000", ("time in ms to wait for the imap_esc "
                                  "sequence to complete")),
    'search_vim': ("off", ("allow n/N usage after searching (requires an extra"
                           " <Enter> to return to normal mode)")),
    'user_mappings': ("", ("see the `:nmap` command in the README for more "
                           "info; please do not modify this field manually "
                           "unless you know what you're doing")),
    'mode_indicator_prefix': ("", "prefix for the bar item mode_indicator"),
    'mode_indicator_suffix': ("", "suffix for the bar item mode_indicator"),
    'mode_indicator_normal_color': ("white",
                                    "color for mode indicator in Normal mode"),
    'mode_indicator_normal_color_bg': ("gray",
                                       ("background color for mode indicator "
                                        "in Normal mode")),
    'mode_indicator_insert_color': ("white",
                                    "color for mode indicator in Insert mode"),
    'mode_indicator_insert_color_bg': ("blue",
                                       ("background color for mode indicator "
                                        "in Insert mode")),
    'mode_indicator_replace_color': ("white",
                                     "color for mode indicator in Replace mode"),
    'mode_indicator_replace_color_bg': ("red",
                                        ("background color for mode indicator "
                                         "in Replace mode")),
    'mode_indicator_cmd_color': ("white",
                                 "color for mode indicator in Command mode"),
    'mode_indicator_cmd_color_bg': ("cyan",
                                    ("background color for mode indicator in "
                                     "Command mode")),
    'mode_indicator_search_color': ("white",
                                    "color for mode indicator in Search mode"),
    'mode_indicator_search_color_bg': ("magenta",
                                       ("background color for mode indicator "
                                        "in Search mode")),
    'line_number_prefix': ("", "prefix for line numbers"),
    'line_number_suffix': (" ", "suffix for line numbers")
}


# Regex patterns.
# ---------------

WHITESPACE = re.compile(r"\s")
IS_KEYWORD = re.compile(r"[a-zA-Z0-9_@À-ÿ]")
REGEX_MOTION_LOWERCASE_W = re.compile(r"\b\S|(?<=\s)\S")
REGEX_MOTION_UPPERCASE_W = re.compile(r"(?<=\s)\S")
REGEX_MOTION_UPPERCASE_E = re.compile(r"\S(?!\S)")
REGEX_MOTION_UPPERCASE_B = REGEX_MOTION_UPPERCASE_E
REGEX_MOTION_G_UPPERCASE_E = REGEX_MOTION_UPPERCASE_W
REGEX_MOTION_CARRET = re.compile(r"\S")
REGEX_INT = r"[0-9]"
REGEX_MAP_KEYS_1 = {
    re.compile("<([^>]*-)Left>", re.IGNORECASE): '<\\1\x01[[D>',
    re.compile("<([^>]*-)Right>", re.IGNORECASE): '<\\1\x01[[C>',
    re.compile("<([^>]*-)Up>", re.IGNORECASE): '<\\1\x01[[A>',
    re.compile("<([^>]*-)Down>", re.IGNORECASE): '<\\1\x01[[B>',
    re.compile("<Left>", re.IGNORECASE): '\x01[[D',
    re.compile("<Right>", re.IGNORECASE): '\x01[[C',
    re.compile("<Up>", re.IGNORECASE): '\x01[[A',
    re.compile("<Down>", re.IGNORECASE): '\x01[[B'
}
REGEX_MAP_KEYS_2 = {
    re.compile(r"<C-([^>]*)>", re.IGNORECASE): '\x01\\1',
    re.compile(r"<M-([^>]*)>", re.IGNORECASE): '\x01[\\1'
}

# Regex used to detect problematic keybindings.
# For example: meta-wmeta-s is bound by default to ``/window swap``.
#    If the user pressed Esc-w, WeeChat will detect it as meta-w and will not
#    send any signal to `cb_key_combo_default()` just yet, since it's the
#    beginning of a known key combo.
#    Instead, `cb_key_combo_default()` will receive the Esc-ws signal, which
#    becomes "ws" after removing the Esc part, and won't know how to handle it.
REGEX_PROBLEMATIC_KEYBINDINGS = re.compile(r"meta-\w(meta|ctrl)")


# Vi commands.
# ------------

def cmd_nmap(args):
    """Add a user-defined key mapping.

    Some (but not all) vim-like key codes are supported to simplify things for
    the user: <Up>, <Down>, <Left>, <Right>, <C-...> and <M-...>.

    See Also:
        `cmd_unmap()`.
    """
    args = args.strip()
    if not args:
        mappings = vimode_settings['user_mappings']
        if mappings:
            weechat.prnt("", "User-defined key mappings:")
            for key, mapping in mappings.items():
                weechat.prnt("", "{} -> {}".format(key, mapping))
        else:
            weechat.prnt("", "nmap: no mapping found.")
    elif not " " in args:
        weechat.prnt("", "nmap syntax -> :nmap {lhs} {rhs}")
    else:
        key, mapping = args.split(" ", 1)
        # First pass of replacements. We perform two passes as a simple way to
        # avoid incorrect replacements due to dictionaries not being
        # insertion-ordered prior to Python 3.7.
        for regex, repl in REGEX_MAP_KEYS_1.items():
            key = regex.sub(repl, key)
            mapping = regex.sub(repl, mapping)
        # Second pass of replacements.
        for regex, repl in REGEX_MAP_KEYS_2.items():
            key = regex.sub(repl, key)
            mapping = regex.sub(repl, mapping)
        mappings = vimode_settings['user_mappings']
        mappings[key] = mapping
        weechat.config_set_plugin('user_mappings', json.dumps(mappings))
        vimode_settings['user_mappings'] = mappings

def cmd_nunmap(args):
    """Remove a user-defined key mapping.

    See Also:
        `cmd_map()`.
    """
    args = args.strip()
    if not args:
        weechat.prnt("", "nunmap syntax -> :unmap {lhs}")
    else:
        key = args
        for regex, repl in REGEX_MAP_KEYS_1.items():
            key = regex.sub(repl, key)
        for regex, repl in REGEX_MAP_KEYS_2.items():
            key = regex.sub(repl, key)
        mappings = vimode_settings['user_mappings']
        if key in mappings:
            del mappings[key]
            weechat.config_set_plugin('user_mappings', json.dumps(mappings))
            vimode_settings['user_mappings'] = mappings
        else:
            weechat.prnt("", "nunmap: No such mapping")

# See Also: `cb_exec_cmd()`.
VI_COMMAND_GROUPS = {('h', 'help'): "/help",
                     ('qa', 'qall', 'quita', 'quitall'): "/exit",
                     ('q', 'quit'): "/close",
                     ('w', 'write'): "/save",
                     ('bN', 'bNext', 'bp', 'bprevious'): "/buffer -1",
                     ('bn', 'bnext'): "/buffer +1",
                     ('bd', 'bdel', 'bdelete'): "/close",
                     ('b#',): "/input jump_last_buffer_displayed",
                     ('b', 'bu', 'buf', 'buffer'): "/buffer",
                     ('sp', 'split'): "/window splith",
                     ('vs', 'vsplit'): "/window splitv",
                     ('nm', 'nmap'): cmd_nmap,
                     ('nun', 'nunmap'): cmd_nunmap}

VI_COMMANDS = dict()
for T, v in VI_COMMAND_GROUPS.items():
    VI_COMMANDS.update(dict.fromkeys(T, v))


# Vi operators.
# -------------

# Each operator must have a corresponding function, called "operator_X" where
# X is the operator. For example: `operator_c()`.
VI_OPERATORS = ["c", "d", "y"]


# Vi motions.
# -----------

# Vi motions. Each motion must have a corresponding function, called
# "motion_X" where X is the motion (e.g. `motion_w()`).
# See Also: `SPECIAL_CHARS`.
VI_MOTIONS = ["w", "e", "b", "^", "$", "h", "l", "W", "E", "B", "f", "F", "t",
              "T", "ge", "gE", "0"]

# Special characters for motions. The corresponding function's name is
# converted before calling. For example, "^" will call `motion_carret` instead
# of `motion_^` (which isn't allowed because of illegal characters).
SPECIAL_CHARS = {'^': "carret",
                 '$': "dollar"}


# Methods for vi operators, motions and key bindings.
# ===================================================

# Documented base examples:
# -------------------------

def operator_base(buf, input_line, pos1, pos2, overwrite):
    """Operator method example.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        pos1 (int): the starting position of the motion.
        pos2 (int): the ending position of the motion.
        overwrite (bool, optional): whether the character at the cursor's new
            position should be overwritten or not (for inclusive motions).
            Defaults to False.

    Notes:
        Should be called "operator_X", where X is the operator, and defined in
        `VI_OPERATORS`.
        Must perform actions (e.g. modifying the input line) on its own,
        using the WeeChat API.

    See Also:
        For additional examples, see `operator_d()` and
        `operator_y()`.
    """
    # Get start and end positions.
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    # Print the text the operator should go over.
    weechat.prnt("", "Selection: %s" % input_line[start:end])

def motion_base(input_line, cur, count):
    """Motion method example.

    Args:
        input_line (str): the content of the input line.
        cur (int): the position of the cursor.
        count (int): the amount of times to multiply or iterate the action.

    Returns:
        A tuple containing three values:
            int: the new position of the cursor.
            bool: True if the motion is inclusive, False otherwise.
            bool: True if the motion is catching, False otherwise.
                See `start_catching_keys()` for more info on catching motions.

    Notes:
        Should be called "motion_X", where X is the motion, and defined in
        `VI_MOTIONS`.
        Must not modify the input line directly.

    See Also:
        For additional examples, see `motion_w()` (normal motion) and
        `motion_f()` (catching motion).
    """
    # Find (relative to cur) position of next number.
    pos = get_pos(input_line, REGEX_INT, cur, True, count)
    # Return the new (absolute) cursor position.
    # This motion is exclusive, so overwrite is False.
    return cur + pos, False

def key_base(buf, input_line, cur, count):
    """Key method example.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        cur (int): the position of the cursor.
        count (int): the amount of times to multiply or iterate the action.

    Notes:
        Should be called `key_X`, where X represents the key(s), and defined
        in `VI_KEYS`.
        Must perform actions on its own (using the WeeChat API).

    See Also:
        For additional examples, see `key_a()` (normal key) and
        `key_r()` (catching key).
    """
    # Key was pressed. Go to Insert mode (similar to "i").
    set_mode("INSERT")


# Operators:
# ----------

def operator_d(buf, input_line, pos1, pos2, overwrite=False):
    """Delete text from `pos1` to `pos2` from the input line.

    If `overwrite` is set to True, the character at the cursor's new position
    is removed as well (the motion is inclusive).

    See Also:
        `operator_base()`.
    """
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    if overwrite:
        end += 1
    input_line = list(input_line)
    del input_line[start:end]
    input_line = "".join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, pos1)

def operator_c(buf, input_line, pos1, pos2, overwrite=False):
    """Delete text from `pos1` to `pos2` from the input and enter Insert mode.

    If `overwrite` is set to True, the character at the cursor's new position
    is removed as well (the motion is inclusive.)

    See Also:
        `operator_base()`.
    """
    operator_d(buf, input_line, pos1, pos2, overwrite)
    set_mode("INSERT")

def operator_y(buf, input_line, pos1, pos2, _):
    """Yank text from `pos1` to `pos2` from the input line.

    See Also:
        `operator_base()`.
    """
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    cmd = vimode_settings['copy_clipboard_cmd']
    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    proc.communicate(input=input_line[start:end].encode())


# Motions:
# --------

def motion_0(input_line, cur, count):
    """Go to the first character of the line.

    See Also;
        `motion_base()`.
    """
    return 0, False, False

def motion_w(input_line, cur, count):
    """Go `count` words forward and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_LOWERCASE_W, cur, True, count)
    if pos == -1:
        return len(input_line), False, False
    return cur + pos, False, False

def motion_W(input_line, cur, count):
    """Go `count` WORDS forward and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_W, cur, True, count)
    if pos == -1:
        return len(input_line), False, False
    return cur + pos, False, False

def motion_e(input_line, cur, count):
    """Go to the end of `count` words and return position.

    See Also:
        `motion_base()`.
    """
    for _ in range(max(1, count)):
        found = False
        pos = cur
        for pos in range(cur + 1, len(input_line) - 1):
            # Whitespace, keep going.
            if WHITESPACE.match(input_line[pos]):
                pass
            # End of sequence made from 'iskeyword' characters only,
            # or end of sequence made from non 'iskeyword' characters only.
            elif ((IS_KEYWORD.match(input_line[pos]) and
                   (not IS_KEYWORD.match(input_line[pos + 1]) or
                    WHITESPACE.match(input_line[pos + 1]))) or
                  (not IS_KEYWORD.match(input_line[pos]) and
                   (IS_KEYWORD.match(input_line[pos + 1]) or
                    WHITESPACE.match(input_line[pos + 1])))):
                found = True
                cur = pos
                break
        # We're at the character before the last and we still found nothing.
        # Go to the last character.
        if not found:
            cur = pos + 1
    return cur, True, False

def motion_E(input_line, cur, count):
    """Go to the end of `count` WORDS and return cusor position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_E, cur, True, count)
    if pos == -1:
        return len(input_line), False, False
    return cur + pos, True, False

def motion_b(input_line, cur, count):
    """Go `count` words backwards and return position.

    See Also:
        `motion_base()`.
    """
    # "b" is just "e" on inverted data (e.g. "olleH" instead of "Hello").
    pos_inv = motion_e(input_line[::-1], len(input_line) - cur - 1, count)[0]
    pos = len(input_line) - pos_inv - 1
    return pos, True, False

def motion_B(input_line, cur, count):
    """Go `count` WORDS backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_UPPERCASE_B, new_cur,
                  count=count)
    if pos == -1:
        return 0, False, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True, False

def motion_ge(input_line, cur, count):
    """Go to end of `count` words backwards and return position.

    See Also:
        `motion_base()`.
    """
    # "ge is just "w" on inverted data (e.g. "olleH" instead of "Hello").
    pos_inv = motion_w(input_line[::-1], len(input_line) - cur - 1, count)[0]
    pos = len(input_line) - pos_inv - 1
    return pos, True, False

def motion_gE(input_line, cur, count):
    """Go to end of `count` WORDS backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur - 1
    pos = get_pos(input_line[::-1], REGEX_MOTION_G_UPPERCASE_E, new_cur,
                  True, count)
    if pos == -1:
        return 0, False, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True, False

def motion_h(input_line, cur, count):
    """Go `count` characters to the left and return position.

    See Also:
        `motion_base()`.
    """
    return max(0, cur - max(count, 1)), False, False

def motion_l(input_line, cur, count):
    """Go `count` characters to the right and return position.

    See Also:
        `motion_base()`.
    """
    return cur + max(count, 1), False, False

def motion_carret(input_line, cur, count):
    """Go to first non-blank character of line and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_CARRET, 0)
    return pos, False, False

def motion_dollar(input_line, cur, count):
    """Go to end of line and return position.

    See Also:
        `motion_base()`.
    """
    pos = len(input_line)
    return pos, False, False

def motion_f(input_line, cur, count):
    """Go to `count`'th occurence of character and return position.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_f", input_line, cur, count)

def cb_motion_f(update_last=True):
    """Callback for `motion_f()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'], True,
                  catching_keys_data['count'])
    catching_keys_data['new_cur'] = max(0, pos) + catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': "f", 'data': pattern}
    cb_key_combo_default(None, None, "")

def motion_F(input_line, cur, count):
    """Go to `count`'th occurence of char to the right and return position.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_F", input_line, cur, count)

def cb_motion_F(update_last=True):
    """Callback for `motion_F()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    cur = len(catching_keys_data['input_line']) - catching_keys_data['cur']
    pos = get_pos(catching_keys_data['input_line'][::-1],
                  re.escape(pattern),
                  cur,
                  False,
                  catching_keys_data['count'])
    catching_keys_data['new_cur'] = catching_keys_data['cur'] - max(0, pos + 1)
    if update_last:
        last_search_motion = {'motion': "F", 'data': pattern}
    cb_key_combo_default(None, None, "")

def motion_t(input_line, cur, count):
    """Go to `count`'th occurence of char and return position.

    The position returned is the position of the character to the left of char.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_t", input_line, cur, count)

def cb_motion_t(update_last=True):
    """Callback for `motion_t()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'] + 1,
                  True, catching_keys_data['count'])
    pos += 1
    if pos > 0:
        catching_keys_data['new_cur'] = pos + catching_keys_data['cur'] - 1
    else:
        catching_keys_data['new_cur'] = catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': "t", 'data': pattern}
    cb_key_combo_default(None, None, "")

def motion_T(input_line, cur, count):
    """Go to `count`'th occurence of char to the left and return position.

    The position returned is the position of the character to the right of
    char.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_T", input_line, cur, count)

def cb_motion_T(update_last=True):
    """Callback for `motion_T()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'][::-1], re.escape(pattern),
                  (len(catching_keys_data['input_line']) -
                   (catching_keys_data['cur'] + 1)) + 1,
                  True, catching_keys_data['count'])
    pos += 1
    if pos > 0:
        catching_keys_data['new_cur'] = catching_keys_data['cur'] - pos + 1
    else:
        catching_keys_data['new_cur'] = catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': "T", 'data': pattern}
    cb_key_combo_default(None, None, "")


# Keys:
# -----

def key_cc(buf, input_line, cur, count):
    """Delete line and start Insert mode.

    See Also:
        `key_base()`.
    """
    weechat.command("", "/input delete_line")
    set_mode("INSERT")

def key_C(buf, input_line, cur, count):
    """Delete from cursor to end of line and start Insert mode.

    See Also:
        `key_base()`.
    """
    weechat.command("", "/input delete_end_of_line")
    set_mode("INSERT")

def key_yy(buf, input_line, cur, count):
    """Yank line.

    See Also:
        `key_base()`.
    """
    cmd = vimode_settings['copy_clipboard_cmd']
    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    proc.communicate(input=input_line.encode())

def key_p(buf, input_line, cur, count):
    """Paste text.

    See Also:
        `key_base()`.
    """
    cmd = vimode_settings['paste_clipboard_cmd']
    weechat.hook_process(cmd, 10 * 1000, "cb_key_p", weechat.current_buffer())

def cb_key_p(data, command, return_code, output, err):
    """Callback for fetching clipboard text and pasting it."""
    buf = ""
    this_buffer = data
    if output != "":
        buf += output.strip()
    if return_code == 0:
        my_input = weechat.buffer_get_string(this_buffer, "input")
        pos = weechat.buffer_get_integer(this_buffer, "input_pos")
        my_input = my_input[:pos] + buf + my_input[pos:]
        pos += len(buf)
        weechat.buffer_set(this_buffer, "input", my_input)
        weechat.buffer_set(this_buffer, "input_pos", str(pos))
    return weechat.WEECHAT_RC_OK

def key_i(buf, input_line, cur, count):
    """Start Insert mode.

    See Also:
        `key_base()`.
    """
    set_mode("INSERT")

def key_a(buf, input_line, cur, count):
    """Move cursor one character to the right and start Insert mode.

    See Also:
        `key_base()`.
    """
    set_cur(buf, input_line, cur + 1, False)
    set_mode("INSERT")

def key_A(buf, input_line, cur, count):
    """Move cursor to end of line and start Insert mode.

    See Also:
        `key_base()`.
    """
    set_cur(buf, input_line, len(input_line), False)
    set_mode("INSERT")

def key_I(buf, input_line, cur, count):
    """Move cursor to first non-blank character and start Insert mode.

    See Also:
        `key_base()`.
    """
    pos, _, _ = motion_carret(input_line, cur, 0)
    set_cur(buf, input_line, pos)
    set_mode("INSERT")

def key_G(buf, input_line, cur, count):
    """Scroll to specified line or bottom of buffer.

    See Also:
        `key_base()`.
    """
    if count > 0:
        # This is necessary to prevent weird scroll jumps.
        weechat.command("", "/window scroll_top")
        weechat.command("", "/window scroll %s" % (count - 1))
    else:
        weechat.command("", "/window scroll_bottom")

def key_r(buf, input_line, cur, count):
    """Replace `count` characters under the cursor.

    See Also:
        `key_base()`.
    """
    start_catching_keys(1, "cb_key_r", input_line, cur, count, buf)

def cb_key_r():
    """Callback for `key_r()`.

    See Also:
        `start_catching_keys()`.
    """
    global catching_keys_data
    input_line = list(catching_keys_data['input_line'])
    count = max(catching_keys_data['count'], 1)
    cur = catching_keys_data['cur']
    if cur + count <= len(input_line):
        for _ in range(count):
            input_line[cur] = catching_keys_data['keys']
            cur += 1
        input_line = "".join(input_line)
        weechat.buffer_set(catching_keys_data['buf'], "input", input_line)
        set_cur(catching_keys_data['buf'], input_line, cur - 1)
    catching_keys_data = {'amount': 0}

def key_R(buf, input_line, cur, count):
    """Start Replace mode.

    See Also:
        `key_base()`.
    """
    set_mode("REPLACE")

def key_tilda(buf, input_line, cur, count):
    """Switch the case of `count` characters under the cursor.

    See Also:
        `key_base()`.
    """
    input_line = list(input_line)
    count = max(1, count)
    while count and cur < len(input_line):
        input_line[cur] = input_line[cur].swapcase()
        count -= 1
        cur += 1
    input_line = "".join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, cur)

def key_alt_j(buf, input_line, cur, count):
    """Go to WeeChat buffer.

    Called to preserve WeeChat's alt-j buffer switching.

    This is only called when alt-j<num> is pressed after pressing Esc, because
    \x01\x01j is received in key_combo_default which becomes \x01j after
    removing the detected Esc key.
    If Esc isn't the last pressed key, \x01j<num> is directly received in
    key_combo_default.
    """
    start_catching_keys(2, "cb_key_alt_j", input_line, cur, count)

def cb_key_alt_j():
    """Callback for `key_alt_j()`.

    See Also:
        `start_catching_keys()`.
    """
    global catching_keys_data
    weechat.command("", "/buffer " + catching_keys_data['keys'])
    catching_keys_data = {'amount': 0}

def key_semicolon(buf, input_line, cur, count, swap=False):
    """Repeat last f, t, F, T `count` times.

    Args:
        swap (bool, optional): if True, the last motion will be repeated in the
            opposite direction (e.g. "f" instead of "F"). Defaults to False.

    See Also:
        `key_base()`.
    """
    global catching_keys_data, vi_buffer
    catching_keys_data = ({'amount': 0,
                           'input_line': input_line,
                           'cur': cur,
                           'keys': last_search_motion['data'],
                           'count': count,
                           'new_cur': 0,
                           'buf': buf})
    # Swap the motion's case if called from key_comma.
    if swap:
        motion = last_search_motion['motion'].swapcase()
    else:
        motion = last_search_motion['motion']
    func = "cb_motion_%s" % motion
    vi_buffer = motion
    globals()[func](False)

def key_comma(buf, input_line, cur, count):
    """Repeat last f, t, F, T in opposite direction `count` times.

    See Also:
        `key_base()`.
    """
    key_semicolon(buf, input_line, cur, count, True)

def key_u(buf, input_line, cur, count):
    """Undo change `count` times.

    See Also:
        `key_base()`.
    """
    buf = weechat.current_buffer()
    if buf not in undo_history:
        return
    for _ in range(max(count, 1)):
        if undo_history_index[buf] > -len(undo_history[buf]):
            undo_history_index[buf] -= 1
            input_line = undo_history[buf][undo_history_index[buf]]
            weechat.buffer_set(buf, "input", input_line)
        else:
            break

def key_ctrl_r(buf, input_line, cur, count):
    """Redo change `count` times.

    See Also:
        `key_base()`.
    """
    if buf not in undo_history:
        return
    for _ in range(max(count, 1)):
        if undo_history_index[buf] < -1:
            undo_history_index[buf] += 1
            input_line = undo_history[buf][undo_history_index[buf]]
            weechat.buffer_set(buf, "input", input_line)
        else:
            break


# Vi key bindings.
# ================

# String values will be executed as normal WeeChat commands.
# For functions, see `key_base()` for reference.
VI_KEYS = {'j': "/window scroll_down",
           'k': "/window scroll_up",
           'G': key_G,
           'gg': "/window scroll_top",
           'x': "/input delete_next_char",
           'X': "/input delete_previous_char",
           'dd': "/input delete_line",
           'D': "/input delete_end_of_line",
           'cc': key_cc,
           'C': key_C,
           'i': key_i,
           'a': key_a,
           'A': key_A,
           'I': key_I,
           'yy': key_yy,
           'p': key_p,
           'gt': "/buffer -1",
           'K': "/buffer -1",
           'gT': "/buffer +1",
           'J': "/buffer +1",
           'r': key_r,
           'R': key_R,
           '~': key_tilda,
           'nt': "/bar scroll nicklist * -100%",
           'nT': "/bar scroll nicklist * +100%",
           '\x01[[A': "/input history_previous",
           '\x01[[B': "/input history_next",
           '\x01[[C': "/input move_next_char",
           '\x01[[D': "/input move_previous_char",
           '\x01[[H': "/input move_beginning_of_line",
           '\x01[[F': "/input move_end_of_line",
           '\x01[[5~': "/window page_up",
           '\x01[[6~': "/window page_down",
           '\x01[[3~': "/input delete_next_char",
           '\x01[[2~': key_i,
           '\x01M': "/input return",
           '\x01?': "/input move_previous_char",
           ' ': "/input move_next_char",
           '\x01[j': key_alt_j,
           '\x01[1': "/buffer *1",
           '\x01[2': "/buffer *2",
           '\x01[3': "/buffer *3",
           '\x01[4': "/buffer *4",
           '\x01[5': "/buffer *5",
           '\x01[6': "/buffer *6",
           '\x01[7': "/buffer *7",
           '\x01[8': "/buffer *8",
           '\x01[9': "/buffer *9",
           '\x01[0': "/buffer *10",
           '\x01^': "/input jump_last_buffer_displayed",
           '\x01D': "/window page_down",
           '\x01U': "/window page_up",
           '\x01Wh': "/window left",
           '\x01Wj': "/window down",
           '\x01Wk': "/window up",
           '\x01Wl': "/window right",
           '\x01W=': "/window balance",
           '\x01Wx': "/window swap",
           '\x01Ws': "/window splith",
           '\x01Wv': "/window splitv",
           '\x01Wq': "/window merge",
           ';': key_semicolon,
           ',': key_comma,
           'u': key_u,
           '\x01R': key_ctrl_r}

# Add alt-j<number> bindings.
for i in range(10, 99):
    VI_KEYS['\x01[j%s' % i] = "/buffer %s" % i


# Key handling.
# =============

def cb_key_pressed(data, signal, signal_data):
    """Detect potential Esc presses.

    Alt and Esc are detected as the same key in most terminals. The difference
    is that Alt signal is sent just before the other pressed key's signal.
    We therefore use a timeout (50ms) to detect whether Alt or Esc was pressed.
    """
    global last_signal_time
    last_signal_time = time.time()
    if signal_data == "\x01[":
        # In 50ms, check if any other keys were pressed. If not, it's Esc!
        weechat.hook_timer(50, 0, 1, "cb_check_esc",
                           "{:f}".format(last_signal_time))
    return weechat.WEECHAT_RC_OK

def cb_check_esc(data, remaining_calls):
    """Check if the Esc key was pressed and change the mode accordingly."""
    global esc_pressed, vi_buffer, catching_keys_data
    # Not perfect, would be better to use direct comparison (==) but that only
    # works for py2 and not for py3.
    if abs(last_signal_time - float(data)) <= 0.000001:
        esc_pressed += 1
        if mode == "SEARCH":
            weechat.command("", "/input search_stop_here")
        set_mode("NORMAL")
        # Cancel any current partial commands.
        vi_buffer = ""
        catching_keys_data = {'amount': 0}
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

def cb_key_combo_default(data, signal, signal_data):
    """Eat and handle key events when in Normal mode, if needed.

    The key_combo_default signal is sent when a key combo is pressed. For
    example, alt-k will send the "\x01[k" signal.

    Esc is handled a bit differently to avoid delays, see `cb_key_pressed()`.
    """
    global esc_pressed, vi_buffer, cmd_compl_text, cmd_text_orig, \
           cmd_compl_pos, cmd_history_index

    # If Esc was pressed, strip the Esc part from the pressed keys.
    # Example: user presses Esc followed by i. This is detected as "\x01[i",
    # but we only want to handle "i".
    keys = signal_data
    if esc_pressed or esc_pressed == -2:
        if keys.startswith("\x01[" * esc_pressed):
            # Multiples of 3 seem to "cancel" themselves,
            # e.g. Esc-Esc-Esc-Alt-j-11 is detected as "\x01[\x01[\x01"
            # followed by "\x01[j11" (two different signals).
            if signal_data == "\x01[" * 3:
                esc_pressed = -1  # `cb_check_esc()` will increment it to 0.
            else:
                esc_pressed = 0
        # This can happen if a valid combination is started but interrupted
        # with Esc, such as Ctrl-W→Esc→w which would send two signals:
        # "\x01W\x01[" then "\x01W\x01[w".
        # In that case, we still need to handle the next signal ("\x01W\x01[w")
        # so we use the special value "-2".
        else:
            esc_pressed = -2
        keys = keys.split("\x01[")[-1]  # Remove the "Esc" part(s).
    # Ctrl-Space.
    elif keys == "\x01@":
        set_mode("NORMAL")
        return weechat.WEECHAT_RC_OK_EAT

    # Clear the undo history for this buffer on <Return>.
    if keys == "\x01M":
        buf = weechat.current_buffer()
        clear_undo_history(buf)

    # Detect imap_esc presses if any.
    if mode == "INSERT":
        imap_esc = vimode_settings['imap_esc']
        if not imap_esc:
            return weechat.WEECHAT_RC_OK
        if (imap_esc.startswith(vi_buffer) and
                imap_esc[len(vi_buffer):len(vi_buffer)+1] == keys):
            vi_buffer += keys
            weechat.bar_item_update("vi_buffer")
            weechat.hook_timer(int(vimode_settings['imap_esc_timeout']), 0, 1,
                               "cb_check_imap_esc", vi_buffer)
        elif (vi_buffer and imap_esc.startswith(vi_buffer) and
              imap_esc[len(vi_buffer):len(vi_buffer)+1] != keys):
            vi_buffer = ""
            weechat.bar_item_update("vi_buffer")
        # imap_esc sequence detected -- remove the sequence keys from the
        # Weechat input bar and enter Normal mode.
        if imap_esc == vi_buffer:
            buf = weechat.current_buffer()
            input_line = weechat.buffer_get_string(buf, "input")
            cur = weechat.buffer_get_integer(buf, "input_pos")
            input_line = (input_line[:cur-len(imap_esc)+1] +
                          input_line[cur:])
            weechat.buffer_set(buf, "input", input_line)
            set_cur(buf, input_line, cur-len(imap_esc)+1, False)
            set_mode("NORMAL")
            vi_buffer = ""
            weechat.bar_item_update("vi_buffer")
            return weechat.WEECHAT_RC_OK_EAT
        return weechat.WEECHAT_RC_OK

    # We're in Replace mode — allow "normal" key presses (e.g. "a") and
    # overwrite the next character with them, but let the other key presses
    # pass normally (e.g. backspace, arrow keys, etc).
    if mode == "REPLACE":
        if len(keys) == 1:
            weechat.command("", "/input delete_next_char")
        elif keys == "\x01?":
            weechat.command("", "/input move_previous_char")
            return weechat.WEECHAT_RC_OK_EAT
        return weechat.WEECHAT_RC_OK

    # We're catching keys! Only "normal" key presses interest us (e.g. "a"),
    # not complex ones (e.g. backspace).
    if len(keys) == 1 and catching_keys_data['amount']:
        catching_keys_data['keys'] += keys
        catching_keys_data['amount'] -= 1
        # Done catching keys, execute the callback.
        if catching_keys_data['amount'] == 0:
            globals()[catching_keys_data['callback']]()
            vi_buffer = ""
            weechat.bar_item_update("vi_buffer")
        return weechat.WEECHAT_RC_OK_EAT

    # We're in command-line mode.
    if mode == "COMMAND":
        buf = weechat.current_buffer()
        cmd_text = weechat.buffer_get_string(buf, "input")
        weechat.hook_timer(1, 0, 1, "cb_check_cmd_mode", "")
        # Return key.
        if keys == "\x01M":
            weechat.hook_timer(1, 0, 1, "cb_exec_cmd", cmd_text)
            if len(cmd_text) > 1 and (not cmd_history or
                                      cmd_history[-1] != cmd_text):
                cmd_history.append(cmd_text)
            cmd_history_index = 0
            set_mode("NORMAL")
            buf = weechat.current_buffer()
            input_line = input_line_backup[buf]['input_line']
            weechat.buffer_set(buf, "input", input_line)
            set_cur(buf, input_line, input_line_backup[buf]['cur'], False)
        # Up arrow.
        elif keys == "\x01[[A":
            if cmd_history_index > -len(cmd_history):
                cmd_history_index -= 1
                cmd_text = cmd_history[cmd_history_index]
            weechat.buffer_set(buf, "input", cmd_text)
            set_cur(buf, cmd_text, len(cmd_text), False)
        # Down arrow.
        elif keys == "\x01[[B":
            if cmd_history_index < -1:
                cmd_history_index += 1
                cmd_text = cmd_history[cmd_history_index]
            else:
                cmd_history_index = 0
                cmd_text = ":"
            weechat.buffer_set(buf, "input", cmd_text)
            set_cur(buf, cmd_text, len(cmd_text), False)
        # Tab key. No completion when searching ("/").
        elif keys == "\x01I" and cmd_text[0] == ":":
            if cmd_text_orig is None:
                input_ = list(cmd_text)
                del input_[0]
                cmd_text_orig = "".join(input_)
            cmd_compl_list = []
            for cmd in VI_COMMANDS.keys():
                if cmd.startswith(cmd_text_orig):
                    cmd_compl_list.append(cmd)
            if cmd_compl_list:
                curr_suggestion = cmd_compl_list[cmd_compl_pos]
                cmd_text = ":%s" % curr_suggestion
                cmd_compl_list[cmd_compl_pos] = weechat.string_eval_expression(
                    "${color:bold}%s${color:-bold}" % curr_suggestion,
                    {}, {}, {})
                cmd_compl_text = ", ".join(cmd_compl_list)
                cmd_compl_pos = (cmd_compl_pos + 1) % len(cmd_compl_list)
                weechat.buffer_set(buf, "input", cmd_text)
                set_cur(buf, cmd_text, len(cmd_text), False)
        # Input.
        else:
            cmd_compl_text = ""
            cmd_text_orig = None
            cmd_compl_pos = 0
        weechat.bar_item_update("cmd_completion")
        if keys in ["\x01M", "\x01[[A", "\x01[[B"]:
            cmd_compl_text = ""
            return weechat.WEECHAT_RC_OK_EAT
        else:
            return weechat.WEECHAT_RC_OK
    # Enter command mode.
    elif keys in [":", "/"]:
        if keys == "/":
            weechat.command("", "/input search_text_here")
            if not weechat.config_string_to_boolean(
                    vimode_settings['search_vim']):
                return weechat.WEECHAT_RC_OK
        else:
            buf = weechat.current_buffer()
            cur = weechat.buffer_get_integer(buf, "input_pos")
            input_line = weechat.buffer_get_string(buf, "input")
            input_line_backup[buf] = {'input_line': input_line, 'cur': cur}
            input_line = ":"
            weechat.buffer_set(buf, "input", input_line)
            set_cur(buf, input_line, 1, False)
        set_mode("COMMAND")
        cmd_compl_text = ""
        cmd_text_orig = None
        cmd_compl_pos = 0
        return weechat.WEECHAT_RC_OK_EAT

    # Add key to the buffer.
    vi_buffer += keys
    weechat.bar_item_update("vi_buffer")
    if not vi_buffer:
        return weechat.WEECHAT_RC_OK

    # Check if the keys have a (partial or full) match. If so, also get the
    # keys without the count. (These are the actual keys we should handle.)
    # After that, `vi_buffer` is only used for display purposes — only
    # `vi_keys` is checked for all the handling.
    # If no matches are found, the keys buffer is cleared.
    matched, vi_keys, count = get_keys_and_count(vi_buffer)
    if not matched:
        vi_buffer = ""
        return weechat.WEECHAT_RC_OK_EAT
    # Check if it's a command (user defined key mapped to a :cmd).
    if vi_keys.startswith(":"):
        weechat.hook_timer(1, 0, 1, "cb_exec_cmd", "{} {}".format(vi_keys,
                                                                  count))
        vi_buffer = ""
        return weechat.WEECHAT_RC_OK_EAT
    # It's a WeeChat command (user defined key mapped to a /cmd).
    if vi_keys.startswith("/"):
        weechat.command("", vi_keys)
        vi_buffer = ""
        return weechat.WEECHAT_RC_OK_EAT

    buf = weechat.current_buffer()
    input_line = weechat.buffer_get_string(buf, "input")
    cur = weechat.buffer_get_integer(buf, "input_pos")

    # It's a default mapping. If the corresponding value is a string, we assume
    # it's a WeeChat command. Otherwise, it's a method we'll call.
    if vi_keys in VI_KEYS:
        if vi_keys not in ['u', '\x01R']:
            add_undo_history(buf, input_line)
        if isinstance(VI_KEYS[vi_keys], str):
            for _ in range(max(count, 1)):
                # This is to avoid crashing WeeChat on script reloads/unloads,
                # because no hooks must still be running when a script is
                # reloaded or unloaded.
                if (VI_KEYS[vi_keys] == "/input return" and
                        input_line.startswith("/script ")):
                    return weechat.WEECHAT_RC_OK
                weechat.command("", VI_KEYS[vi_keys])
                current_cur = weechat.buffer_get_integer(buf, "input_pos")
                set_cur(buf, input_line, current_cur)
        else:
            VI_KEYS[vi_keys](buf, input_line, cur, count)
    # It's a motion (e.g. "w") — call `motion_X()` where X is the motion, then
    # set the cursor's position to what that function returned.
    elif vi_keys in VI_MOTIONS:
        if vi_keys in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys]
        else:
            func = "motion_%s" % vi_keys
        end, _, _ = globals()[func](input_line, cur, count)
        set_cur(buf, input_line, end)
    # It's an operator + motion (e.g. "dw") — call `motion_X()` (where X is
    # the motion), then we call `operator_Y()` (where Y is the operator)
    # with the position `motion_X()` returned. `operator_Y()` should then
    # handle changing the input line.
    elif (len(vi_keys) > 1 and
          vi_keys[0] in VI_OPERATORS and
          vi_keys[1:] in VI_MOTIONS):
        add_undo_history(buf, input_line)
        if vi_keys[1:] in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys[1:]]
        else:
            func = "motion_%s" % vi_keys[1:]
        pos, overwrite, catching = globals()[func](input_line, cur, count)
        # If it's a catching motion, we don't want to call the operator just
        # yet -- this code will run again when the motion is complete, at which
        # point we will.
        if not catching:
            oper = "operator_%s" % vi_keys[0]
            globals()[oper](buf, input_line, cur, pos, overwrite)
    # The combo isn't completed yet (e.g. just "d").
    else:
        return weechat.WEECHAT_RC_OK_EAT

    # We've already handled the key combo, so clear the keys buffer.
    if not catching_keys_data['amount']:
        vi_buffer = ""
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK_EAT

def cb_check_imap_esc(data, remaining_calls):
    """Clear the imap_esc sequence after some time if nothing was pressed."""
    global vi_buffer
    if vi_buffer == data:
        vi_buffer = ""
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

def cb_key_combo_search(data, signal, signal_data):
    """Handle keys while search mode is active (if search_vim is enabled)."""
    if not weechat.config_string_to_boolean(vimode_settings['search_vim']):
        return weechat.WEECHAT_RC_OK
    if mode == "COMMAND":
        if signal_data == "\x01M":
            set_mode("SEARCH")
            return weechat.WEECHAT_RC_OK_EAT
    elif mode == "SEARCH":
        if signal_data == "\x01M":
            set_mode("NORMAL")
        else:
            if signal_data == "n":
                weechat.command("", "/input search_next")
            elif signal_data == "N":
                weechat.command("", "/input search_previous")
            # Start a new search.
            elif signal_data == "/":
                weechat.command("", "/input search_stop_here")
                set_mode("NORMAL")
                weechat.command("", "/input search_text_here")
            return weechat.WEECHAT_RC_OK_EAT
    return weechat.WEECHAT_RC_OK

# Callbacks.
# ==========

# Bar items.
# ----------

def cb_vi_buffer(data, item, window):
    """Return the content of the vi buffer (pressed keys on hold)."""
    return vi_buffer

def cb_cmd_completion(data, item, window):
    """Return the text of the command line."""
    return cmd_compl_text

def cb_mode_indicator(data, item, window):
    """Return the current mode (INSERT/NORMAL/REPLACE/...)."""
    return "{}{}{}{}{}".format(
        weechat.color(mode_colors[mode]),
        vimode_settings['mode_indicator_prefix'], mode,
        vimode_settings['mode_indicator_suffix'], weechat.color("reset"))

def cb_line_numbers(data, item, window):
    """Fill the line numbers bar item."""
    bar_height = weechat.window_get_integer(window, "win_chat_height")
    content = ""
    for i in range(1, bar_height + 1):
        content += "{}{}{}\n".format(vimode_settings['line_number_prefix'], i,
                                     vimode_settings['line_number_suffix'])
    return content

# Callbacks for the line numbers bar.
# ...................................

def cb_update_line_numbers(data, signal, signal_data):
    """Call `cb_timer_update_line_numbers()` when switching buffers.

    A timer is required because the bar item is refreshed before the new buffer
    is actually displayed, so ``win_chat_height`` would refer to the old
    buffer. Using a timer refreshes the item after the new buffer is displayed.
    """
    weechat.hook_timer(10, 0, 1, "cb_timer_update_line_numbers", "")
    return weechat.WEECHAT_RC_OK

def cb_timer_update_line_numbers(data, remaining_calls):
    """Update the line numbers bar item."""
    weechat.bar_item_update("line_numbers")
    return weechat.WEECHAT_RC_OK


# Config.
# -------

def cb_config(data, option, value):
    """Script option changed, update our copy."""
    option_name = option.split(".")[-1]
    if option_name in vimode_settings:
        vimode_settings[option_name] = value
    if option_name == 'user_mappings':
        load_user_mappings()
    if "_color" in option_name:
        load_mode_colors()
    return weechat.WEECHAT_RC_OK

def load_mode_colors():
    mode_colors.update({
        'NORMAL': "{},{}".format(
            vimode_settings['mode_indicator_normal_color'],
            vimode_settings['mode_indicator_normal_color_bg']),
        'INSERT': "{},{}".format(
            vimode_settings['mode_indicator_insert_color'],
            vimode_settings['mode_indicator_insert_color_bg']),
        'REPLACE': "{},{}".format(
            vimode_settings['mode_indicator_replace_color'],
            vimode_settings['mode_indicator_replace_color_bg']),
        'COMMAND': "{},{}".format(
            vimode_settings['mode_indicator_cmd_color'],
            vimode_settings['mode_indicator_cmd_color_bg']),
        'SEARCH': "{},{}".format(
            vimode_settings['mode_indicator_search_color'],
            vimode_settings['mode_indicator_search_color_bg'])
    })

def load_user_mappings():
    """Load user-defined mappings."""
    mappings = {}
    if vimode_settings['user_mappings']:
        mappings.update(json.loads(vimode_settings['user_mappings']))
    vimode_settings['user_mappings'] = mappings


# Command-line execution.
# -----------------------

def cb_exec_cmd(data, remaining_calls):
    """Translate and execute our custom commands to WeeChat command."""
    # Process the entered command.
    data = list(data)
    del data[0]
    data = "".join(data)
    # s/foo/bar command.
    if data.startswith("s/"):
        cmd = data
        parsed_cmd = next(csv.reader(StringIO(cmd), delimiter="/",
                                     escapechar="\\"))
        pattern = re.escape(parsed_cmd[1])
        repl = parsed_cmd[2]
        repl = re.sub(r"([^\\])&", r"\1" + pattern, repl)
        flag = None
        if len(parsed_cmd) == 4:
            flag = parsed_cmd[3]
        count = 1
        if flag == "g":
            count = 0
        buf = weechat.current_buffer()
        input_line = weechat.buffer_get_string(buf, "input")
        input_line = re.sub(pattern, repl, input_line, count)
        weechat.buffer_set(buf, "input", input_line)
    # Shell command.
    elif data.startswith("!"):
        weechat.command("", "/exec -buffer shell %s" % data[1:])
    # Commands like `:22`. This should start cursor mode (``/cursor``) and take
    # us to the relevant line.
    elif data.isdigit():
        line_number = int(data)
        hdata_window = weechat.hdata_get("window")
        window = weechat.current_window()
        x = weechat.hdata_integer(hdata_window, window, "win_chat_x")
        y = (weechat.hdata_integer(hdata_window, window, "win_chat_y") +
             (line_number - 1))
        weechat.command("", "/cursor go {},{}".format(x, y))
    # Check againt defined commands.
    elif data:
        raw_data = data
        data = data.split(" ", 1)
        cmd = data[0]
        args = ""
        if len(data) == 2:
            args = data[1]
        if cmd in VI_COMMANDS:
            if isinstance(VI_COMMANDS[cmd], str):
                weechat.command("", "%s %s" % (VI_COMMANDS[cmd], args))
            else:
                VI_COMMANDS[cmd](args)
        else:
            # Check for commands not sepearated by space (e.g. "b2")
            for i in range(1, len(raw_data)):
                tmp_cmd = raw_data[:i]
                tmp_args = raw_data[i:]
                if tmp_cmd in VI_COMMANDS and tmp_args.isdigit():
                    weechat.command("", "%s %s" % (VI_COMMANDS[tmp_cmd],
                                                   tmp_args))
                    return weechat.WEECHAT_RC_OK
            # No vi commands found, run the command as WeeChat command
            weechat.command("", "/{} {}".format(cmd, args))
    return weechat.WEECHAT_RC_OK

def cb_vimode_go_to_normal(data, buf, args):
    set_mode("NORMAL")
    return weechat.WEECHAT_RC_OK

# Script commands.
# ----------------

def cb_vimode_cmd(data, buf, args):
    """Handle script commands (``/vimode <command>``)."""
    # ``/vimode`` or ``/vimode help``
    if not args or args == "help":
        weechat.prnt("", "[vimode.py] %s" % README_URL)
    # ``/vimode bind_keys`` or ``/vimode bind_keys --list``
    elif args.startswith("bind_keys"):
        infolist = weechat.infolist_get("key", "", "default")
        weechat.infolist_reset_item_cursor(infolist)
        commands = ["/key unbind ctrl-W",
                    "/key bind ctrl-W /input delete_previous_word",
                    "/key bind ctrl-^ /input jump_last_buffer_displayed",
                    "/key bind ctrl-Wh /window left",
                    "/key bind ctrl-Wj /window down",
                    "/key bind ctrl-Wk /window up",
                    "/key bind ctrl-Wl /window right",
                    "/key bind ctrl-W= /window balance",
                    "/key bind ctrl-Wx /window swap",
                    "/key bind ctrl-Ws /window splith",
                    "/key bind ctrl-Wv /window splitv",
                    "/key bind ctrl-Wq /window merge"]
        while weechat.infolist_next(infolist):
            key = weechat.infolist_string(infolist, "key")
            if re.match(REGEX_PROBLEMATIC_KEYBINDINGS, key):
                commands.append("/key unbind %s" % key)
        if args == "bind_keys":
            weechat.prnt("", "Running commands:")
            for command in commands:
                weechat.command("", command)
            weechat.prnt("", "Done.")
        elif args == "bind_keys --list":
            weechat.prnt("", "Listing commands we'll run:")
            for command in commands:
                weechat.prnt("", "    %s" % command)
            weechat.prnt("", "Done.")
    return weechat.WEECHAT_RC_OK


# Helpers.
# ========

# Motions/keys helpers.
# ---------------------

def get_pos(data, regex, cur, ignore_cur=False, count=0):
    """Return the position of `regex` match in `data`, starting at `cur`.

    Args:
        data (str): the data to search in.
        regex (pattern): regex pattern to search for.
        cur (int): where to start the search.
        ignore_cur (bool, optional): should the first match be ignored if it's
            also the character at `cur`?
            Defaults to False.
        count (int, optional): the index of the match to return. Defaults to 0.

    Returns:
        int: position of the match. -1 if no matches are found.
    """
    # List of the *positions* of the found patterns.
    matches = [m.start() for m in re.finditer(regex, data[cur:])]
    pos = -1
    if count:
        if len(matches) > count - 1:
            if ignore_cur and matches[0] == 0:
                if len(matches) > count:
                    pos = matches[count]
            else:
                pos = matches[count - 1]
    elif matches:
        if ignore_cur and matches[0] == 0:
            if len(matches) > 1:
                pos = matches[1]
        else:
            pos = matches[0]
    return pos

def set_cur(buf, input_line, pos, cap=True):
    """Set the cursor's position.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        pos (int): the position to set the cursor to.
        cap (bool, optional): if True, the `pos` will shortened to the length
            of `input_line` if it's too long. Defaults to True.
    """
    if cap:
        pos = min(pos, len(input_line) - 1)
    weechat.buffer_set(buf, "input_pos", str(pos))

def start_catching_keys(amount, callback, input_line, cur, count, buf=None):
    """Start catching keys. Used for special commands (e.g. "f", "r").

    amount (int): amount of keys to catch.
    callback (str): name of method to call once all keys are caught.
    input_line (str): input line's content.
    cur (int): cursor's position.
    count (int): count, e.g. "2" for "2fs".
    buf (str, optional): pointer to the current WeeChat buffer.
        Defaults to None.

    `catching_keys_data` is a dict with the above arguments, as well as:
        keys (str): pressed keys will be added under this key.
        new_cur (int): the new cursor's position, set in the callback.

    When catching keys is active, normal pressed keys (e.g. "a" but not arrows)
    will get added to `catching_keys_data` under the key "keys", and will not
    be handled any further.
    Once all keys are caught, the method defined in the "callback" key is
    called, and can use the data in `catching_keys_data` to perform its action.
    """
    global catching_keys_data
    if "new_cur" in catching_keys_data:
        new_cur = catching_keys_data['new_cur']
        catching_keys_data = {'amount': 0}
        return new_cur, True, False
    catching_keys_data = ({'amount': amount,
                           'callback': callback,
                           'input_line': input_line,
                           'cur': cur,
                           'keys': "",
                           'count': count,
                           'new_cur': 0,
                           'buf': buf})
    return cur, False, True

def get_keys_and_count(combo):
    """Check if `combo` is a valid combo and extract keys/counts if so.

    Args:
        combo (str): pressed keys combo.

    Returns:
        matched (bool): True if the combo has a (partial or full) match, False
            otherwise.
        combo (str): `combo` with the count removed. These are the actual keys
            we should handle. User mappings are also expanded.
        count (int): count for `combo`.
    """
    # Look for a potential match (e.g. "d" might become "dw" or "dd" so we
    # accept it, but "d9" is invalid).
    matched = False
    # Digits are allowed at the beginning (counts or "0").
    count = 0
    if combo.isdigit():
        matched = True
    elif combo and combo[0].isdigit():
        count = ""
        for char in combo:
            if char.isdigit():
                count += char
            else:
                break
        combo = combo.replace(count, "", 1)
        count = int(count)
    # It's a user defined key. Expand it.
    if combo in vimode_settings['user_mappings']:
        combo = vimode_settings['user_mappings'][combo]
    # It's a WeeChat command.
    if not matched and combo.startswith("/"):
        matched = True
    # Check against defined keys.
    if not matched:
        for key in VI_KEYS:
            if key.startswith(combo):
                matched = True
                break
    # Check against defined motions.
    if not matched:
        for motion in VI_MOTIONS:
            if motion.startswith(combo):
                matched = True
                break
    # Check against defined operators + motions.
    if not matched:
        for operator in VI_OPERATORS:
            if combo.startswith(operator):
                # Check for counts before the motion (but after the operator).
                vi_keys_no_op = combo[len(operator):]
                # There's no motion yet.
                if vi_keys_no_op.isdigit():
                    matched = True
                    break
                # Get the motion count, then multiply the operator count by
                # it, similar to vim's behavior.
                elif vi_keys_no_op and vi_keys_no_op[0].isdigit():
                    motion_count = ""
                    for char in vi_keys_no_op:
                        if char.isdigit():
                            motion_count += char
                        else:
                            break
                    # Remove counts from `vi_keys_no_op`.
                    combo = combo.replace(motion_count, "", 1)
                    motion_count = int(motion_count)
                    count = max(count, 1) * motion_count
                # Check against defined motions.
                for motion in VI_MOTIONS:
                    if motion.startswith(combo[1:]):
                        matched = True
                        break
    return matched, combo, count


# Other helpers.
# --------------

def set_mode(arg):
    """Set the current mode and update the bar mode indicator."""
    global mode
    buf = weechat.current_buffer()
    input_line = weechat.buffer_get_string(buf, "input")
    if mode == "INSERT" and arg == "NORMAL":
        add_undo_history(buf, input_line)
    mode = arg
    # If we're going to Normal mode, the cursor must move one character to the
    # left.
    if mode == "NORMAL":
        cur = weechat.buffer_get_integer(buf, "input_pos")
        set_cur(buf, input_line, cur - 1, False)
    weechat.bar_item_update("mode_indicator")

def cb_check_cmd_mode(data, remaining_calls):
    """Exit command mode if user erases the leading ':' character."""
    buf = weechat.current_buffer()
    cmd_text = weechat.buffer_get_string(buf, "input")
    if not cmd_text:
        set_mode("NORMAL")
    return weechat.WEECHAT_RC_OK

def add_undo_history(buf, input_line):
    """Add an item to the per-buffer undo history."""
    if buf in undo_history:
        if not undo_history[buf] or undo_history[buf][-1] != input_line:
            undo_history[buf].append(input_line)
            undo_history_index[buf] = -1
    else:
        undo_history[buf] = ['', input_line]
        undo_history_index[buf] = -1

def clear_undo_history(buf):
    """Clear the undo history for a given buffer."""
    undo_history[buf] = ['']
    undo_history_index[buf] = -1

def print_warning(text):
    """Print warning, in red, to the current buffer."""
    weechat.prnt("", ("%s[vimode.py] %s" % (weechat.color("red"), text)))

def check_warnings():
    """Warn the user about problematic key bindings and tmux/screen."""
    user_warned = False
    # Warn the user about problematic key bindings that may conflict with
    # vimode.
    # The solution is to remove these key bindings, but that's up to the user.
    infolist = weechat.infolist_get("key", "", "default")
    problematic_keybindings = []
    while weechat.infolist_next(infolist):
        key = weechat.infolist_string(infolist, "key")
        command = weechat.infolist_string(infolist, "command")
        if re.match(REGEX_PROBLEMATIC_KEYBINDINGS, key):
            problematic_keybindings.append("%s -> %s" % (key, command))
    if problematic_keybindings:
        user_warned = True
        print_warning("Problematic keybindings detected:")
        for keybinding in problematic_keybindings:
            print_warning("    %s" % keybinding)
        print_warning("These keybindings may conflict with vimode.")
        print_warning("You can remove problematic key bindings and add"
                      " recommended ones by using /vimode bind_keys, or only"
                      " list them with /vimode bind_keys --list")
        print_warning("For help, see: %s" % FAQ_KEYBINDINGS)
    del problematic_keybindings
    # Warn tmux/screen users about possible Esc detection delays.
    if "STY" in os.environ or "TMUX" in os.environ:
        if user_warned:
            weechat.prnt("", "")
        user_warned = True
        print_warning("tmux/screen users, see: %s" % FAQ_ESC)
    if (user_warned and not
            weechat.config_string_to_boolean(vimode_settings['no_warn'])):
        if user_warned:
            weechat.prnt("", "")
        print_warning("To force disable warnings, you can set"
                      " plugins.var.python.vimode.no_warn to 'on'")


# Main script.
# ============

if __name__ == "__main__":
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                     SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    # Warn the user if he's using an unsupported WeeChat version.
    VERSION = weechat.info_get("version_number", "")
    if int(VERSION) < 0x01000000:
        print_warning("Please upgrade to WeeChat ≥ 1.0.0. Previous versions"
                      " are not supported.")
    # Set up script options.
    for option, value in list(vimode_settings.items()):
        if weechat.config_is_set_plugin(option):
            vimode_settings[option] = weechat.config_get_plugin(option)
        else:
            weechat.config_set_plugin(option, value[0])
            vimode_settings[option] = value[0]
        weechat.config_set_desc_plugin(option,
                                       "%s (default: \"%s\")" % (value[1],
                                                                 value[0]))
    load_user_mappings()
    load_mode_colors()
    # Warn the user about possible problems if necessary.
    if not weechat.config_string_to_boolean(vimode_settings['no_warn']):
        check_warnings()
    # Create bar items and setup hooks.
    weechat.bar_item_new("mode_indicator", "cb_mode_indicator", "")
    weechat.bar_item_new("cmd_completion", "cb_cmd_completion", "")
    weechat.bar_item_new("vi_buffer", "cb_vi_buffer", "")
    weechat.bar_item_new("line_numbers", "cb_line_numbers", "")
    weechat.bar_new("vi_line_numbers", "on", "0", "window", "", "left",
                    "vertical", "vertical", "0", "0", "default", "default",
                    "default", "0", "line_numbers")
    weechat.hook_config("plugins.var.python.%s.*" % SCRIPT_NAME, "cb_config",
                        "")
    weechat.hook_signal("key_pressed", "cb_key_pressed", "")
    weechat.hook_signal("key_combo_default", "cb_key_combo_default", "")
    weechat.hook_signal("key_combo_search", "cb_key_combo_search", "")
    weechat.hook_signal("buffer_switch", "cb_update_line_numbers", "")
    weechat.hook_command("vimode", SCRIPT_DESC, "[help | bind_keys [--list]]",
                         "     help: show help\n"
                         "bind_keys: unbind problematic keys, and bind"
                         " recommended keys to use in WeeChat\n"
                         "          --list: only list changes",
                         "help || bind_keys |--list",
                         "cb_vimode_cmd", "")
    weechat.hook_command("vimode_go_to_normal",
                         ("This command can be used for key bindings to go to "
                          "normal mode."),
                         "", "", "", "cb_vimode_go_to_normal", "")
    # Remove obsolete bar.
    vi_cmd_bar = weechat.bar_search("vi_cmd")
    weechat.bar_remove(vi_cmd_bar)
