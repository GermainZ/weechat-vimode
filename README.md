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

If you're using Arch Linux, you can also install
[weechat-vimode-git](https://aur.archlinux.org/packages/weechat-vimode-git/)
from the AUR.


# Screencast:
[![weechat-vimode demo by @gotbletu (YouTube)](https://img.youtube.com/vi/tjHEbfwHlR4/0.jpg)](https://www.youtube.com/watch?v=tjHEbfwHlR4)

# Usage:
To switch to Normal mode, press `Esc` or `Ctrl+Space`. You can also use an
alternate mapping while in Insert mode, similar to `:image jk <Esc>` in vim.
See the `imap_esc` and `imap_esc_timeout` options for more details.

Three bar items are provided:

* **mode_indicator**: shows the currently active mode (e.g. `NORMAL`). Has
  various customization options (see `/fset vimode.mode_indicator`).
* **vi_buffer**: shows partial commands (e.g. `df`).
* **cmd_completion**: shows completion suggestions for `:commands` (triggered
  with `<Tab>`).

It is highly recommended you add **mode_indicator** and **vi_buffer** to your
input bar. For example:

* `/fset weechat.bar.input.items`
* `<Alt+Enter>` or type `s` and press `Enter`
* Add `mode_indicator+` at the start, and `,[vi_buffer]` at the end.
* Final result example:
    `"mode_indicator+[input_prompt]+(away),[input_search],
    [input_paste],input_text,[vi_buffer]"`

You can also add **cmd_completion** to the status bar:

* `/fset weechat.bar.status.items`
* `<Alt+Enter>` or type `s` and press `Enter`
* Add `,cmd_completion` at the end.
* Final result example:
    `""[time],[buffer_last_number],[buffer_plugin],buffer_number+:+buffer_name+(buffer_modes)+{buffer_nicklist_count}+buffer_zoom+buffer_filter,scroll,[lag],[hotlist],completion,cmd_completion"`

To switch back to Insert mode, you can use `i`, `a`, `A`, etc.

To execute an Ex command, simply precede it with a ":" while in Normal mode,
for example: ":h" or ":s/foo/bar".


# Showing line numbers:
The `vi_line_numbers` bar (comes with a bar item) is provided but hidden by
default, and can be shown to display line numbers next to the chat window
(similar to vi's `:set number`). You can show it by using the command:
`/set weechat.bar.vi_line_numbers.hidden off`.

(Depending on your configuration, you may need to adjust some of its settings
for it to be displayed correctly, but the defaults should suit most users.)

It is useful for `:<num>` commands, which will start WeeChat's cursor mode and
take you to the appropriate line. You can then use the default key bindings to
quote the message (`Q`, `m` and `q`).

You can customize the prefix/suffix for each line: `/fset vimode.line_number`.


# Enabling vim-like search:
By default, pressing `/` will simply launch WeeChat's search mode.

Optionally, weechat-vimode can also handle `n`/`N` presses after pressing `/`
and confirming the query. To enable this setting:
`/set plugins.var.python.vimode.search_vim on`.
Note that having this setting enabled will require an extra `<Enter>` press to
exit search mode (where only `n`/`N` are recognized and handled) and return to
Normal mode. When in search mode, pressing `/` will start a new search.


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
* `r{char}`         Replace **[count]** characters with **{char}** under and
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
* `u`               Undo change **[count]** times.
* `^R`              Redo change **[count]** times.
* `nt`              Scroll nicklist up.
* `nT`              Scroll nicklist down.

## Buffers:
* `^B`              Scroll buffer page up. (use `weechat.look.scroll_page_percent` value)
* `^F`              Scroll buffer page down. (use `weechat.look.scroll_page_percent` value)
* `^U`              Scroll buffer up. (use `weechat.look.scroll_amount` value)
* `^D`              Scroll buffer down. (use `weechat.look.scroll_amount` value)
* `^Y` or `k`       Scroll buffer line up.
* `^E` or `j`       Scroll buffer line down.
* `gt` or `K` or `H`Go to the previous buffer.
* `gT` or `J` or `L`Go to the next buffer.
* `gg`              Goto first line.
* `G`               Goto line **[count]**, default last line.
* `/`               Launch WeeChat search mode
* `^^`              Jump to the last buffer.

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
                    Go to buffer `[N]`.
* `:sp`, `:split`   Split current window in two (`/window splith`).
* `:vs`, `:vsplit`  Split current window in two, but vertically
                    (`/window splitv`).
* `:!{cmd}`         Execute shell command (`/exec -buffer shell`)
* `:s/pattern/repl`  
  `:s/pattern/repl/g`
                    Search/Replace \*
* `:<num>`          Start cursor mode and go to line.
* `:nmap`           List user-defined key mappings.
* `:nmap {lhs} {rhs}`
                    Map `{lhs}` to `{rhs}` for Normal mode.  Some (but not all) vim-like key codes are
                    supported: `<Up>`, `<Down>`, `<Left>`, `<Right>`, `<C-...>` and `<M-...>`. These "user
                    mappings" share much of the flexibility you are accustomed to from using regular
                    vim mappings. See the [User Mappings](#usermaps) section for details and examples.
* `:nunmap {lhs}`   Remove the mapping of `{lhs}` for Normal mode.
* `:command`        All other commands will be passed to WeeChat (e.g.
                    ":script …" is equivalent to "/script …").

\* Supports regex (check docs for the Python re module for more
information). `&` in the replacement is also substituted by the pattern. If the
`g` flag isn't present, only the first match will be substituted.

# <a name="usermaps"></a>User Mappings
User mappings are created using `:nmap {lhs} {rhs}`. The `{rhs}` argument consists of any
combination of the following:

* A WeeChat command, specified with: `/command [options]<CR>`. You may also use a colon (`:`)
  in place of the forward slash (`/`) if you wish.
* An INSERT mode action, specified by an `A`, `I`, `i`, or `a` to enter INSERT mode; then an
  (optional) arbitrary string of characters to send to the command-line; and then (optionally) ending the
  pattern with a `<CR>` (to submit the text to the current buffer) or a `<Esc>` to end the INSERT
  mode action and go back to NORMAL mode.
* Keys specifying a vim motion (`h`,`j`,`k`,`l`,`^`,`0`, etc.).
* Keys specifying a vim operation (`dd`, `y$`, `cw`, etc.).

A count may be specified either in the mapping itself or before triggering the mapping.
Furthermore, you may place the following count tag anywhere (except inside an INSERT action) within
the binding (`{rhs}`): `#{N}`, where `N` is some arbitrary integer. This special "count tag" is used to
consume an external count. If no external count is provided, `N` will be used as the default
count. This will all probably be easier to grasp after seeing a few examples:

### Examples

1) Commands can be concatenated together:
     - INPUT: `:nmap h /cmd1<CR>/cmd2<CR>`
     - OUTPUT [h]: Runs `/cmd1` then `/cmd2`.

2) User defined bindings will be followed:
     - INPUT: `:nmap j /buffer 5<CR>h`
     - OUTPUT [j]: Go to the fifth buffer, then run `/cmd1`, and then run `/cmd2`.

3) Bindings can take advantage of INSERT mode:
     - INPUT: `:nmap k i/msg <Esc>0i`
     - OUTPUT [k]: Prints "/msg " to the command-line and then returns the user to the beginning of the line. The user is left in INSERT mode.

4) Counts are respected both internally and externally:
     - INPUT: `:nmap j 3J`
     - OUTPUT [j]: Go three buffers down.
     - OUTPUT [3j]: Go nine buffers down.

5) Special "count tag" gives you more flexibility when using external counts:
     - INPUT: `:nmap @ /buffer #{3}<CR>`
     - OUTPUT [7@]: Go to the seventh buffer.
     - OUTPUT [@]: Go to the third buffer.

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
* version 0.7:      added support for user-defined key mappings (`:nmap {lhs}
                    {rhs}`/`:nunmap {lhs}`), undo history, optional vim-like
                    search, command-line mode history, and various
                    customization options (mode indicator colors and
                    prefix/suffix; line numbers prefix/suffix).
                    Removed the separate command-line bar (the input bar is now
                    used instead).
                    Other bug fixes and improvements.

For the full change log, please check the [list of commits][1].


# Support:
Please report any issues using the [GitHub issue tracker][2]. Also feel free to
suggest new features that you need.

You can contact me on irc.freenode.net in #weechat or via a query (nickname:
GermainZ).

[1]: https://github.com/GermainZ/weechat-vimode/commits/master
[2]: https://github.com/GermainZ/weechat-vimode/issues/new
