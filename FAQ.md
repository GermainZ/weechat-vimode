# Problematic key bindings
`meta-<key>meta-…` key bindings may conflict with vimode. For example, these
default key bindings are all considered problematic:

* `meta-jmeta-l` -> `/input jump_last_buffer`
* `meta-jmeta-r` -> `/server raw`
* `meta-jmeta-s` -> `/server jump`
* `meta-wmeta-meta2-A` -> `/window up`
* `meta-wmeta-meta2-B` -> `/window down`
* `meta-wmeta-meta2-C` -> `/window right`
* `meta-wmeta-meta2-D` -> `/window left`
* `meta-wmeta-b` -> `/window balance`
* `meta-wmeta-s` -> `/window swap`

This only matters after you press Esc. For example:

* Press `Esc` to switch to Normal mode.
* Press `w` expecting to move the cursor to the next word.
* `Esc-w` is actually detected as `meta-w` by your terminal (and therefore
WeeChat). However, `meta-w` matches the beginning of known keybindings, such
as `meta-wmeta-meta2-A`. This means WeeChat won't report that `meta-w` was
pressed just yet, and will wait for another keystroke to see if that still
matches a known keybinding.
* The result is that vimode won't know you pressed `w`. Once you press another
key (e.g. `w`), it'll then receive a `ww` press and ignore that (since it's
bound to nothing). You'll have to press `w` a third time for vimode to detect
it.

You have a few choices to solve this:

* Live with it if you consider it's not important enough.
* Remove the problematic key bindings entirely.
* Rebind the problematic key bindings to something that won't conflict.

To remove the conflicting key bindings and add recommended key bindings,
you can run the `/vimode bind_keys` command inside WeeChat. To only list
changes, run `/vimode bind_keys --list` instead.

# Esc key not being detected instantly
This can happen if you're using a terminal multiplexer, such as tmux or screen.
You can decrease (or remove) the time your multiplexer waits to determine
input key sequences to fix this.

* tmux: set `escape-time` to 0 (e.g. `tmux set-option escape-time 0`, or add
`set -sg escape-time 0` to your `.tmux.conf` file).
* screen: set `maptimeout` to 0 (e.g. `C-a :` followed by `maptimeout 0`, or
add `maptimeout 0` to your `.screenrc`).

# Exiting insert mode upon sending a message

If you want to go to normal mode after sending a message, you can rebind the
`<Enter>` key in WeeChat:

    /key bind ctrl-M /vimode_go_to_normal;/input return

If you're using a script that rebinds `<Enter>` like multiline.pl, replace
`/input return` with the appropriate command. To check the current binding,
you can press `Alt-K` followed by `<Enter>` in WeeChat.

You'll need to manually rebind `<Enter>` if you remove weechat-vimode. For
example:

    /key bind ctrl-M /input return

You can always use `^J` instead of `<Enter>` if something goes wrong.

# Custom key mappings examples (in Normal mode)

To swap the behavior of `J` and `K`, you map one to the other:
```
:nmap J K
:nmap K J
```

If you'd like `j`/`k`/`^j`/`^k` to behave like `↑`/`↓`/`^↑`/`^↓`, execute the
following commands:
```
:nmap j <Up>
:nmap k <Down>
:nmap <C-j> <C-Up>
:nmap <C-k> <C-Down>
```

# Command-line bar behavior

The default behavior for the command-line bar is for it to be hidden when it
doesn't contain any text.

If you'd like to keep the command-line bar visible at all times, you can do so
as such: `/fset plugins.var.python.vimode.cmd_bar_behavior visible`.

You can also keep the command-line bar permanently hidden if you prefer: `/fset
plugins.var.python.vimode.cmd_bar_behavior hidden`. This can be useful if you
don't want any wasted space, but please take care to add the `cmd_text` bar
item to some visible bar, such as the `input` bar. To do so, modify
`weechat.bar.input.items` and add `cmd_text` to it somewhere.
