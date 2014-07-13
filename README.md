You can view this help text inside WeeChat by typing `/vimode`

# Description:
An attempt to add a vi-like mode to WeeChat, which provides some common vi
key bindings and commands, as well as normal/insert modes.

# Usage:
To switch to Normal mode, press Ctrl + Space. The Escape key can be used as
well.

You can use the `mode_indicator` bar item to view the current mode.

To switch back to Insert mode, you can use `i`, `a`, `A`, etc.
To execute a command, simply precede it with a `:` while in normal mode,
for example: `:h` or `:s/foo/bar`.

# Current key bindings:

## Input line:

### Operators:
* `d{motion}`       Delete text that **{motion}** moves over.
* `c{motion}`       Delete **{motion}** text and start insert.
* `y{motion}`       Yank **{motion}** text to clipboard.

### Motions:
* `h`               **[count]** characters to the left exclusive.
* `l`               **[count]** characters to the right exclusive.
* `w`               **[count]** words forward exclusive.
* `W`               **[count]** WORDS forward exclusive.
* `b`               **[count]** words backward.
* `B`               **[count]** WORDS backward.
* `e`               Forward to the end of word **[count]** inclusive.
* `E`               Forward to the end of WORD **[count]** inclusive.
* `0`               To the first character of the line.
* `^`               To the first non-blank character of the line exclusive.
* `$`               To the end of the line exclusive.

### Other:
* `x`               Delete **[count]** characters under and after the cursor.
* `r{char}`         Replace **[count]** characters with **{char}**` under and
                    after the cursor.
* `R`               Enter Replace mode. Counts are not supported.
* `f{char}`         To **[count]**'th occurence of **{char}** to the right.
* `F{char}`         To **[count]**'th occurence of **{char}** to the left.
* `t{char}`         Till before **[count]**'th occurence of **{char}** to the
                    right.
* `T{char}`         Till after **[count]**'th occurence of **{char}** to the
                    left.
* `dd`              Delete line.
* `cc`              Delete line and start insert.
* `yy`              Yank line.
* `I`               Insert text before the first non-blank in the line.
* `p`               Put the text from the clipboard after the cursor.

## Buffer:
* `j`               Scroll buffer up. \*
* `k`               Scroll buffer down. \*
* `gt` or `K`       Go to the next buffer.
* `gT` or `J`       Go to the previous buffer.
* `gg`              Goto first line.
* `G`               Goto line **[count]**, default last line. \*
* `/`               Launch WeeChat search mode

\* Counts may not work as intended, depending on the value of
weechat.look.scroll_amount.

# Current commands:
* `:h`              Help (`/help`)
* `:set`            Set WeeChat config option (`/set`)
* `:q`              Closes current buffer (`/close`)
* `:qall`           Exits WeeChat (`/exit`)
* `:w`              Saves settings (`/save`)
* `:!**{cmd}**`     Execute shell command (`/exec -buffer shell`)
* `:s/pattern/repl`
* `:s/pattern/repl/g`
                    Search/Replace \*

\* Supports regex (check docs for the Python re module for more
information). `&` in the replacement is also substituted by the pattern. If
the `g` flag isn't present, only the first match will be substituted.

# History:
* version 0.1:      initial release
* version 0.2:      added esc to switch to normal mode, various key bindings
                    and commands.
* version 0.2.1:    fixes/refactoring
* version 0.3:      separate operators from motions and better handling. Added
                    yank operator, I/p. Other fixes and improvements. The
                    Escape key should work flawlessly on WeeChat ≥ 0.4.4.
* version 0.4:      added: f, F, t, T, r, R, W, E, B, gt, gT, J, K, :!cmd.
                    Improved substitutions (:s/foo/bar). Many fixes and
                    improvements. WeeChat ≥ 1.0.0 required.
