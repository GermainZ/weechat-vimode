# Description:
Add vi/vim-like modes and keybindings to WeeChat.

# Screencast

[![weechat-vimode screencast (webm; 7.63M](https://ptpb.pw/be75e2b38eb743a29682ca60e6768ab8d0418250.png)](https://ptpb.pw/a826c31608ec80d0eed229b8747b2bdd27b92ca3.webm)

# Usage:
To switch to Normal mode, press `Esc` or `Ctrl+Space`.

Two bar items are provided:

* **mode_indicator**: shows the currently active mode (e.g. `NORMAL`).
* **vi_buffer**: shows partial commands (e.g. `df`).

You can add them to your input bar. For example, using `iset.pl`:

* `/iset weechat.bar.input.items`
* `<Alt+Enter>`
* Add `[mode_indicator]+` at the start, and `,[vi_buffer]` at the end.
* Final result example:
    `"[mode_indicator]+[input_prompt]+(away),[input_search],
    [input_paste],input_text,[vi_buffer]"`

To switch back to Insert mode, you can use `i`, `a`, `A`, etc.

To execute an Ex command, simply precede it with a ':' while in Normal mode,
for example: ":h" or ":s/foo/bar".

# Showing line numbers:

The `vi_line_numbers` bar (comes with a bar item) is provided but hidden by
default, and can be shown to display line numbers next to the chat window
(similar to vi's `:set number`). You can show it by using the command:
`/set weechat.bar.vi_line_numbers.hidden on`.

(Depending on your configuration, you may need to adjust some of its settings
for it to be displayed correctly, but the defaults should suit most users.)

It is useful for `:<num>` commands, which will start WeeChat's cursor mode and
take you to the appropriate line. You can then use the default key bindings
to quote the message (`Q`, `m` and `q`).

# Current key bindings:

## Input line:

### Operators:
* `d{motion}`       Delete text that **{motion}** moves over.
* `c{motion}`       Delete **{motion}** text and start Insert mode.
* `y{motion}`       Yank **{motion}** text to clipboard.

### Motions:
* `h`               **[count]** characters to the left exclusive.
* `l`               **[count]** characters to the right exclusive.
* `w`               **[count]** words forward exclusive.
* `W`               **[count]** WORDS forward exclusive.
* `b`               **[count]** words backward.
* `B`               **[count]** WORDS backward.
* `ge`              Backward to the end of word **[count]** inclusive.
* `gE`              Backward to the end of WORD **[count]** inclusive.
* `e`               Forward to the end of word **[count]** inclusive.
* `E`               Forward to the end of WORD **[count]** inclusive.
* `0`               To the first character of the line.
* `^`               To the first non-blank character of the line exclusive.
* `$`               To the end of the line exclusive.
* `f{char}`         To **[count]**'th occurence of **{char}** to the right.
* `F{char}`         To **[count]**'th occurence of **{char}** to the left.
* `t{char}`         Till before **[count]**'th occurence of **{char}** to the
                    right.
* `T{char}`         Till after **[count]**'th occurence of **{char}** to the
                    left.

### Other:
* `<Space>`         **[count]** characters to the right.
* `<BS>`            **[count]** characters to the left.
* `x`               Delete **[count]** characters under and after the cursor.
* `X`               Delete **[count]** characters before the cursor.
* `~`               Switch case of the character under the cursor.
* `;`               Repeat latest f, t, F or T **[count]** times.
* `,`               Repeat latest f, t, F or T in opposite direction
                    **[count]** times.
* `r{char}`         Replace **[count]** characters with **{char}**` under and
                    after the cursor.
* `R`               Enter Replace mode. Counts are not supported.
* `dd`              Delete line.
* `D`               Delete the characters under the cursor until the end of the
                    line.
* `cc`              Delete line and start Insert mode.
* `C`               Delete from the cursor position to the end of the line,
                    and start Insert mode.
* `yy`              Yank line to clipboard. Requires xclip.
* `I`               Insert text before the first non-blank in the line.
* `p`               Put the text from the clipboard after the cursor. Requires
                    xclip.

## Buffers:
* `j`               Scroll buffer up. \*
* `k`               Scroll buffer down. \*
* `^U`              Scroll buffer page up. \*
* `^D`              Scroll buffer page down. \*
* `gt` or `K`       Go to the next buffer.
* `gT` or `J`       Go to the previous buffer.
* `gg`              Goto first line.
* `G`               Goto line **[count]**, default last line. \*
* `/`               Launch WeeChat search mode
* `^^`              Jump to the last buffer.

\* Counts may not work as intended, depending on the value of
`weechat.look.scroll_amount` and `weechat.look.scroll_page_percent`.

## Windows:
* `^Wh`             Go to the window to the left.
* `^Wj`             Go to the window below the current one.
* `^Wk`             Go to the window above the current one.
* `^Wl`             Go to the window to the right.
* `^W=`             Balance windows' sizes.
* `^Wx`             Swap window with the next one.
* `^Ws`             Split current window in two.
* `^Wv`             Split current window in two, but vertically.
* `^Wq`             Quit current window.


# Current commands:
* `:h`              Help (`/help`)
* `:set`            Set WeeChat config option (`/set`)
* `:q`              Closes current buffer (`/close`)
* `:qall`           Exits WeeChat (`/exit`)
* `:w`              Saves settings (`/save`)
* `:bp`             Go to the previous buffer (`/buffer -1`).
* `:bn`             Go to the next buffer (`/buffer +1`).
* `:bd`             Close the current buffer (`/close`).
* `:b#`             Go to the last buffer (`/input jump_last_buffer`).
* `:b [N]`          Go to buffer [N].
* `:sp`             Split current window in two (`/window splith`).
* `:vsp`            Split current window in two, but vertically
                    (`/window splitv`).
* `:!{cmd}`         Execute shell command (`/exec -buffer shell`)
* `:s/pattern/repl`
* `:s/pattern/repl/g`
                    Search/Replace \*
* `:<num>`          Start cursor mode and go to line.
* `:command`        All other commands will be passed to WeeChat (e.g.
                    ':script …' is equivalent to '/script …').

\* Supports regex (check docs for the Python re module for more
information). `&` in the replacement is also substituted by the pattern. If
the `g` flag isn't present, only the first match will be substituted.

# History:
* version 0.1:      initial release
* version 0.2:      added esc to switch to Normal mode, various key bindings
                    and commands.
* version 0.2.1:    fixes/refactoring
* version 0.3:      separate operators from motions and better handling. Added
                    yank operator, I/p. Other fixes and improvements. The
                    Escape key should work flawlessly on WeeChat ≥ 0.4.4.
* version 0.4:      added: f, F, t, T, r, R, W, E, B, gt, gT, J, K, ge, gE, X,
                    ~, ,, ;, ^^, ^Wh, ^Wj, ^Wk, ^Wl, ^W=, ^Wx, ^Ws, ^Wv, ^Wq,
                    :!cmd, :sp, :vsp.
                    Improved substitutions (:s/foo/bar). Rewrote key handling
                    logic to take advantage of WeeChat API additions.
                    Many fixes and improvements. WeeChat ≥ 1.0.0 required.
