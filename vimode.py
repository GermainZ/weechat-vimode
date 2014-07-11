# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Germain Z. <germanosz@gmail.com>
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

import weechat
import re
import time
from subprocess import Popen, PIPE
from StringIO import StringIO
from csv import reader


# Type '/vimode' in WeeChat to view this help formatted text.
help_text = """
Github repo: {url}https://github.com/GermainZ/weechat-vimode

{header}Description:
An attempt to add a vi-like mode to WeeChat, which provides some common vi \
key bindings and commands, as well as normal/insert modes.

{header}Usage:
To switch to Normal mode, press Ctrl + Space. The Escape key can be used as \
well. The Esc key will conflict with existing key bindings (e.g. Esc followed \
by 'd' will be detected as meta-d) for WeeChat ≤ 0.4.3.
It works as expected for WeeChat ≥ 0.4.4. You can get the latest WeeChat from \
{url}http://weechat.org/download/devel/

You can use the {bold}mode_indicator{reset} bar item to view the current mode.

To switch back to Insert mode, you can use i/a/A (or the c operator.)
To execute a command, simply precede it with a ':' while in normal mode, \
for example: ":h" or ":s/foo/bar".

{header}Current key bindings:
{header2}Input line:
{header3}Operators:
d{com}{{motion}}{reset}   Delete text that {com}{{motion}}{reset} moves over.
c{com}{{motion}}{reset}   Delete {com}{{motion}}{reset} text and start insert.
y{com}{{motion}}{reset}   Yank {com}{{motion}}{reset} text to clipboard.
{header3}Motions:
h    {com}[count]{reset} characters to the left exclusive.
l    {com}[count]{reset} characters to the right exclusive.
w    {com}[count]{reset} words forward exclusive.
b    {com}[count]{reset} words backward.
e    Forward to the end of word {com}[count]{reset} inclusive.
0    To the first character of the line.
^    To the first non-blank character of the line exclusive.
$    To the end of the line exclusive.
{header3}Other:
x    Delete {com}[count]{reset} characters under and after the cursor.
dd   Delete line.
cc   Delete line and start insert.
yy   Yank line.
I    Insert text before the first non-blank in the line.
p    Put the text from the clipboard after the cursor.
{header2}Buffer:
j    Scroll buffer up. {note}
k    Scroll buffer down. {note}
gt   Go to the next buffer.
     (or K)
gT   Go to the previous buffer.
     (or J)
gg   Goto first line.
G    Goto line {com}[count]{reset}, default last line. {note}
/    Launch WeeChat search mode
{note} Counts may not work as intended, depending on the value of \
weechat.look.scroll_amount.

{todo} u W B r R % f F   ||   better search (/), add: n N ?
{todo} .

{header}Current commands:
:h                  Help ({bold}/help{reset})
:set                Set WeeChat config option ({bold}/set{reset})
:q                  Closes current buffer ({bold}/close{reset})
:qall               Exits WeeChat ({bold}/exit{reset})
:w                  Saves settings ({bold}/save{reset})
:s/pattern/repl
:s/pattern/repl/g   Search/Replace {note}
{note} Supports regex (check docs for the Python re module for more \
information). '&' in the replacement is also substituted by the pattern. If \
the 'g' flag isn't present, only the first match will be substituted.
{todo} :! (probably using shell.py)
{todo} :w <file> saves buffer's contents to file
{todo} :r <file> puts file's content in input line/open in buffer?
{todo} Display matching commands with (basic) help, like Penta \
and Vimp do.

{header}History:
{header2}version 0.1:{reset}   initial release
{header2}version 0.2:{reset}   added esc to switch to normal mode, various key \
bindings and commands.
{header2}version 0.2.1:{reset} fixes/refactoring
{header2}version 0.3:{reset}   separate operators from motions and better \
handling. Added yank operator, I/p. Other fixes and improvements. The Escape \
key should work flawlessly on WeeChat ≥ 0.4.4.
""".format(header=weechat.color("red"), header2=weechat.color("lightred"),
           header3=weechat.color("brown"), url=weechat.color("cyan"),
           todo="%sTODO:%s" % (weechat.color("blue"), weechat.color("reset")),
           note="%s*%s" % (weechat.color("red"), weechat.color("reset")),
           bold=weechat.color("bold"), reset=weechat.color("reset"),
           com=weechat.color("green"))


SCRIPT_NAME = "vimode"
SCRIPT_AUTHOR = "GermainZ <germanosz@gmail.com>"
SCRIPT_VERSION = "0.3"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = ("An attempt to add a vi-like mode to WeeChat, which adds some"
               " common vi key bindings and commands, as well as normal/insert"
               " modes.")

# Initialize variables:
input_line = '' # used to communicate between functions, when only passing a
                # single string is allowed (e.g. for weechat.hook_timer).
cmd_text = '' # holds the text of the command line.
mode = "INSERT" # mode we start in (INSERT or COMMAND), insert by default.
pressed_keys = '' # holds any pressed keys, regardless of their type.
vi_buffer = '' # holds 'printable' pressed keys (e.g. arrow keys aren't added).
last_time = time.time() # used to check if pressed_keys and vi_buffer need to
                        # be reset.
num = r"[0-9]*" # simple regex to detect number of repeats in keystrokes such
                # as "d2w"

# Some common vi commands.
# Others may be present in exec_cmd:
vi_commands = {'h': "/help", 'qall': "/exit", 'q': "/close", 'w': "/save",
               'set': "/set"}

def get_pos(data, regex, cur):
    """Get the position of the first match in data, starting at cur."""
    matches = [m.start() for m in re.finditer(regex, data[cur+1:])]
    if len(matches) > 1 and matches[0] == 0:
        pos = matches[1] + 1
    elif len(matches) > 0 and matches[0] != 0:
        pos = matches[0] + 1
    else:
        pos = len(data)
    return pos

def set_cur(buf, pos):
    """Set the cursor's position."""
    weechat.buffer_set(buf, "input_pos", str(pos))
    pass

def operator_d(buf, input_line, pos1, pos2, overwrite=False):
    """Simulate the behavior of the 'd' operator. Remove everything between two
    positions from the input line.

    If overwrite is set to True, the character at the cursor's new position is
    removed as well (pos2 is inclusive.)"""
    start = min([pos1, pos2])
    end = max([pos1, pos2])
    if overwrite:
        end += 1
    input_line = list(input_line)
    del input_line[start:end]
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)

def operator_c(buf, input_line, pos1, pos2, overwrite=False):
    """Simulate the behavior of the 'c' operator."""
    operator_d(buf, input_line, pos1, pos2, overwrite)
    set_mode("INSERT")

def operator_y(buf, input_line, pos1, pos2, overwrite=False):
    """Simulate the behavior of the 'y' operator."""
    start = min([pos1, pos2])
    end = max([pos1, pos2])
    p = Popen(['xsel', '-pi'], stdin=PIPE)
    p.communicate(input=input_line[start:end])

def motion_w(input_line, cur):
    """Return the new position of the cursor after the 'w' motion."""
    pos = get_pos(input_line, r"\b\w", cur)
    return cur+pos, False

def motion_e(input_line, cur):
    """Return the new position of the cursor after the 'e' motion."""
    pos = get_pos(input_line, r"\w\b", cur)
    return cur+pos, True

def motion_b(input_line, cur):
    """Return the new position of the cursor after the 'b' motion."""
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], r"\w\b", new_cur)
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_h(input_line, cur):
    """Return the new position of the cursor after the 'h' motion."""
    return cur-1, False

def motion_l(input_line, cur):
    """Return the new position of the cursor after the 'l' motion."""
    return cur+1, False

def motion_carret(input_line, cur):
    """Return the new position of the cursor after the '^' motion."""
    pos = get_pos(input_line, r"\S", 0)
    return pos, False

def motion_dollar(input_line, cur):
    """Return the new position of the cursor after the '$' motion."""
    pos = len(input_line)
    return pos, False


def key_cc(buf, input_line, cur, repeat):
    """Simulate vi's behavior for cc."""
    weechat.command('', "/input delete_line")
    set_mode("INSERT")

def key_yy(buf, input_line, cur, repeat):
    """Simulate vi's behavior for yy."""
    p = Popen(['xsel', '-pi'], stdin=PIPE)
    p.communicate(input=input_line)

def key_I(buf, input_line, cur, repeat):
    """Simulate vi's behavior for I."""
    pos, _ = motion_carret(input_line, cur)
    set_cur(buf, pos)
    set_mode("INSERT")

def key_G(buf, input_line, cur, repeat):
    """Simulate vi's behavior for the G key."""
    if repeat > 0:
        # This is necessary to prevent weird scroll jumps.
        weechat.command('', "/window scroll_bottom")
        weechat.command('', "/window scroll %s" % repeat)
    else:
        weechat.command('', "/window scroll_bottom")

# Common vi key bindings. If the value is a string, it's assumed it's a WeeChat
# command, and a function otherwise.
vi_keys = {'j': "/window scroll_down",
           'k': "/window scroll_up",
           'G': key_G,
           'gg': "/window scroll_top",
           'x': "/input delete_next_char",
           'dd': "/input delete_line",
           'cc': key_cc,
           'I': key_I,
           'yy': key_yy,
           'p': "/input clipboard_paste",
           '0': "/input move_beginning_of_line",
           '/': "/input search_text",
           'gt': "/buffer +1",
           'K': "/buffer +1",
           'gT': "/buffer -1",
           'J': "/buffer -1"}
# Vi operators. Each operator must have a corresponding function,
# called "operator_X" where X is the operator. For example: "operator_c"
vi_operators = ['c', 'd', 'y']
# Vi motions. Each motion must have a corresponding function, called "motion_X"
# where X is the motion.
vi_motions = ['w', 'e', 'b', '^', '$', 'h', 'l', '0']
# Special characters for motions. The corresponding function's name is converted
# before calling. For example, '^' will call 'motion_carret' instead of
# 'motion_^' (which isn't allowed because of illegal characters.)
special_chars = {'^': "carret", '$': "dollar"}


def set_mode(arg):
    """Set the current mode and update the bar mode indicator."""
    global mode
    mode = arg
    weechat.bar_item_update("mode_indicator")

def vi_buffer_cb(data, item, window):
    """Return the content of the vi buffer (pressed keys on hold)."""
    return vi_buffer

def cmd_text_cb(data, item, window):
    """Return the text of the command line."""
    return cmd_text

def mode_indicator_cb(data, item, window):
    """Return the current mode (INSERT/COMMAND)."""
    return mode

def exec_cmd(data, remaining_calls):
    """Translate and execute our custom commands to WeeChat command, with
    any passed arguments.

    input_line is set in key_pressed_cb and is used here to restore its value
    if we want, along with any potential replacements that should be made (e.g.
    for s/foo/bar type commands).

    """
    global input_line
    data = list(data)
    del data[0]
    data = ''.join(data)
    # s/foo/bar command
    if data.startswith("s/"):
        cmd = data
        parsed_cmd = next(reader(StringIO(cmd), delimiter='/',
                                 escapechar='\\'));
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
        input_line = re.sub(pattern, repl, input_line, count)
        weechat.buffer_set(buf, "input", input_line)
    # Check againt defined commands
    else:
        data = data.split(' ', 1)
        cmd = data[0]
        args = ''
        if len(data) == 2:
            args = data[1]
        if cmd in vi_commands:
            weechat.command('', "%s %s" % (vi_commands[cmd], args))
        else:
            weechat.prnt('', "Command '%s' not found." % cmd)
    return weechat.WEECHAT_RC_OK

def input_set(data, remaining_calls):
    """Set the input line's content."""
    buf = weechat.current_buffer()
    weechat.buffer_set(buf, "input", data)
    # move the cursor back to its position prior to setting the content
    weechat.command('', "/input move_next_char")
    return weechat.WEECHAT_RC_OK

def input_rem_char(data, remaining_calls):
    """Remove one character from the input buffer.

    If data is set to 'cursor', the character at the cursor will be removed.
    Otherwise, data must be an integer and the character at that position will
    be removed instead.

    """
    buf = weechat.current_buffer()
    input_line = weechat.buffer_get_string(buf, 'input')
    if data == "cursor":
        data = weechat.buffer_get_integer(buf, "input_pos")
    input_line = list(input_line)
    try:
        del input_line[int(data - 1)]
    # Not sure why nothing is being detected in some cases from the first time
    except IndexError:
        weechat.hook_timer(1, 0, 1, "input_rem_char", "cursor")
        return weechat.WEECHAT_RC_OK
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    # move the cursor back to its position before removing our character
    weechat.command('', "/input move_previous_char")
    return weechat.WEECHAT_RC_OK

def handle_esc(data, remaining_calls):
    """Esc acts as a modifier and usually waits for another keypress.

    To circumvent that, simulate a keypress then remove what was inserted.

    """
    global cmd_text
    weechat.command('', "/input insert %s" % data)
    weechat.hook_signal_send("key_pressed", weechat.WEECHAT_HOOK_SIGNAL_STRING,
                            data)
    if cmd_text == ":[":
        cmd_text = ':'
    return weechat.WEECHAT_RC_OK

esc_pressed = False
def pressed_keys_check(data, remaining_calls):
    """Check the pressed keys and changes modes or detects bound keys
    accordingly.

    """
    global pressed_keys, mode, vi_buffer, esc_pressed
    # If the last pressed key was Escape, this one will be detected as an arg
    # as Escape acts like a modifier (pressing Esc, then pressing i is detected
    # as pressing meta-i). We'll emulate it being pressed again, so that the
    # user's input is actually processed normally.
    if esc_pressed is True:
        esc_pressed = False
        weechat.hook_timer(50, 0, 1, "handle_esc", pressed_keys[-1])
    if mode == "INSERT":
        # Ctrl + Space, or Escape
        if pressed_keys == "@" or pressed_keys == "[":
            set_mode("NORMAL")
            if pressed_keys == "[":
                esc_pressed = True
    elif mode == "NORMAL":
        # We strip all numbers and check if the the combo is recognized below,
        # then extract the numbers, if any, and pass them as the repeat factor.
        buffer_stripped = re.sub(num, '', vi_buffer)
        if vi_buffer in ['i', 'a', 'A']:
            set_mode("INSERT")
            if vi_buffer == 'a':
                weechat.command('', "/input move_next_char")
            elif vi_buffer == 'A':
                weechat.command('', "/input move_end_of_line")
        # Pressing only '0' should not be detected as a repeat count.
        elif vi_buffer == '0':
            weechat.command('', vi_keys['0'])
        # Quick way to detect repeats (e.g. d5w). This isn't perfect, as things
        # like "5d2w1" are detected as "dw" repeated 521 times, but it should
        # be alright as long as the user doesn't try to break it on purpose.
        # Maximum number of repeats performed is 10000.
        elif len(buffer_stripped) > 0:
            repeat = ''.join(re.findall(num, vi_buffer))
            if len(repeat) > 0:
                repeat = min([int(repeat), 10000])
            else:
                repeat = 0
            buf = weechat.current_buffer()
            input_line = weechat.buffer_get_string(buf, 'input')
            cur = weechat.buffer_get_integer(buf, "input_pos")
            # First, the key combo is checked against the vi_keys dict which can
            # contain WeeChat commands (as strings) or Python functions.
            if buffer_stripped in vi_keys:
                if isinstance(vi_keys[buffer_stripped], str):
                    for _ in range(1 if repeat == 0 else repeat):
                        weechat.command('', vi_keys[re.sub(num, '', vi_buffer)])
                else:
                    vi_keys[buffer_stripped](buf, input_line, cur, repeat)
            # We then check if the pressed key is a motion (e.g. 'w')
            # If it is, we call the function "motion_X" where X is the motion,
            # then set the cursor's position to what the function returned.
            elif buffer_stripped[0] in vi_motions:
                for _ in range(1 if repeat == 0 else repeat):
                    input_line = weechat.buffer_get_string(buf, 'input')
                    cur = weechat.buffer_get_integer(buf, "input_pos")
                    if buffer_stripped[0] in special_chars:
                        func = "motion_%s" % special_chars[buffer_stripped[0]]
                    else:
                        func = "motion_%s" % buffer_stripped[0]
                    end, _ = globals()[func](input_line, cur)
                    set_cur(buf, end)
            # And finally, if it's an operator + motion (e.g. 'dw')
            # If it is, we call the function "motion_X" where X is the motion,
            # then we call the function "operator_Y" where Y is the operator,
            # with the position "motion_X" returned. The "operator_Y" then
            # handles changing the input line.
            elif (len(buffer_stripped) > 1 and
                    buffer_stripped[0] in vi_operators and
                    buffer_stripped[1] in vi_motions):
                for _ in range(1 if repeat == 0 else repeat):
                    input_line = weechat.buffer_get_string(buf, 'input')
                    cur = weechat.buffer_get_integer(buf, "input_pos")
                    if buffer_stripped[1] in special_chars:
                        func = "motion_%s" % special_chars[buffer_stripped[1]]
                    else:
                        func = "motion_%s" % buffer_stripped[1]
                    pos, overwrite = globals()[func](input_line, cur)
                    oper = "operator_%s" % buffer_stripped[0]
                    globals()[oper](buf, input_line, cur, pos, overwrite)
            else:
                return weechat.WEECHAT_RC_OK
        else:
            return weechat.WEECHAT_RC_OK
    clear_vi_buffers()
    return weechat.WEECHAT_RC_OK

def clear_vi_buffers(data=None, remaining_calls=None):
    """Clear both pressed_keys and vi_buffer.

    If data is set to 'check_time', they'll only be cleared if enough time has
    gone by since they've been last set.
    This is useful as this function is called using a timer, so other keys
    might've been pressed before the timer is activated.

    """
    global pressed_keys, vi_buffer
    if data == "check_time" and time.time() < last_time + 1.0:
        return weechat.WEECHAT_RC_OK
    pressed_keys = ''
    vi_buffer = ''
    weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

def is_printing(current, saved):
    """Is the character a visible, printing character that would normally
    show in the input box?

    Previously saved characters are taken into consideration as well for some
    key combinations, such as the arrows, which are detected as three separate
    events (^A[, [ and A/B/C/D).
    The keys buffers will be cleared if the character isn't visible.

    """
    if current.startswith("") or saved.startswith(""):
        weechat.hook_timer(50, 0, 1, "clear_vi_buffers", '')
        return False
    return True

def key_combo_default_cb(data, signal, signal_data):
    """Eat the escape key if needed. Requires WeeChat ≥ 0.4.4.

    The key_combo_default signal is sent when a valid key combo is pressed. For
    example, alt-j12 will send the signal, any single character like 'a' will
    too, but alt-j will send nothing (not a valid combo.)

    This is why key_pressed_cb takes effect before this function when the Esc
    key is pressed. Basically, what happens when the Esc key is pressed is:
        * Esc pressed -> key_pressed_cb is called, and sets the mode to NORMAL.
        * When the user presses another key (e.g. d,) WeeChat detects meta-d
          which is mapped by default to /input delete_next_word.
        * This callback eats that combo, so WeeChat doesn't execute the meta-d
          mapping anymore, and normal mode behaves as expected."""
    # TODO: Eventually drop support for WeeChat < 0.4.4, cleanup all the nasty
    #       workaround that try to make Esc work for these versions, and use
    #       this hook instead and achieve happiness.
    if mode == "NORMAL" and signal_data.startswith("["):
        return weechat.WEECHAT_RC_OK_EAT;
    return weechat.WEECHAT_RC_OK

def key_pressed_cb(data, signal, signal_data):
    """Handle key presses.

    Make sure inputted keys are removed from the input bar and added to the
    appropriate keys buffers or to the command line if it's active, activate it
    when needed, etc.

    """
    global pressed_keys, last_time, cmd_text, input_line, vi_buffer
    if mode == "NORMAL":
        # The character is a printing character, so we'll want to remove it
        # so it doesn't add up to the normal input box.
        if is_printing(signal_data, pressed_keys):
            weechat.hook_timer(1, 0, 1, "input_rem_char", "cursor")
        # It's a command!
        if signal_data == ':':
            cmd_text += ':'
        # Command line is active, so we want to check for some special keys
        # to modify (backspace/normal keys) or submit (Return key) our command.
        elif cmd_text != '':
            # Backspace key
            if signal_data == "?":
                buf = weechat.current_buffer()
                input_line = weechat.buffer_get_string(buf, 'input')
                # Remove the last character from our command line
                cmd_text = list(cmd_text)
                del cmd_text[-1]
                cmd_text = ''.join(cmd_text)
                # We can't actually eat these keystrokes, so simply removing
                # the last character would result in the last two characters
                # being removed (once by the backspace key, once by our script)
                # Instead, we'll just set the input line in a millisecond to
                # its original value, leaving it untouched.
                weechat.hook_timer(1, 0, 1, "input_set", input_line)
            # Return key
            elif signal_data == "M":
                buf = weechat.current_buffer()
                # Clear the input line, therefore nullifying the effect of the
                # Return key, then set it back a millisecond later.
                # This leaves the input box untouched and allows us to execute
                # the command filled in in our command line.
                # We can only pass strings as data using hook_timer, so we'll
                # use the global variable input_line in our exec_cmd function
                # instead to reset the input box's value.
                input_line = weechat.buffer_get_string(buf, 'input')
                weechat.buffer_set(buf, "input", '')
                weechat.hook_timer(1, 0, 1, "exec_cmd", cmd_text)
                cmd_text = ''
            # The key is a normal key, so just append it to our command line.
            elif is_printing(signal_data, pressed_keys):
                cmd_text += signal_data
    # Show the command line when needed, hide it (and update vi_buffer since
    # we'd be looking for keystrokes instead) otherwise.
    if cmd_text != '':
        weechat.command('', "/bar show vi_cmd")
        weechat.bar_item_update("cmd_text")
    else:
        weechat.command('', "/bar hide vi_cmd")
        if is_printing(signal_data, pressed_keys):
            vi_buffer += signal_data
        pressed_keys += signal_data
        # Check for any matching bound keys.
        weechat.hook_timer(1, 0, 1, "pressed_keys_check", '')
        last_time = time.time()
        # Clear the buffers after some time.
        weechat.hook_timer(1000, 0, 1, "clear_vi_buffers", "check_time")
    weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

help_buf = None
def help_closed_cb(data, buffer):
    global help_buf
    help_buf = None
    return weechat.WEECHAT_RC_OK

def help_cb(data, buffer, args):
    global help_buf
    if help_buf is None:
        help_buf = weechat.buffer_new("vimode", '', '', "help_closed_cb", '')
    buf_num = weechat.buffer_get_integer(help_buf, "number")
    weechat.command('', "/buffer %s" % buf_num)
    weechat.prnt(help_buf, help_text)
    return weechat.WEECHAT_RC_OK

weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                 SCRIPT_DESC, '', '')
version = weechat.info_get("version_number", '')
if int(version) < 0x00040400:
    weechat.prnt('', ("%svimode: please upgrade to WeeChat ≥ 0.4.4 to be able"
            " to use the Esc key correctly." % weechat.color("red")))

weechat.bar_item_new("mode_indicator", "mode_indicator_cb", '')
weechat.bar_item_new("cmd_text", "cmd_text_cb", '')
weechat.bar_item_new("vi_buffer", "vi_buffer_cb", '')
vi_cmd = weechat.bar_new("vi_cmd", "off", "0", "root", '', "bottom",
                         "vertical", "vertical", "0", "0", "default",
                         "default", "default", "0", "cmd_text")
weechat.hook_signal("key_pressed", "key_pressed_cb", '')
weechat.hook_signal("key_combo_default", "key_combo_default_cb", '')

weechat.hook_command("vimode", "vimode help", '', '', '', "help_cb", '')
