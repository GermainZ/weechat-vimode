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
# For the full help, type `/vimode` inside WeeChat.
#

SCRIPT_NAME = "vimode"
SCRIPT_AUTHOR = "GermainZ <germanosz@gmail.com>"
SCRIPT_VERSION = "0.4"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = ("Add vi/vim-like modes and keybindings to WeeChat.")


import weechat
import re
import time
from subprocess import Popen, PIPE
from StringIO import StringIO
from csv import reader


weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                 SCRIPT_DESC, '', '')


# Type '/vimode' in WeeChat to view this help formatted text.
HELP_TEXT = """
GitHub repo: {url}https://github.com/GermainZ/weechat-vimode

{header}Description:
Add vi/vim-like modes and keybindings to WeeChat.

{header}Usage:
To switch to Normal mode, press Esc or Ctrl+Space.

Two bar items are provided:
    {bold}mode_indicator{reset}: shows the currently active mode \
(e.g. "NORMAL").
    {bold}vi_buffer{reset}: shows partial commands (e.g. "df").
You can add them to your input bar. For example, using iset.pl:
    /iset weechat.bar.input.items
    <Alt+Enter>
    Add {bold}[mode_indicator]+{reset} at the start, and \
{bold},[vi_buffer]{reset} at the end.
Final result example:
    "{bold}[mode_indicator]+{reset}[input_prompt]+(away),[input_search],\
[input_paste],input_text,{bold}[vi_buffer]{reset}"

To switch back to Insert mode, you can use i, a, A, etc.
To execute an Ex command, simply precede it with a ':' while in normal mode, \
for example: ":h" or ":s/foo/bar".

{header}Current key bindings:
{header2}Input line:
{header3}Operators:
d{com}{{motion}}{reset}   Delete text that {com}{{motion}}{reset} moves over.
c{com}{{motion}}{reset}   Delete {com}{{motion}}{reset} text and start insert.
y{com}{{motion}}{reset}   Yank {com}{{motion}}{reset} text to clipboard.
{header3}Motions:
h           {com}[count]{reset} characters to the left exclusive.
l           {com}[count]{reset} characters to the right exclusive.
w           {com}[count]{reset} words forward exclusive.
W           {com}[count]{reset} WORDS forward exclusive.
b           {com}[count]{reset} words backward.
B           {com}[count]{reset} WORDS backward.
ge          Backward to the end of word {com}[count]{reset} inclusive.
gE          Backward to the end of WORD {com}[count]{reset} inclusive.
e           Forward to the end of word {com}[count]{reset} inclusive.
E           Forward to the end of WORD {com}[count]{reset} inclusive.
0           To the first character of the line.
^           To the first non-blank character of the line exclusive.
$           To the end of the line exclusive.
f{com}{{char}}{reset}     To {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the right.
F{com}{{char}}{reset}     To {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the left.
t{com}{{char}}{reset}     Till before {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the right.
T{com}{{char}}{reset}     Till after {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the left.
{header3}Other:
<Space>     {com}[count]{reset} characters to the right.
<BS>        {com}[count]{reset} characters to the left.
x           Delete {com}[count]{reset} characters under and after the cursor.
X           Delete {com}[count]{reset} characters before the cursor.
~           Switch case of the character under the cursor.
r{com}{{count}}{reset}    Replace {com}[count]{reset} characters with \
{com}{{count}}{reset} under and after the cursor.
R           Enter Replace mode. Counts are not supported.
dd          Delete line.
cc          Delete line and start insert.
yy          Yank line. Requires xsel.
I           Insert text before the first non-blank in the line.
p           Put the text from the clipboard after the cursor. Requires xsel.
{header2}Buffers:
j           Scroll buffer up. {note}
k           Scroll buffer down. {note}
^U          Scroll buffer page up. {note}
^D          Scroll buffer page down. {note}
gt          Go to the next buffer.
            (or K)
gT          Go to the previous buffer.
            (or J)
gg          Goto first line.
G           Goto line {com}[count]{reset}, default last line. {note}
/           Launch WeeChat search mode
^^          Jump to the last buffer.
{note} Counts may not work as intended, depending on the value of \
{bold}weechat.look.scroll_amount{reset} and \
{bold}weechat.look.scroll_page_percent{reset}.
{header2}Windows:
^Wh         Go to the window to the left.
^Wj         Go to the window below the current one.
^Wk         Go to the window above the current one.
^Wl         Go to the window to the right.
^W=         Balance windows' sizes.
^Wx         Swap window with the next one.
^Ws         Split current window in two.
^Wv         Split current window in two, but vertically.
^Wq         Quit current window.

{header}Current commands:
:h                  Help ({bold}/help{reset})
:set                Set WeeChat config option ({bold}/set{reset})
:q                  Closes current buffer ({bold}/close{reset})
:qall               Exits WeeChat ({bold}/exit{reset})
:w                  Saves settings ({bold}/save{reset})
:!{com}{{cmd}}{reset}             Execute shell command ({bold}/exec -buffer \
shell{reset})
:s/pattern/repl
:s/pattern/repl/g   Search/Replace {note}
{note} Supports regex (check docs for the Python re module for more \
information). '&' in the replacement is also substituted by the pattern. If \
the 'g' flag isn't present, only the first match will be substituted.

{header}History:
{header2}version 0.1:{reset}   initial release
{header2}version 0.2:{reset}   added esc to switch to normal mode, various \
key bindings and commands.
{header2}version 0.2.1:{reset} fixes/refactoring
{header2}version 0.3:{reset}   separate operators from motions and better \
handling. Added yank operator, I/p. Other fixes and improvements. The Escape \
key should work flawlessly on WeeChat ≥ 0.4.4.
{header2}version 0.4:{reset}   added: f, F, t, T, r, R, W, E, B, gt, gT, J, \
K, ge, gE, X, ~, ^^, ^Wh, ^Wj, ^Wk, ^Wl, ^W=, ^Wx, ^Ws, ^Wv, ^Wq, :!cmd. \
Improved substitutions (:s/foo/bar). Rewrote key handling logic to take \
advantage of WeeChat API additions. Many fixes and improvements. \
WeeChat ≥ 1.0.0 required.
""".format(header=weechat.color("red"), header2=weechat.color("lightred"),
           header3=weechat.color("brown"), url=weechat.color("cyan"),
           note="%s*%s" % (weechat.color("red"), weechat.color("reset")),
           bold=weechat.color("bold"), reset=weechat.color("reset"),
           com=weechat.color("green"))

# Holds the text of the command-line mode (currently only Ex commands ":").
cmd_text = ''
# Mode we're in. One of INSERT, NORMAL or REPLACE.
mode = "INSERT"
# Holds normal commands (e.g. 'dd').
vi_buffer = ''
# Buffer used to show help message (/vimode).
help_buf = None
# See cb_key_combo_default(…).
esc_pressed = 0
# See cb_key_pressed(…).
last_signal_time = 0
# See start_catching_keys(…) for more info.
catching_keys_data = {'amount': 0}

# Regex patterns for some motions
REGEX_MOTION_LOWERCASE_W = re.compile(r"\b\w|[^\w ]")
REGEX_MOTION_UPPERCASE_W = re.compile(r"(?<!\S)\b\w")
REGEX_MOTION_LOWERCASE_E = re.compile(r"\w\b|[^\w ]")
REGEX_MOTION_UPPERCASE_E = re.compile(r"\S(?!\S)")
REGEX_MOTION_LOWERCASE_B = re.compile(r"\w\b|[^\w ]")
REGEX_MOTION_UPPERCASE_B = re.compile(r"\w\b(?!\S)")
REGEX_MOTION_GE = re.compile(r"\b\w|[^\w ]")
REGEX_MOTION_CARRET = re.compile(r"\S")

# Some common vi Ex commands.
# Others may be present in cb_exec_cmd(…).
VI_COMMANDS = {'h': "/help", 'qall': "/exit", 'q': "/close", 'w': "/save",
               'set': "/set"}

def get_pos(data, regex, cur, ignore_zero=False, count=0):
    """Return the position of a regex pattern match in data, starting at cur.

    data -- the data to search in
    regex -- regex pattern to search for
    cur -- where to start the search
    ignore_zero -- if the first match should be ignored if it's also the first
                   character in data (default False)
    count -- the index of the match (default 0 for the first match)
    """
    # List of the *positions* of the found patterns
    matches = [m.start() for m in re.finditer(regex, data[cur:])]
    pos = 0
    if count:
        if len(matches) > count-1:
            if ignore_zero and matches[count-1] == 0:
                if len(matches) > count:
                    pos = matches[count]
            else:
                pos = matches[count-1]
    elif matches:
        if ignore_zero and matches[0] == 0:
            if len(matches) > 1:
                pos = matches[1]
        else:
            pos = matches[0]
    return pos

def set_cur(buf, input_line, pos, cap=True):
    """Set the cursor's position.

    cap -- if True, the cursor's position can't be more than the input line's
           length.
    """
    if cap:
        pos = min(pos, len(input_line) - 1)
    weechat.buffer_set(buf, "input_pos", str(pos))

def start_catching_keys(amount, callback, input_line, cur, count, buf=None):
    """Start catching keys. Used for special commands (e.g. 'f', 'r').

    amount -- amount of keys to catch
    callback -- name of method to call once all keys are caught
    input_line -- input line's content
    cur -- cursor's position
    count -- {count}, e.g. '2' for '2fs'
    buf -- buffer (default None)

    catching_keys_data is a dict with the above arguments, as well as:
        keys -- pressed keys will be added under this key
        new_cur -- the new cursor's position, set in the callback

    When catching keys is active, 'normal' pressed keys  will get added to
    catching_keys_data['keys'] and will not be handled any further.
    Once all keys are caught, catching_keys_data['callback'] is called.
    """
    global catching_keys_data
    if 'new_cur' in catching_keys_data:
        new_cur = catching_keys_data['new_cur']
        catching_keys_data = {'amount': 0}
        return new_cur, True
    catching_keys_data = ({'amount': amount, 'callback': callback,
                           'input_line': input_line, 'cur': cur,
                           'keys': '', 'count': count,
                           'new_cur': 0, 'buf': buf})
    return cur, False


def operator_d(buf, input_line, pos1, pos2, overwrite=False):
    """Simulate the behavior of the 'd' operator. Remove everything between two
    positions from the input line.

    If overwrite is set to True, the character at the cursor's new position is
    removed as well (pos2 is inclusive.)
    """
    start = min([pos1, pos2])
    end = max([pos1, pos2])
    if overwrite:
        end += 1
    input_line = list(input_line)
    del input_line[start:end]
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, pos1)

def operator_c(buf, input_line, pos1, pos2, overwrite=False):
    """Simulate the behavior of the 'c' operator.

    If overwrite is set to True, the character at the cursor's new position is
    removed as well (pos2 is inclusive.)
    """
    operator_d(buf, input_line, pos1, pos2, overwrite)
    set_mode("INSERT")

def operator_y(buf, input_line, pos1, pos2, _):
    """Simulate the behavior of the 'y' operator."""
    start = min([pos1, pos2])
    end = max([pos1, pos2])
    proc = Popen(['xsel', '-bi'], stdin=PIPE)
    proc.communicate(input=input_line[start:end])

def motion_w(input_line, cur, count):
    """Return the new position of the cursor after the 'w' motion."""
    count = max(1, count)
    pos = get_pos(input_line, REGEX_MOTION_LOWERCASE_W, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur+pos, False

def motion_W(input_line, cur, count):
    """Return the new position of the cursor after the 'W' motion."""
    count = max(1, count)
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_W, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur+pos, False

def motion_e(input_line, cur, count):
    """Return the new position of the cursor after the 'e' motion."""
    count = max(1, count)
    pos = get_pos(input_line, REGEX_MOTION_LOWERCASE_E, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur+pos, True

def motion_E(input_line, cur, count):
    """Return the new position of the cursor after the 'E' motion."""
    count = max(1, count)
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_E, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur+pos, True

def motion_b(input_line, cur, count):
    """Return the new position of the cursor after the 'b' motion."""
    count = max(1, count)
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_LOWERCASE_B, new_cur,
                  count=count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_B(input_line, cur, count):
    """Return the new position of the cursor after the 'B' motion."""
    count = max(1, count)
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_UPPERCASE_B, new_cur,
                  count=count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_ge(input_line, cur, count):
    """Return the new position of the cursor after the 'ge' motion."""
    count = max(1, count)
    new_cur = len(input_line) - cur - 1
    pos = get_pos(input_line[::-1], REGEX_MOTION_GE, new_cur,
                  count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_gE(input_line, cur, count):
    """Return the new position of the cursor after the 'gE' motion."""
    count = max(1, count)
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_GE, new_cur,
                  True, count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_h(input_line, cur, count):
    """Return the new position of the cursor after the 'h' motion."""
    count = max(1, count)
    return max(0, cur-count), False

def motion_l(input_line, cur, count):
    """Return the new position of the cursor after the 'l' motion."""
    count = max(1, count)
    return cur+count, False

def motion_carret(input_line, cur, count):
    """Return the new position of the cursor after the '^' motion."""
    pos = get_pos(input_line, REGEX_MOTION_CARRET, 0)
    return pos, False

def motion_dollar(input_line, cur, count):
    """Return the new position of the cursor after the '$' motion."""
    pos = len(input_line)
    return pos, False

def motion_f(input_line, cur, count):
    """"Simulate vi's behavior for the f key."""
    count = max(1, count)
    return start_catching_keys(1, "cb_motion_f", input_line, cur, count)

def cb_motion_f():
    """Callback for motion_f."""
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'], True,
                  catching_keys_data['count'])
    catching_keys_data['new_cur'] = pos + catching_keys_data['cur']
    cb_key_combo_default(None, None, '')

def motion_F(input_line, cur, count):
    """"Simulate vi's behavior for the F key."""
    count = max(1, count)
    return start_catching_keys(1, "cb_motion_F", input_line, cur, count)

def cb_motion_F():
    """Callback for motion_F."""
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'][::-1], re.escape(pattern),
                  (len(catching_keys_data['input_line']) -
                   (catching_keys_data['cur'] + 1)),
                  True, catching_keys_data['count'])
    catching_keys_data['new_cur'] = catching_keys_data['cur'] - pos
    cb_key_combo_default(None, None, '')

def motion_t(input_line, cur, count):
    """"Simulate vi's behavior for the t key."""
    count = max(1, count)
    return start_catching_keys(1, "cb_motion_t", input_line, cur, count)

def cb_motion_t():
    """Callback for motion_t."""
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'] + 1,
                  True, catching_keys_data['count'])
    pos += 1
    if pos > 0:
        catching_keys_data['new_cur'] = pos + catching_keys_data['cur'] - 1
    else:
        catching_keys_data['new_cur'] = catching_keys_data['cur']
    cb_key_combo_default(None, None, '')

def motion_T(input_line, cur, count):
    """"Simulate vi's behavior for the T key."""
    count = max(1, count)
    return start_catching_keys(1, "cb_motion_T", input_line, cur, count)

def cb_motion_T():
    """Callback for motion_T."""
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
    cb_key_combo_default(None, None, '')


def key_cc(buf, input_line, cur, repeat):
    """Simulate vi's behavior for cc."""
    weechat.command('', "/input delete_line")
    set_mode("INSERT")

def key_yy(buf, input_line, cur, repeat):
    """Simulate vi's behavior for yy."""
    proc = Popen(['xsel', '-bi'], stdin=PIPE)
    proc.communicate(input=input_line)

def key_i(buf, input_line, cur, repeat):
    """Simulate vi's behavior for i."""
    set_mode("INSERT")

def key_a(buf, input_line, cur, repeat):
    """Simulate vi's behavior for a."""
    set_cur(buf, input_line, cur+1, False)
    set_mode("INSERT")

def key_A(buf, input_line, cur, repeat):
    """Simulate vi's behavior for a."""
    set_cur(buf, input_line, len(input_line), False)
    set_mode("INSERT")

def key_I(buf, input_line, cur, repeat):
    """Simulate vi's behavior for I."""
    pos, _ = motion_carret(input_line, cur, 0)
    set_cur(buf, input_line, pos)
    set_mode("INSERT")

def key_G(buf, input_line, cur, repeat):
    """Simulate vi's behavior for the G key."""
    if repeat > 0:
        # This is necessary to prevent weird scroll jumps.
        weechat.command('', "/window scroll_bottom")
        weechat.command('', "/window scroll %s" % repeat)
    else:
        weechat.command('', "/window scroll_bottom")

def key_r(buf, input_line, cur, repeat):
    """"Simulate vi's behavior for the r key."""
    repeat = max(1, repeat)
    start_catching_keys(1, "cb_key_r", input_line, cur, repeat, buf)

def cb_key_r():
    """Callback for key_r."""
    global catching_keys_data
    input_line = list(catching_keys_data['input_line'])
    count = catching_keys_data['count']
    cur = catching_keys_data['cur']
    if cur + count <= len(input_line):
        for _ in range(count):
            input_line[cur] = catching_keys_data['keys']
            cur += 1
        input_line = ''.join(input_line)
        weechat.buffer_set(catching_keys_data['buf'], "input", input_line)
        set_cur(catching_keys_data['buf'], input_line, cur-1)
    catching_keys_data = {'amount': 0}

def key_R(buf, input_line, cur, repeat):
    """Simulate vi's behavior for the R key."""
    set_mode("REPLACE")

def key_tilda(buf, input_line, cur, repeat):
    """Simulate vi's behavior for the ~ key."""
    repeat = max(1, repeat)
    input_line = list(input_line)
    while repeat and cur < len(input_line):
        input_line[cur] = input_line[cur].swapcase()
        repeat -= 1
        cur += 1
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, cur)

def key_alt_j(buf, input_line, cur, repeat):
    """Preserve WeeChat's alt-j buffer switching.

    This is only called when alt-j<num> is pressed after pressing Esc, because
    \x01\x01j is received in key_combo_default which becomes \x01j after
    removing the detected Esc key.
    If Esc isn't the last pressed key, \x01j<num> is directly received in
    key_combo_default.
    """
    start_catching_keys(2, "cb_key_alt_j", input_line, cur, repeat)

def cb_key_alt_j():
    """Callback for key_alt_j."""
    global catching_keys_data
    weechat.command('', "/buffer " + catching_keys_data['keys'])
    catching_keys_data = {'amount': 0}

# Common vi key bindings. If the value is a string, it's assumed it's a WeeChat
# command, and a function otherwise.
VI_KEYS = {'j': "/window scroll_down",
           'k': "/window scroll_up",
           'G': key_G,
           'gg': "/window scroll_top",
           'x': "/input delete_next_char",
           'X': "/input delete_previous_char",
           'dd': "/input delete_line",
           'cc': key_cc,
           'i': key_i,
           'a': key_a,
           'A': key_A,
           'I': key_I,
           'yy': key_yy,
           'p': "/input clipboard_paste",
           '0': "/input move_beginning_of_line",
           '/': "/input search_text",
           'gt': "/buffer +1",
           'K': "/buffer +1",
           'gT': "/buffer -1",
           'J': "/buffer -1",
           'r': key_r,
           'R': key_R,
           '~': key_tilda,
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
           '\x01[j10': "/buffer 10",
           '\x01[j11': "/buffer 11",
           '\x01[j12': "/buffer 12",
           '\x01[j13': "/buffer 13",
           '\x01[j14': "/buffer 14",
           '\x01[j15': "/buffer 15",
           '\x01[j16': "/buffer 16",
           '\x01[j17': "/buffer 17",
           '\x01[j18': "/buffer 18",
           '\x01[j19': "/buffer 19",
           '\x01[j20': "/buffer 20",
           '\x01[j21': "/buffer 21",
           '\x01[j22': "/buffer 22",
           '\x01[j23': "/buffer 23",
           '\x01[j24': "/buffer 24",
           '\x01[j25': "/buffer 25",
           '\x01[j26': "/buffer 26",
           '\x01[j27': "/buffer 27",
           '\x01[j28': "/buffer 28",
           '\x01[j29': "/buffer 29",
           '\x01[j30': "/buffer 30",
           '\x01[j31': "/buffer 31",
           '\x01[j32': "/buffer 32",
           '\x01[j33': "/buffer 33",
           '\x01[j34': "/buffer 34",
           '\x01[j35': "/buffer 35",
           '\x01[j36': "/buffer 36",
           '\x01[j37': "/buffer 37",
           '\x01[j38': "/buffer 38",
           '\x01[j39': "/buffer 39",
           '\x01[j40': "/buffer 40",
           '\x01[j41': "/buffer 41",
           '\x01[j42': "/buffer 42",
           '\x01[j43': "/buffer 43",
           '\x01[j44': "/buffer 44",
           '\x01[j45': "/buffer 45",
           '\x01[j46': "/buffer 46",
           '\x01[j47': "/buffer 47",
           '\x01[j48': "/buffer 48",
           '\x01[j49': "/buffer 49",
           '\x01[j50': "/buffer 50",
           '\x01[j51': "/buffer 51",
           '\x01[j52': "/buffer 52",
           '\x01[j53': "/buffer 53",
           '\x01[j54': "/buffer 54",
           '\x01[j55': "/buffer 55",
           '\x01[j56': "/buffer 56",
           '\x01[j57': "/buffer 57",
           '\x01[j58': "/buffer 58",
           '\x01[j59': "/buffer 59",
           '\x01[j60': "/buffer 60",
           '\x01[j61': "/buffer 61",
           '\x01[j62': "/buffer 62",
           '\x01[j63': "/buffer 63",
           '\x01[j64': "/buffer 64",
           '\x01[j65': "/buffer 65",
           '\x01[j66': "/buffer 66",
           '\x01[j67': "/buffer 67",
           '\x01[j68': "/buffer 68",
           '\x01[j69': "/buffer 69",
           '\x01[j70': "/buffer 70",
           '\x01[j71': "/buffer 71",
           '\x01[j72': "/buffer 72",
           '\x01[j73': "/buffer 73",
           '\x01[j74': "/buffer 74",
           '\x01[j75': "/buffer 75",
           '\x01[j76': "/buffer 76",
           '\x01[j77': "/buffer 77",
           '\x01[j78': "/buffer 78",
           '\x01[j79': "/buffer 79",
           '\x01[j80': "/buffer 80",
           '\x01[j81': "/buffer 81",
           '\x01[j82': "/buffer 82",
           '\x01[j83': "/buffer 83",
           '\x01[j84': "/buffer 84",
           '\x01[j85': "/buffer 85",
           '\x01[j86': "/buffer 86",
           '\x01[j87': "/buffer 87",
           '\x01[j88': "/buffer 88",
           '\x01[j89': "/buffer 89",
           '\x01[j90': "/buffer 90",
           '\x01[j91': "/buffer 91",
           '\x01[j92': "/buffer 92",
           '\x01[j93': "/buffer 93",
           '\x01[j94': "/buffer 94",
           '\x01[j95': "/buffer 95",
           '\x01[j96': "/buffer 96",
           '\x01[j97': "/buffer 97",
           '\x01[j98': "/buffer 98",
           '\x01[j99': "/buffer 99",
           '\x01^': "/input jump_last_buffer",
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
           '\x01Wq': "/window merge"}

# Vi operators. Each operator must have a corresponding function,
# called "operator_X" where X is the operator. For example: "operator_c"
VI_OPERATORS = ['c', 'd', 'y']
# Vi motions. Each motion must have a corresponding function, called "motion_X"
# where X is the motion.
VI_MOTIONS = ['w', 'e', 'b', '^', '$', 'h', 'l', '0', 'W', 'E', 'B', 'f', 'F',
              't', 'T', 'ge', 'gE']
# Special characters for motions. The corresponding function's name is
# converted before calling. For example, '^' will call 'motion_carret' instead
# of 'motion_^' (which isn't allowed because of illegal characters.)
SPECIAL_CHARS = {'^': "carret", '$': "dollar", '~': "tilda"}


# Callbacks for bar items.
def cb_vi_buffer(data, item, window):
    """Return the content of the vi buffer (pressed keys on hold)."""
    return vi_buffer

def cb_cmd_text(data, item, window):
    """Return the text of the command line."""
    return cmd_text

def cb_mode_indicator(data, item, window):
    """Return the current mode (INSERT/NORMAL/REPLACE)."""
    return mode


def set_mode(arg):
    """Set the current mode and update the bar mode indicator."""
    global mode
    mode = arg
    weechat.bar_item_update("mode_indicator")

def cb_exec_cmd(data, remaining_calls):
    """Translate and execute our custom commands to WeeChat command, with
    any passed arguments.
    """
    # Process the entered command
    data = list(data)
    del data[0]
    data = ''.join(data)
    # s/foo/bar command
    if data.startswith("s/"):
        cmd = data
        parsed_cmd = next(reader(StringIO(cmd), delimiter='/',
                                 escapechar='\\'))
        pattern = re.escape(parsed_cmd[1])
        repl = parsed_cmd[2]
        repl = re.sub(r'([^\\])&', r'\1' + pattern, repl)
        flag = None
        if len(parsed_cmd) == 4:
            flag = parsed_cmd[3]
        count = 1
        if flag == 'g':
            count = 0
        buf = weechat.current_buffer()
        input_line = weechat.buffer_get_string(buf, 'input')
        input_line = re.sub(pattern, repl, input_line, count)
        weechat.buffer_set(buf, "input", input_line)
    # Shell command
    elif data.startswith('!'):
        weechat.command('', "/exec -buffer shell %s" % data[1:])
    # Check againt defined commands
    else:
        data = data.split(' ', 1)
        cmd = data[0]
        args = ''
        if len(data) == 2:
            args = data[1]
        if cmd in VI_COMMANDS:
            weechat.command('', "%s %s" % (VI_COMMANDS[cmd], args))
        else:
            weechat.command('', "/{} {}".format(cmd, args))
    return weechat.WEECHAT_RC_OK


# Pressed keys handling.
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
    if last_signal_time == float(data):
        esc_pressed += 1
        set_mode("NORMAL")
        # Cancel any current partial commands.
        vi_buffer = ''
        catching_keys_data = {'amount': 0}
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

def cb_key_combo_default(data, signal, signal_data):
    """Eat and handle key events when in normal mode, if needed.

    The key_combo_default signal is sent when a key combo is pressed. For
    example, alt-k will send the '\x01[k' signal.

    Esc is handled a bit differently to avoid delays, see cb_key_pressed(…).
    """
    global esc_pressed, vi_buffer, cmd_text

    # If Esc was pressed, strip the Esc part from the pressed keys.
    # Example: user presses Esc followed by i. This is detected as "\x01[i",
    # but we only want to handle "i".
    keys = signal_data
    if esc_pressed and keys.startswith("\x01[" * esc_pressed):
        keys = keys[2*esc_pressed:]
        # Multiples of 3 seem to "cancel" themselves
        # e.g. Esc-Esc-Esc-Alt-j-11 is detected as "\x01[\x01[\x01" followed by
        # "\x01[j11" (two different signals).
        if signal_data == "\x01[" * 3:
            esc_pressed = -1 # Because cb_check_esc will increment it to 0
        else:
            esc_pressed = 0
    elif keys == "\x01@":
        set_mode("NORMAL")
        return weechat.WEECHAT_RC_OK_EAT

    # Nothing to do here.
    if mode == "INSERT":
        return weechat.WEECHAT_RC_OK

    # We're in Replace mode — allow 'normal' key presses (e.g. 'a') and
    # overwrite the next character with them, but let the other key presses
    # pass normally (e.g. backspace, arrow keys, etc).
    if mode == "REPLACE":
        if len(keys) == 1:
            weechat.command('', "/input delete_next_char")
        elif keys == "\x01?":
            weechat.command('', "/input move_previous_char")
            return weechat.WEECHAT_RC_OK_EAT
        return weechat.WEECHAT_RC_OK

    # We're catching keys! Only 'normal' key presses interest us (e.g. 'a'),
    # not complex ones (e.g. backspace).
    if len(keys) == 1 and catching_keys_data['amount']:
        catching_keys_data['keys'] += keys
        catching_keys_data['amount'] -= 1
        # Done catching keys, execute the callback.
        if catching_keys_data['amount'] == 0:
            globals()[catching_keys_data['callback']]()
            vi_buffer = ''
            weechat.bar_item_update("vi_buffer")
        return weechat.WEECHAT_RC_OK_EAT

    # We're in command-line mode.
    if cmd_text:
        # Backspace key.
        if keys == "\x01?":
            # Remove the last character from our command line.
            cmd_text = list(cmd_text)
            del cmd_text[-1]
            cmd_text = ''.join(cmd_text)
        # Return key.
        elif keys == "\x01M":
            weechat.hook_timer(1, 0, 1, "cb_exec_cmd", cmd_text)
            cmd_text = ''
        # Input.
        elif len(keys) == 1:
            cmd_text += keys
        # Update (and maybe hide) the bar item.
        weechat.bar_item_update("cmd_text")
        if not cmd_text:
            weechat.command('', "/bar hide vi_cmd")
        return weechat.WEECHAT_RC_OK_EAT
    # Enter command mode.
    elif keys == ':':
        cmd_text += ':'
        weechat.command('', "/bar show vi_cmd")
        weechat.bar_item_update("cmd_text")
        return weechat.WEECHAT_RC_OK_EAT

    # Add key to the buffer.
    vi_buffer += keys
    weechat.bar_item_update("vi_buffer")
    if not vi_buffer:
        return weechat.WEECHAT_RC_OK

    # Keys without the count. These are the actual keys we should handle.
    # The count, if any, will be removed from vi_keys just below.
    # After that, vi_buffer is only used for display purposes — only vi_keys is
    # checked for all the handling.
    vi_keys = vi_buffer

    # Look for a potential match (e.g. 'd' might become 'dw' or 'dd' so we
    # accept it, but 'd9' is invalid).
    # If no matches are found, the keys buffer is cleared.
    match = False
    # Digits are allowed at the beginning (repeats or '0').
    repeat = 0
    if vi_buffer.isdigit():
        match = True
    elif vi_buffer and vi_buffer[0].isdigit():
        repeat = ''
        for char in vi_buffer:
            if char.isdigit():
                repeat += char
            else:
                break
        vi_keys = vi_buffer.replace(repeat, '', 1)
        repeat = int(repeat)
    # Check against defined keys.
    if not match:
        for key in VI_KEYS:
            if key.startswith(vi_keys):
                match = True
                break
    # Check against defined motions.
    if not match:
        for motion in VI_MOTIONS:
            if motion.startswith(vi_keys):
                match = True
                break
    # Check against defined operators + motions.
    if not match:
        for operator in VI_OPERATORS:
            if vi_keys.startswith(operator):
                for motion in VI_MOTIONS:
                    if motion.startswith(vi_keys[1:]):
                        match = True
                        break
    # No match found — clear the keys buffer.
    if not match:
        vi_buffer = ''
        return weechat.WEECHAT_RC_OK_EAT

    buf = weechat.current_buffer()
    input_line = weechat.buffer_get_string(buf, 'input')
    cur = weechat.buffer_get_integer(buf, "input_pos")

    # It's a key. If the corresponding value is a string, we assume it's a
    # WeeChat command. Otherwise, it's a method we'll call.
    if vi_keys in VI_KEYS:
        if isinstance(VI_KEYS[vi_keys], str):
            for _ in range(max(1, repeat)):
                # This is to avoid crashing WeeChat on script reloads/unloads,
                # because no hooks must still be running when a script is
                # reloaded or unloaded.
                if VI_KEYS[vi_keys] == "/input return":
                    return weechat.WEECHAT_RC_OK
                weechat.command('', VI_KEYS[vi_keys])
                current_cur = weechat.buffer_get_integer(buf, "input_pos")
                set_cur(buf, input_line, current_cur)
        else:
            VI_KEYS[vi_keys](buf, input_line, cur, repeat)
    # It's a motion (e.g. 'w') — call the function "motion_X" where X is the
    # motion, then set the cursor's position to what that function returned.
    elif vi_keys in VI_MOTIONS:
        if vi_keys in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys]
        else:
            func = "motion_%s" % vi_keys
        end, _ = globals()[func](input_line, cur, repeat)
        set_cur(buf, input_line, end)
    # It's an operator + motion (e.g. 'dw') — call the function "motion_X"
    # where X is the motion, then we call the function "operator_Y" where Y is
    # the operator, with the position "motion_X" returned. The "operator_Y"
    # then handles changing the input line.
    elif (len(vi_keys) > 1 and
          vi_keys[0] in VI_OPERATORS and
          vi_keys[1:] in VI_MOTIONS):
        if vi_keys[1:] in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys[1:]]
        else:
            func = "motion_%s" % vi_keys[1:]
        pos, overwrite = globals()[func](input_line, cur, repeat)
        oper = "operator_%s" % vi_keys[0]
        globals()[oper](buf, input_line, cur, pos, overwrite)
    # The combo isn't completed yet (e.g. just 'd').
    else:
        return weechat.WEECHAT_RC_OK_EAT

    # We've already handled the key combo, so clear the keys buffer.
    if not catching_keys_data['amount']:
        vi_buffer = ''
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK_EAT


# Callbacks for the help buffer (/vimode).
def cb_help_closed(data, buf):
    """The help buffer has been closed."""
    global help_buf
    help_buf = None
    return weechat.WEECHAT_RC_OK

def cb_vimode_cmd(data, buf, args):
    """Show the script's help."""
    global help_buf
    if not args or args == "help":
        if help_buf is None:
            help_buf = weechat.buffer_new("vimode", '', '', "cb_help_closed",
                                          '')
            weechat.command(help_buf, "/buffer set time_for_each_line 0")
        buf_num = weechat.buffer_get_integer(help_buf, "number")
        weechat.command('', "/buffer %s" % buf_num)
        weechat.prnt(help_buf, HELP_TEXT)
        weechat.command(help_buf, "/window scroll_top")
    elif args.startswith("bind_keys"):
        weechat.infolist_reset_item_cursor(infolist)
        commands = ["/key unbind ctrl-W",
                    "/key bind ctrl-^ /input jump_last_buffer",
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
            if re.match(r"meta-\wmeta-", key):
                commands.append("/key unbind %s" % key)
        if args == "bind_keys":
            weechat.prnt('', "Running commands:")
            for command in commands:
                weechat.command('', command)
            weechat.prnt('', "Done.")
        elif args == "bind_keys --list":
            weechat.prnt('', "Listing commands we'll run:")
            for command in commands:
                weechat.prnt('', "    %s" % command)
            weechat.prnt('', "Done.")
    return weechat.WEECHAT_RC_OK


# Warn the user if he's using an unsupported WeeChat version
VERSION = weechat.info_get("version_number", '')
if int(VERSION) < 0x01000000:
    weechat.prnt('', ("%svimode: please upgrade to WeeChat ≥ 1.0.0. Previous"
                      " versions are not supported." % weechat.color("red")))

# Warn the user about problematic key bindings that may conflict with vimode.
# For example: meta-wmeta-s is bound by default to /window swap.
#    If the user pressed Esc-w, WeeChat will detect it as meta-w and will not
#    send any signal to cb_key_combo_default just yet, since it's the beginning
#    of a known key combo.
#    Instead, cb_key_combo_default will receive the Esc-ws signal, which
#    becomes "ws" after removing the Esc part, and won't know how to handle it.
# The solution is to remove these key bindings, but that's up to the user.
infolist = weechat.infolist_get("key", '', "default")
problematic_keybindings = []
while weechat.infolist_next(infolist):
    key = weechat.infolist_string(infolist, "key")
    command = weechat.infolist_string(infolist, "command")
    if re.match(r"meta-\wmeta-", key):
        problematic_keybindings.append("%s -> %s" % (key, command))
if problematic_keybindings:
    weechat.prnt('', ("%sProblematic keybindings detected:" %
                      weechat.color("red")))
    for keybinding in problematic_keybindings:
        weechat.prnt('', "%s    %s" % (weechat.color("red"), keybinding))
    weechat.prnt('', ("%sThese keybindings may conflict with vimode." %
                      weechat.color("red")))
    weechat.prnt('', ("%sYou can remove problematic key bindings and add"
                      " recommended ones by using /vimode bind_keys,"
                      " or only list them with /vimode bind_keys --list" %
                      weechat.color("red")))
    weechat.prnt('', ("%sFor help, see: https://github.com/GermainZ/weechat-"
                      "vimode/blob/master/FAQ.md" % weechat.color("red")))
del problematic_keybindings

# Create bar items and setup hooks.
weechat.bar_item_new("mode_indicator", "cb_mode_indicator", '')
weechat.bar_item_new("cmd_text", "cb_cmd_text", '')
weechat.bar_item_new("vi_buffer", "cb_vi_buffer", '')
vi_cmd = weechat.bar_new("vi_cmd", "off", "0", "root", '', "bottom",
                         "vertical", "vertical", "0", "0", "default",
                         "default", "default", "0", "cmd_text")
weechat.hook_signal("key_pressed", "cb_key_pressed", '')
weechat.hook_signal("key_combo_default", "cb_key_combo_default", '')

weechat.hook_command("vimode", SCRIPT_DESC, "[help | bind_keys [--list]]",
                     "     help: show help\n"
                     "bind_keys: unbind problematic keys, and bind recommended"
                     " keys to use in WeeChat\n"
                     "          --list: only list changes",
                     "help || bind_keys |--list",
                     "cb_vimode_cmd", '')
