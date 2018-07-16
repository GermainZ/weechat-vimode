# Description:
Add vi/vim-like modes and keybindings to WeeChat.


# Download:
weechat-vimode is available in the WeeChat scripts repo. You can install it by
running the following command:

    /script install vimode.py

The version on GitHub may be more recent. You can install it from the shell as
follows:

    cd ~/.weechat/python/
    wget 'https://github.com/GermainZ/weechat-vimode/raw/master/vimode.py'
    cd autoload/
    ln -s ../vimode.py .

If you prefer to clone the git repo (allowing you to easily update it), you can
do the following instead:

    git clone 'https://github.com/GermainZ/weechat-vimode.git'
    ln -s /path/to/git/repo/vimode.py ~/.weechat/python/autoload/vimode.py


# Screencast:
[![weechat-vimode screencast (webm; 7.63M](https://ptpb.pw/be75e2b38eb743a29682ca60e6768ab8d0418250.png)](https://ptpb.pw/a826c31608ec80d0eed229b8747b2bdd27b92ca3.webm)

# Usage:
To switch to Normal mode, press `Esc` or `Ctrl+Space`. You can also use an
alternate mapping while in Insert mode, similar to `:image jk <Esc>` in vim.
See the `imap_esc` and `imap_esc_timeout` options for more details.

Two bar items are provided:

* **mode_indicator**: shows the currently active mode (e.g. `NORMAL`).
* **vi_buffer**: shows partial commands (e.g. `df`).

You can add them to your input bar. For example:

* `/fset weechat.bar.input.items`
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
take you to the appropriate line. You can then use the default key bindings to
quote the message (`Q`, `m` and `q`).


# Enabling vim-like search:
By default, pressing `/` will simply launch WeeChat's search mode.

Optionally, weechat-vimode can also handle `n`/`N` presses after pressing `/`
and confirming the query. To enable this setting:
`/set plugins.var.python.vimode.search_vim on`.
Note that having this setting enabled will require an extra `<Enter>` press to
exit search mode (where only `n`/`N` are recognized and handled) and return to
Normal mode.


# Current key bindings:

## Input line:

### Operators:
* `d{motion}`       Delete text that **{motion}** moves over.
* `c{motion}`       Delete **{motion}** text and start Insert mode.
* `y{motion}`       Yank **{motion}** text to clipboard. Uses xclip by default.
                    You can change this with the `copy\_clipboard\_cmd` option.

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
* `f{char}`         To **[count]**'th occurrence of **{char}** to the right.
* `F{char}`         To **[count]**'th occurrence of **{char}** to the left.
* `t{char}`         Till before **[count]**'th occurrence of **{char}** to the
                    right.
* `T{char}`         Till after **[count]**'th occurrence of **{char}** to the
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
* `yy`              Yank line to clipboard. Uses xclip by default. You can
                    change this with the `copy\_clipboard\_cmd` option.
* `I`               Insert text before the first non-blank in the line.
* `p`               Put the text from the clipboard after the cursor. Uses
                    xclip by default. You can change this with the
                    `paste\_clipboard\_cmd` option.
* `nt`              Scroll nicklist up.
* `nT`              Scroll nicklist down.

## Buffers:
* `j`               Scroll buffer down. \*
* `k`               Scroll buffer up. \*
* `^U`              Scroll buffer page up. \*
* `^D`              Scroll buffer page down. \*
* `gt` or `K`       Go to the previous buffer.
* `gT` or `J`       Go to the next buffer.
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
* `:h`, `:help`     Help (`/help`)
* `:set`            Set WeeChat config option (`/set`)
* `:q`, `:quit`     Closes current buffer (`/close`)
* `:qa`, `:qall`, `:quita`, `:quitall`
                    Exits WeeChat (`/exit`)
* `:w`, `:write`    Saves settings (`/save`)
* `:bN`, `:bNext`, `:bp`, `:bprevious`
                    Go to the previous buffer (`/buffer -1`).
* `:bn`, `:bnext`   Go to the next buffer (`/buffer +1`).
* `:bd`, `:bdel`, `:bdelete`
                    Close the current buffer (`/close`).
* `:b#`             Go to the last buffer (`/input jump_last_buffer`).
* `:b [N]`, `:bu [N]`, `:buf [N]`, `:buffer [N]`
                    Go to buffer [N].
* `:sp`, `:split`   Split current window in two (`/window splith`).
* `:vs`, `:vsplit`  Split current window in two, but vertically
                    (`/window splitv`).
* `:!{cmd}`         Execute shell command (`/exec -buffer shell`)
* `:s/pattern/repl`  
  `:s/pattern/repl/g`
                    Search/Replace \*
* `:<num>`          Start cursor mode and go to line.
* `:command`        All other commands will be passed to WeeChat (e.g.
                    ':script …' is equivalent to '/script …').

\* Supports regex (check docs for the Python re module for more
information). `&` in the replacement is also substituted by the pattern. If the
`g` flag isn't present, only the first match will be substituted.


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
* version 0.5:      added: line numbers bar (disabled by default), :<num>
                    commands, C, D. Many fixes and improvements.
* version 0.6:      added python3 support, `:imap <key_sequence> <Esc>`,
                    `/vimode_go_to_normal` for use in user-defined key
                    bindings, nt/nT to scroll nicklist, support for
                    user-defined commands for copying/pasting, simple
                    tab-completion for Ex mode. Flipped J/K and gT/gt. Other
                    bug fixes and improvements.

For the full change log, please check the [list of commits][1].


# Support:
Please report any issues using the [GitHub issue tracker][2]. Also feel free to
suggest new features that you need.

You can contact me on irc.freenode.net in #weechat or via a query (nickname:
GermainZ).

[1]: https://github.com/GermainZ/weechat-vimode/commits/master
[2]: https://github.com/GermainZ/weechat-vimode/issues/new
