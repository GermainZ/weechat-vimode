You can view this help text inside WeeChat by typing `/vimode`

# Description:
Add vi/vim-like modes and keybindings to WeeChat.

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

To switch back to Insert mode, you can use i, a, A, etc.

To execute an Ex command, simply precede it with a ':' while in normal mode,
for example: ":h" or ":s/foo/bar".

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
* `f{char}`         To **[count]**'th occurence of **{char}** to the right.
* `F{char}`         To **[count]**'th occurence of **{char}** to the left.
* `t{char}`         Till before **[count]**'th occurence of **{char}** to the
                    right.
* `T{char}`         Till after **[count]**'th occurence of **{char}** to the
                    left.

### Other:
* `x`               Delete **[count]** characters under and after the cursor.
* `r{char}`         Replace **[count]** characters with **{char}**` under and
                    after the cursor.
* `R`               Enter Replace mode. Counts are not supported.
* `dd`              Delete line.
* `cc`              Delete line and start insert.
* `yy`              Yank line to clipboard. Requires xsel.
* `I`               Insert text before the first non-blank in the line.
* `p`               Put the text from the clipboard after the cursor. Requires
                    xsel.

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
* `:!{cmd}`         Execute shell command (`/exec -buffer shell`)
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
                    Improved substitutions (:s/foo/bar). Rewrote key handling
                    logic to take advantage of WeeChat API additions.
                    Many fixes and improvements. WeeChat ≥ 1.0.0 required.
